from ..test import ExperimentTest, Results
from . import dwifslpreproc_dtifit as dfp_dtifit


class HasCorrectItems(ExperimentTest):
    """Passes if a `PYMENT` resource is found and this resource has the expected
    items according to the pipeline [specifications
    ](ttps://gitlab.com/bbrc/xnat/docker-images/-/tree/master/pyment#outputs)."""

    passing = 'BBRCDEV_E02823',
    failing = 'BBRCDEV_E03095',
    resource_name = 'PYMENT'
    expected_items = ['cropped.nii.gz',
                      'grad_cam.png',
                      'stdout.log',
                      'stderr.log']

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)

        self.expected_items.append(f'{experiment_id}_prediction.csv')
        res = e.resource(self.resource_name)
        file_list = set([e.attributes()['Name'] for e in res.files()])
        missing = set(self.expected_items).difference(file_list)

        msg = []
        result = True
        if missing:
            result = False
            msg.append('Missing items: {}.'.format(list(missing)))

        return Results(result, data=msg)
    

class HasCorrectFSLVersion(dfp_dtifit.HasCorrectFSLVersion):
    __doc__ = (dfp_dtifit.HasCorrectFSLVersion.__doc__.
               replace('DWIFSLPREPROC_DTIFIT', 'PYMENT'))

    passing = 'BBRCDEV_E02823',
    failing = 'BBRCDEV_E03095',
    resource_name = 'PYMENT'


class PYMENTSnapshot(ExperimentTest):
    """This test creates a snapshot of the preprocessed image (i.e. `cropped.nii.gz`) 
    that serves as input to the `pyment` model. The MNI152 template is used as
    background and the cropped image is overlaid in red to visualize alignment and
    preprocessing quality. Test passes if the snapshot is created successfully,
    fails otherwise."""

    passing = 'BBRCDEV_E02823',
    failing = 'BBRCDEV_E03095',
    resource_name = 'PYMENT'

    def run(self, experiment_id):
        import os
        import tempfile
        import logging as log
        from nilearn import image
        from nilearn import plotting

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            log.error(msg)
            return Results(False, data=[msg])

        f = r.file('cropped.nii.gz')
        if not f.exists():
            return Results(False,
                           data=['File `cropped.nii.gz` not found.'])

        fd, fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(fp)
        img = image.load_img(fp)
        os.remove(fp)

        paths = []
        for each in 'xyz':
            _, path = tempfile.mkstemp(suffix='.jpg')
            paths.append(path)
            im = plotting.plot_stat_map(img,
                                    black_bg=True,
                                    display_mode=each,
                                    draw_cross=False,
                                    alpha=0.6,
                                    cmap='red_transparent',
                                    colorbar=False)
            im.savefig(path)

        return Results(True, paths)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append(f'![snapshot]({path})')
        else:
            report = self.results.data
        return report
    

class GRADCAMSnapshot(ExperimentTest):
    """Grad-CAM (Gradient-weighted Class Activation Mapping) is a gradient-based 
    explainability technique that generates heatmaps to highlight which image
    regions contribute most to a model's predictions. In this visualization, layer
    activations greater than 0.6 are considered relevant; with the colormap
    ranging from blue (at 0.6) to red (at 1.0). Test passes if the snapshot is
    created successfully, fails otherwise."""

    passing = 'BBRCDEV_E02823',
    failing = 'BBRCDEV_E03095',
    resource_name = 'PYMENT'

    def run(self, experiment_id):
        import os
        import tempfile
        import logging as log

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            log.error(msg)
            return Results(False, data=[msg])

        f = r.file('grad_cam.png')
        if not f.exists():
            return Results(False,
                           data=['File `grad_cam.png` not found.'])

        fd, fp = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        f.get(fp)

        return Results(True, fp)

    def report(self):
        report = []
        if self.results.has_passed:
            report.append('![snapshot]({})'.format(self.results.data))
        else:
            report = self.results.data

        return report
