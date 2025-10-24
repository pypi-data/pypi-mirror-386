from ..test import ExperimentTest, Results
from . import basil


class HasCorrectItems(ExperimentTest):
    """Passes if a `3DASL_QUANTIFICATION` resource is found and this resource
    has the expected items according to the pipeline
    [specifications](https://gitlab.com/bbrc/xnat/xnat-pipelines/-/tree/master/asl#outputs-1)."""

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',

    def run(self, experiment_id):
        resource_name = '3DASL_QUANTIFICATION'
        unique_items = ['masked_asl.nii.gz',
                        'mask.nii.gz',
                        'asl2std.nii.gz',
                        'asl2struct.mat',
                        'asl2struct_init.mat',
                        'asl2struct.nii.gz',
                        'std2asl.mat',
                        'std2struct.mat',
                        'struct2asl.mat',
                        'T1_fast_pve_2_bin.nii.gz',
                        'tissedge.nii.gz',
                        'tissseg.nii.gz',
                        'gm2asl.nii.gz',
                        'wm2asl.nii.gz',
                        'quantification_results.csv']

        e = self.xnat_instance.select.experiment(experiment_id)
        res = e.resource(resource_name)

        missing = []
        for item in unique_items:
            files = res.files(item).get()
            if not files:
                missing.append(item)

        result = not bool(missing)
        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectFSLVersion(basil.HasCorrectFSLVersion):
    __doc__ = basil.HasCorrectFSLVersion.__doc__
    __doc__ = __doc__.replace('BASIL', '3DASL_QUANTIFICATION')

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'


class HasCorrectASLRegVersion(ExperimentTest):
    """Checks the version of `asl_reg` tool used for registration of ASL data.
    Passes if `3DASL_QUANTIFICATION` outputs were created using the expected
    version (`4.0.15`)."""

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'
    expected_version = 'v4.0.15-dirty Fri Jul 17 12:23:03 2020'

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        log_filename = 'LOGS/{}.log'.format(e.label())
        log_file = e.resource(self.resource_name).file(log_filename)

        if not log_file.exists():
            msg = '{} log file not found.'.format(self.resource_name)
            return Results(False, data=[msg])

        log_data = self.xnat_instance.get(log_file.attributes()['URI']).text
        version_line = [line for line in log_data.splitlines()
                        if line.strip().startswith('asl_reg')]
        if not version_line:
            msg = 'No asl_reg version registered in the logs.'
            return Results(False, data=[msg])

        version = version_line[0].split('asl_reg ')[-1]
        if not version.startswith(self.expected_version):
            return Results(False, data=[version])

        return Results(True, data=[])


class IsT1Session1(basil.IsT1Session1):
    __doc__ = basil.IsT1Session1.__doc__
    __doc__ = __doc__.replace('BASIL', '3DASL_QUANTIFICATION')

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'


class IsT1Session3(basil.IsT1Session3):
    __doc__ = basil.IsT1Session3.__doc__
    __doc__ = __doc__.replace('BASIL', '3DASL_QUANTIFICATION')

    passing = 'BBRCDEV_E03480',
    failing = 'BBRCDEV_E03479',
    resource_name = '3DASL_QUANTIFICATION'


class IsGMPerfusionMeanConsistent(ExperimentTest):
    """Checks the quantified perfusion mean value for GM. Test passes if average
    CBF is within the expected range, i.e. between 30-100 ml/(100g min). Test
    fails otherwise."""

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'
    tissue = "GM"
    range = (30, 100)

    def run(self, experiment_id):

        e = self.xnat_instance.select.experiment(experiment_id)
        df = e.resource(self.resource_name).perfusion()
        perf = df.query(f'region == "{self.tissue}"')['mean'].item()
        result = bool(self.range[0] <= perf <= self.range[1])

        return Results(result, data=[perf])

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data[0], str):
                report = self.results.data
            elif isinstance(self.results.data[0], float):
                report.append('Mean perfusion value ({}) is out of the '
                              'expected range.'.format(self.results.data[0]))
        return report


class IsWMPerfusionMeanConsistent(IsGMPerfusionMeanConsistent):
    __doc__ = IsGMPerfusionMeanConsistent.__doc__.replace('GM', 'WM')
    __doc__ = __doc__.replace('between 30-100', 'between 10-60')

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'
    tissue = "WM"
    range = (10, 60)


class PerfusionSnapshot(ExperimentTest):
    """This test creates a snapshot of the calibrated brain perfusion generated
    by `3DASL_QUANTIFICATION`. Passes if the snapshot is created successfully.
    Test fails otherwise."""

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E00381',
    resource_name = '3DASL_QUANTIFICATION'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting

        slices = {'x': [-46, -30, -16, -4, 12, 26, 38],
                  'y': [-80, -60, -40, -20, 10, 20, 40],
                  'z': [-20, -10, 0, 10, 20, 30, 45]}

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        paths = []
        try:
            bg, filepaths = self.__download_perf__(experiment_id,
                                                   tempfile.gettempdir(),
                                                   self.resource_name)
            for each in 'xyz':
                fd, path = tempfile.mkstemp(suffix='.jpg')
                os.close(fd)
                paths.append(path)
                im = plotting.plot_anat(bg,
                                        black_bg=True,
                                        display_mode=each,
                                        cut_coords=slices[each])
                im.add_overlay(filepaths[0],
                               threshold=5,
                               colorbar=True,
                               cmap='hsv',
                               vmin=10,
                               vmax=60)
                im.savefig(path)

            for item in [bg] + filepaths:
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

    def __download_perf__(self, experiment_id, destination, resource):
        import os.path as op

        files = ['fsl.anat/T1_to_MNI_lin.nii.gz',
                 'asl2std.nii.gz']

        filepaths = []

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(resource)
        for each in files:
            f = r.file(each)
            fp = op.join(destination, f.attributes()['Name'])
            f.get(fp)
            filepaths.append(fp)

        bg = filepaths.pop(0)
        return bg, filepaths


class FSLANATSegmentationSnapshot(basil.FSLANATSegmentationSnapshot):
    __doc__ = basil.FSLANATSegmentationSnapshot.__doc__
    __doc__ = __doc__.replace('BASIL', '3DASL_QUANTIFICATION')

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E00381',
    resource_name = '3DASL_QUANTIFICATION'


class HasNormalFSLANATVolumes(basil.HasNormalFSLANATVolumes):
    __doc__ = basil.HasNormalFSLANATVolumes.__doc__
    __doc__ = __doc__.replace('BASIL', '3DASL_QUANTIFICATION')

    passing = 'BBRCDEV_E03479',
    failing = 'BBRCDEV_E03480',
    resource_name = '3DASL_QUANTIFICATION'
