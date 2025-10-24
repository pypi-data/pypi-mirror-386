from ..test import ExperimentTest, Results
from . import dwifslpreproc_dtifit


class HasCorrectItems(dwifslpreproc_dtifit.HasCorrectItems):
    __doc__ = (dwifslpreproc_dtifit.HasCorrectItems.__doc__.
               replace('DWIFSLPREPROC_DTIFIT', 'ALPS').
               replace('dwifslpreproc_dtifit#outputs', 'alps#outputs'))

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'
    expected_items = ['alps.stat/alps.csv',
                      'alps.stat/fa+md_alps.csv',
                      'b0.nii.gz',
                      'b0_2_t1w.nii.gz',
                      'b0_brain_mask.nii.gz',
                      'b0_brain_mask_2_struct.nii.gz',
                      'dti2struct_init.mat',
                      'dti2struct.mat',
                      'dti2struct_fast_wmedge.nii.gz',
                      'dti2struct_fast_wmseg.nii.gz',
                      'dti_FA.nii.gz',
                      'dti_FA_2_t1w.nii.gz',
                      'dti_FA_to_MNI152_T1_1mm.nii.gz',
                      'dti_MD.nii.gz',
                      'dti_MD_2_t1w.nii.gz',
                      'dti_MD_to_MNI152_T1_1mm.nii.gz',
                      'dti_tensor.nii.gz',
                      'dti_tensor_in_MNI152_T1_1mm.nii.gz',
                      'dxx_in_MNI152_T1_1mm.nii.gz',
                      'dyy_in_MNI152_T1_1mm.nii.gz',
                      'dzz_in_MNI152_T1_1mm.nii.gz',
                      'struct2template_aff.mat',
                      'struct2template_warps.nii.gz',
                      't1w.nii.gz',
                      't1w_bet.nii.gz',
                      't1w_bet_mask.nii.gz',
                      't1w_brain.nii.gz',
                      't1w_to_MNI152_T1_1mm_brain.log',
                      'wm.nii.gz']


class HasCorrectMRtrix3Version(dwifslpreproc_dtifit.HasCorrectMRtrix3Version):
    __doc__ = (dwifslpreproc_dtifit.HasCorrectMRtrix3Version.__doc__.
               replace('DWIFSLPREPROC_DTIFIT', 'ALPS'))

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'
    expected_version = 'MRtrix3 Version: 3.0.4'
    init_line = 'MRtrix3 Version:'


class HasCorrectFSLVersion(dwifslpreproc_dtifit.HasCorrectFSLVersion):
    __doc__ = (dwifslpreproc_dtifit.HasCorrectFSLVersion.__doc__.
               replace('DWIFSLPREPROC_DTIFIT', 'ALPS'))

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'


class FAtoT1RegistrationSnapshot(ExperimentTest):
    """This test creates a snapshot of the Fractional Anisotropy (`FA`) map registered
    to the T1w native space, overlaid with the White Matter (`WM`) probability map.
    Passes if the snapshot is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        paths = []
        try:
            tmpdir = tempfile.gettempdir()
            fa = self.__download_map__('dti_FA_2_t1w.nii.gz', experiment_id,
                                       tmpdir, self.resource_name)
            wm = self.__download_map__('wm.nii.gz', experiment_id,
                                       tmpdir, self.resource_name)
            for each in 'xyz':
                fd, path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                paths.append(path)
                im = plotting.plot_anat(fa,
                                        black_bg=True,
                                        bg_img=None,
                                        display_mode=each,
                                        draw_cross=False,
                                        cut_coords=8)

                im.add_overlay(wm, threshold=0.5, alpha=0.4, cmap='red_transparent')
                im.savefig(path)

            for item in [fa, wm]:
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

    def __download_map__(self, filename, experiment_id, destination, resource='ALPS'):
        import os.path as op

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(resource)

        f = r.file(filename)
        fp = op.join(destination, f.attributes()['Name'])
        f.get(fp)
        return fp


class FAtoMNIRegistrationSnapshot(FAtoT1RegistrationSnapshot):
    """This test creates a snapshot of the Fractional Anisotropy (`FA`) map
    registered to the MNI standard space, overlaid on the MNI template.
    Passes if the snapshot is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting, datasets

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        paths = []
        try:
            tmpdir = tempfile.gettempdir()
            fa = self.__download_map__('dti_FA_to_MNI152_T1_1mm.nii.gz',
                                       experiment_id, tmpdir, self.resource_name)
            # Load the MNI template
            mni_template = datasets.load_mni152_template()
            # Load a standard MNI mask (e.g., the MNI brain mask)
            mni_mask = datasets.load_mni152_brain_mask()

            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            paths.append(path)
            im = plotting.plot_stat_map(fa,
                                        bg_img=mni_template,
                                        threshold=0.2,
                                        vmax=0.9,
                                        alpha=0.75,
                                        display_mode="mosaic",
                                        draw_cross=False,
                                        cut_coords=8,
                                        annotate=False,
                                        cmap="gnuplot")

            im.savefig(path)

            for item in [fa]:
                os.remove(item)

        except Exception:
            return Results(False, data=['Snapshot creation failed.'])

        return Results(True, paths)


class IsALPSIndexConsistent(ExperimentTest):
    """Checks if the calculated ALPS index, a measure of perivascular water
    diffusion and a proxy for glymphatic clearance, is consistently within an
    expected range of 1.0 to 2.0. The test passes if the index is within the 
    range; fails otherwise."""

    passing = 'BBRCDEV_E02949',
    failing = 'BBRCDEV_E02823',
    resource_name = 'ALPS'
    range = (1., 2.)

    def run(self, experiment_id):

        e = self.xnat_instance.select.experiment(experiment_id)
        alps_idx = e.resource(self.resource_name).alps().alps.iloc[0]
        result = bool(self.range[0] <= alps_idx <= self.range[1])

        return Results(result, data=[alps_idx])

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data[0], str):
                report = self.results.data
            elif isinstance(self.results.data[0], float):
                report.append(f'ALPS index ({self.results.data[0]}) '
                              f'is out of the expected range.')
        return report
