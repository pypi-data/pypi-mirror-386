from ..test import ExperimentTest, Results
from . import Snapshot


class HasCorrectItems(ExperimentTest):
    """Passes if a `MRTRIX3` resource is found and this resource has the
    expected items according to the pipeline [specifications](
    https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/mrtrix3#outputs)."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E02823',
    resource_name = 'MRTRIX3'
    expected_items = ['dwi_bc.mif',
                      'dwi_bc_mask.mif',
                      'mean_b0.mif',
                      'mean_b0.nii.gz',
                      '5tt.mif',
                      '5tt.nii.gz',
                      '5tt_coreg.mif',
                      '5tt_coreg.nii.gz',
                      'qc_5tt_vis.nii.gz',
                      'dwi2struct.mat',
                      'dwi2struct.txt',
                      'csf.txt',
                      'csf_fod.mif',
                      'csf_fod_norm.mif',
                      'wm.txt',
                      'wm_fod.mif',
                      'wm_fod_norm.mif',
                      'qc_rf_voxels.mif',
                      'gmwm_seed_coreg.mif',
                      'parc.mif',
                      'parc_coreg.mif',
                      'parc_coreg.nii.gz',
                      'tracks_5M.tck',
                      'sift2_weights.txt',
                      'assignments.csv',
                      'connectome.csv']

    def run(self, experiment_id):
        result = True

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        files = r.files().get()

        missing = [item for item in self.expected_items if item not in files]
        if missing:
            result = False

        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectMRtrixVersion(ExperimentTest):
    """This test checks the version of `MRtrix` used. Passes if outputs
    were created using the expected version (`{version}`)."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E02823',
    resource_name = 'MRTRIX3'
    expected_version = '3.0.4'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = r.file('LOGS/stdout.log')
        if not f.exists():
            msg = ['File `stdout.log` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        info = [ln for ln in file_content.splitlines() if 'mrtrix_version' in ln]
        if not info:
            msg = ['No `MRtrix` version information found.']
            return Results(False, data=msg)

        version = info[0].split()[1]
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(version)]

        return Results(result, data=data)


class FiveTTSegmentationSnapshot(ExperimentTest):
    """This test creates a snapshot of the 5TT (5 tissue types: cortical GM,
    sub-cortical GM, WM, CSF, pathological tissue) segmented T1w image generated
    by `MRTRIX3` and based on the Hybrid Surface & Volume Segmentation (HSVS)
    algorithm. The segmentation uses existing `FREESURFER7` results as input and
    is required for generating an anatomically-constrained tractography. Passes
    if the snapshot is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E02823',
    resource_name = 'MRTRIX3'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting

        slices = {'x': [-46, -30, -16, -4, 12, 26, 38],
                  'y': [-60, -40, -20, 10, 20, 40, 60],
                  'z': [0, 10, 20, 30, 40, 50, 60]}

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        paths = []
        try:
            fp = self.__download_5tt_vis__(experiment_id,
                                           tempfile.gettempdir(),
                                           self.resource_name)
            for each in 'xyz':
                fd, path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                paths.append(path)
                im = plotting.plot_anat(fp,
                                        black_bg=True,
                                        display_mode=each,
                                        cmap='jet',
                                        colorbar=False,
                                        threshold=0.1,
                                        vmin=0.15,
                                        vmax=1.15,
                                        cut_coords=slices[each])
                im.savefig(path)

            os.remove(fp)

        except Exception:
            return Results(False, data=['Snapshot creation failed.'])

        return Results(True, paths)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report

    def __download_5tt_vis__(self, experiment_id, destination, resource='MRTRIX3'):
        import os.path as op

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(resource)
        f = r.file('qc_5tt_vis.nii.gz')
        fp = op.join(destination, f.attributes()['Name'])
        f.get(fp)

        return fp


class T1toDWICoregistrationSnapshot(ExperimentTest):
    """This test creates a snapshot of the cortical GM segmentation coregistered
    to the DWI space, overlaid to the DWI b=0 average image. Passes if the snapshot
    is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E02823',
    resource_name = 'MRTRIX3'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting, image

        slices = {'x': [-46, -30, -16, -4, 12, 26, 38],
                  'y': [-60, -40, -20, 10, 20, 40, 60],
                  'z': [25, 40, 50, 60, 70, 80, 90]}

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        paths = []
        try:
            bg, parc = self.__download_5tt_coreg__(experiment_id,
                                                   tempfile.gettempdir(),
                                                   self.resource_name)
            for each in 'xyz':
                fd, path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                paths.append(path)
                im = plotting.plot_anat(bg,
                                        black_bg=True,
                                        display_mode=each,
                                        cut_coords=slices[each])

                im.add_overlay(image.index_img(parc, 0),
                               threshold=0.5,
                               cmap='hot',
                               vmin=0.5,
                               vmax=2)
                im.savefig(path)

            for item in [bg, parc]:
                os.remove(item)

        except Exception:
            return Results(False, data=['Snapshot creation failed.'])

        return Results(True, paths)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report

    def __download_5tt_coreg__(self, experiment_id, destination, resource='MRTRIX3'):
        import os.path as op

        files = ['mean_b0.nii.gz',
                 '5tt_coreg.nii.gz']

        filepaths = []
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(resource)
        for each in files:
            f = r.file(each)
            fp = op.join(destination, f.attributes()['Name'])
            f.get(fp)
            filepaths.append(fp)

        return filepaths


class IsRegionalStructuralConnectivityConsistent(ExperimentTest):
    """This test passes if the quantified structural connectivity for a subset of
    well-connected region pairs (i.e. {}) is greater than zero. Fails otherwise."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E03095',
    resource_name = 'MRTRIX3'

    fs_default_labels = ['ctx-lh-bankssts',
                         'ctx-lh-caudalanteriorcingulate',
                         'ctx-lh-caudalmiddlefrontal',
                         'ctx-lh-cuneus',
                         'ctx-lh-entorhinal',
                         'ctx-lh-fusiform',
                         'ctx-lh-inferiorparietal',
                         'ctx-lh-inferiortemporal',
                         'ctx-lh-isthmuscingulate',
                         'ctx-lh-lateraloccipital',
                         'ctx-lh-lateralorbitofrontal',
                         'ctx-lh-lingual',
                         'ctx-lh-medialorbitofrontal',
                         'ctx-lh-middletemporal',
                         'ctx-lh-parahippocampal',
                         'ctx-lh-paracentral',
                         'ctx-lh-parsopercularis',
                         'ctx-lh-parsorbitalis',
                         'ctx-lh-parstriangularis',
                         'ctx-lh-pericalcarine',
                         'ctx-lh-postcentral',
                         'ctx-lh-posteriorcingulate',
                         'ctx-lh-precentral',
                         'ctx-lh-precuneus',
                         'ctx-lh-rostralanteriorcingulate',
                         'ctx-lh-rostralmiddlefrontal',
                         'ctx-lh-superiorfrontal',
                         'ctx-lh-superiorparietal',
                         'ctx-lh-superiortemporal',
                         'ctx-lh-supramarginal',
                         'ctx-lh-frontalpole',
                         'ctx-lh-temporalpole',
                         'ctx-lh-transversetemporal',
                         'ctx-lh-insula',
                         'Left-Cerebellum-Cortex',
                         'Left-Thalamus',
                         'Left-Caudate',
                         'Left-Putamen',
                         'Left-Pallidum',
                         'Left-Hippocampus',
                         'Left-Amygdala',
                         'Left-Accumbens-area',
                         'Right-Thalamus',
                         'Right-Caudate',
                         'Right-Putamen',
                         'Right-Pallidum',
                         'Right-Hippocampus',
                         'Right-Amygdala',
                         'Right-Accumbens-area',
                         'ctx-rh-bankssts',
                         'ctx-rh-caudalanteriorcingulate',
                         'ctx-rh-caudalmiddlefrontal',
                         'ctx-rh-cuneus',
                         'ctx-rh-entorhinal',
                         'ctx-rh-fusiform',
                         'ctx-rh-inferiorparietal',
                         'ctx-rh-inferiortemporal',
                         'ctx-rh-isthmuscingulate',
                         'ctx-rh-lateraloccipital',
                         'ctx-rh-lateralorbitofrontal',
                         'ctx-rh-lingual',
                         'ctx-rh-medialorbitofrontal',
                         'ctx-rh-middletemporal',
                         'ctx-rh-parahippocampal',
                         'ctx-rh-paracentral',
                         'ctx-rh-parsopercularis',
                         'ctx-rh-parsorbitalis',
                         'ctx-rh-parstriangularis',
                         'ctx-rh-pericalcarine',
                         'ctx-rh-postcentral',
                         'ctx-rh-posteriorcingulate',
                         'ctx-rh-precentral',
                         'ctx-rh-precuneus',
                         'ctx-rh-rostralanteriorcingulate',
                         'ctx-rh-rostralmiddlefrontal',
                         'ctx-rh-superiorfrontal',
                         'ctx-rh-superiorparietal',
                         'ctx-rh-superiortemporal',
                         'ctx-rh-supramarginal',
                         'ctx-rh-frontalpole',
                         'ctx-rh-temporalpole',
                         'ctx-rh-transversetemporal',
                         'ctx-rh-insula',
                         'Right-Cerebellum-Cortex']
    connected_regions = {'ctx-lh-caudalanteriorcingulate': 'ctx-lh-rostralanteriorcingulate',
                         'ctx-lh-cuneus': 'ctx-lh-pericalcarine',
                         'ctx-lh-isthmuscingulate': 'ctx-lh-precuneus',
                         'ctx-lh-lateraloccipital': 'ctx-lh-pericalcarine',
                         'ctx-lh-lingual': 'ctx-lh-pericalcarine',
                         'ctx-lh-medialorbitofrontal': 'ctx-lh-rostralanteriorcingulate',
                         'ctx-lh-parsorbitalis': 'ctx-lh-parstriangularis',
                         'ctx-lh-superiorfrontal': 'ctx-lh-rostralmiddlefrontal',
                         'ctx-lh-superiorparietal': 'ctx-lh-precuneus',
                         'ctx-lh-frontalpole': 'ctx-lh-medialorbitofrontal',
                         'ctx-lh-transversetemporal': 'ctx-lh-superiortemporal',
                         'Left-Cerebellum-Cortex': 'Right-Cerebellum-Cortex',
                         'Left-Thalamus': 'Left-Caudate',
                         'Left-Hippocampus': 'ctx-lh-parahippocampal',
                         'Left-Amygdala': 'ctx-lh-entorhinal',
                         'Left-Accumbens-area': 'ctx-lh-medialorbitofrontal',
                         'Right-Thalamus': 'Right-Caudate',
                         'Right-Hippocampus': 'ctx-rh-parahippocampal',
                         'Right-Amygdala': 'ctx-rh-entorhinal',
                         'Right-Accumbens-area': 'ctx-rh-medialorbitofrontal',
                         'ctx-rh-caudalanteriorcingulate': 'ctx-rh-rostralanteriorcingulate',
                         'ctx-rh-cuneus': 'ctx-rh-pericalcarine',
                         'ctx-rh-isthmuscingulate': 'ctx-rh-precuneus',
                         'ctx-rh-lateraloccipital': 'ctx-rh-pericalcarine',
                         'ctx-rh-lingual': 'ctx-rh-pericalcarine',
                         'ctx-rh-superiorfrontal': 'ctx-rh-rostralmiddlefrontal',
                         'ctx-rh-superiorparietal': 'ctx-rh-precuneus',
                         'ctx-rh-supramarginal': 'ctx-rh-postcentral',
                         'ctx-rh-frontalpole': 'ctx-rh-medialorbitofrontal',
                         'ctx-rh-transversetemporal': 'ctx-rh-superiortemporal'}
    __doc__ = __doc__.format('; '.join(f'`{r1}`-`{r2}`'
                                       for r1, r2 in connected_regions.items()))

    def run(self, experiment_id):
        import numpy as np
        import pandas as pd

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = r.file('connectome.csv')
        if not f.exists():
            msg = ['File `connectome.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        parsed_content = [row.split(',') for row in content.splitlines()]
        connectome = pd.DataFrame(parsed_content,
                                  columns=self.fs_default_labels,
                                  index=self.fs_default_labels).astype(np.float64)

        failed_region_pairs = []
        for r1, r2 in self.connected_regions.items():
            conn_value = connectome[r1][r2]
            if np.isclose(conn_value, 0.0):
                failed_region_pairs.append([r1, r2])

        result = not bool(failed_region_pairs)

        return Results(result, failed_region_pairs)

    def report(self):

        if self.results.has_passed:
            report = []
        elif isinstance(self.results.data[0], str):
            report = self.results.data
        else:
            data = '<br> '.join(f'`{r1}`-`{r2}`' for r1, r2 in self.results.data)
            report = [f'Regions with no registered structural connectivity: <br>{data}']

        return report


class StructuralConnectivityMatrixSnapshot(ExperimentTest):
    """This test creates a snapshot of the quantified structural connectivity
    between parcellation pairs in the Desikan-Killiany atlas (`connectome.csv`
    file). Passes if the snapshot is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E02885',
    failing = 'BBRCDEV_E02823',
    resource_name = 'MRTRIX3'

    def run(self, experiment_id):
        import os
        import numpy as np
        import pandas as pd

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = r.file('connectome.csv')
        if not f.exists():
            msg = ['File `connectome.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        parsed_content = [row.split(',') for row in content.splitlines()]
        connectome = pd.DataFrame(parsed_content).astype(np.float64)

        path = self.__heatmap__(data=connectome.to_numpy(),
                                label=f"{experiment_id} structural connectivity matrix",
                                cmap='viridis', vmin=0, vmax=0.5)

        return Results(True, [path])

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report

    def __heatmap__(self, data, label=None, cbarlabel=None, **kwargs):
        """
        Create a heatmap from a numpy array.

        Parameters
        ----------
        data
            A 2D numpy array of shape (M, N).
        label
            The label for the plot figure. Optional.
        cbarlabel
            The label for the colorbar. Optional.
        **kwargs
            All other arguments are forwarded to `imshow`.
        """

        import os
        import tempfile
        import matplotlib.pyplot as plt

        f, ax = plt.subplots(1, 1, figsize=(10, 8))

        # Plot the heatmap
        im = ax.imshow(data, **kwargs)

        # Create colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        if cbarlabel:
            cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

        # Turn spines off and create white grid.
        ax.spines[:].set_visible(False)

        # add title label to the plot
        if label:
            plt.title(label)

        plt.axis(False)

        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        plt.tight_layout()
        plt.savefig(path)

        return path

