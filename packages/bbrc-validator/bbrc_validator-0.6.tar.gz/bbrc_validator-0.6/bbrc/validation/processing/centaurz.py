from ..test import ExperimentTest, Results
from . import ftm_quantification as ftm_quant


class HasCorrectItems(ExperimentTest):
    """Passes if a `CENTAURZ` resource is found and this resource has the expected
    items according to the pipeline [specifications](
    https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/centaurz#outputs)."""

    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E04629',
    resource_name = 'CENTAURZ'
    expected_items = ['rstatic_pet_coregT1.nii.gz',
                      'c1mri.nii.gz',
                      'c2mri.nii.gz',
                      'y_mri.nii.gz',
                      'iy_mri.nii.gz',
                      'rp_pet.txt',
                      'mri.nii.gz',
                      'static_pet.nii.gz',
                      'centaurz_quantification_results.csv',
                      'wMCALT_CenTauR.nii.gz',
                      'wMCALT_Frontal_CenTauR.nii.gz',
                      'wMCALT_Mesial_CenTauR.nii.gz',
                      'wMCALT_Meta_CenTauR.nii.gz',
                      'wMCALT_TP_CenTauR.nii.gz',
                      'wMCALT_voi_CerebGry_tau_2mm.nii.gz',
                      'stdout.log',
                      'stderr.log']

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)

        res = e.resource(self.resource_name)
        file_list = set([e.attributes()['Name'] for e in res.files()])
        missing = set(self.expected_items).difference(file_list)

        msg = []
        result = True
        if missing:
            result = False
            msg.append('Missing items: {}.'.format(list(missing)))

        return Results(result, data=msg)
    

class QuantificationResultsShape(ExperimentTest):
    """`CENTAURZ` resources contain quantification results stored as tabular data
    in a CSV-formatted file. This test reads the CSV file and verifies that it can
    be parsed as a valid CSV and matches the expected shape (45 rows x 5 columns).
    Test fails if the file cannot be parsed as CSV or the data dimensions do not
    match the expected size. Passes otherwise."""

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'
    csv_shape = (45, 5)

    def run(self, experiment_id):
        import io
        import pandas as pd
        import pandas.errors as pd_errors

        e = self.xnat_instance.select.experiment(experiment_id)
        res = e.resource(self.resource_name)

        csv_file = res.file('centaurz_quantification_results.csv')
        csv_content = (self.xnat_instance.get(csv_file._uri)).text
        try:
            df = pd.read_csv(io.StringIO(csv_content))
        except pd_errors.ParserError:
            return Results(False, data=['Invalid CSV file format.'])

        if df.shape != self.csv_shape:
            return Results(False,
                           data=['Invalid CSV file dimensions; expected: {}, '
                                 'current: {}'.format(self.csv_shape,
                                                      df.shape)])
        return Results(True, data=[])
    

class HasCorrectSPMVersion(ExperimentTest):
    """This test checks the version of SPM used. Passes if `CENTAURZ` outputs
    were generated using the expected version (i.e. `SPM12 Release 7771`)."""

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'
    expected_version = 'SPM version: SPM12 Release: 7771'

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        res = e.resource(self.resource_name)
        log = res.file('LOGS/stdout.log')
        if not log.exists():
            return Results(False, data=['stdout.log file not found.'])

        log_data = self.xnat_instance.get(log.attributes()['URI']).text
        version = [line for line in log_data.splitlines()
                       if line.startswith(self.expected_version.split(':')[0])]

        if not version:
            return Results(False, data=[f"{self.expected_version.split(':')[0]}"
                                        " registered in the logs."])
        elif list(set(version)) != [self.expected_version]:
            return Results(False, data=list(set(version)))

        return Results(True, [])


class HasCorrectMatlabVersion(HasCorrectSPMVersion):
    """This test checks the version of MATLAB used. Passes if `CENTAURZ` outputs
    were generated using the expected version (i.e. `9.7.0.1737446 (R2019b)`)."""

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'
    expected_version = 'MATLAB Version: 9.7.0.1737446 (R2019b) Update 9'


class IsMaxTranslationConsistent(ftm_quant.IsMaxTranslationConsistent):
    __doc__ = ftm_quant.IsMaxTranslationConsistent.__doc__

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'


class MotionParameterSnapshot(ftm_quant.MotionParameterSnapshot):
    __doc__ = ftm_quant.MotionParameterSnapshot.__doc__

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource = 'CENTAURZ'


class UniversalMaskSnapshot(ExperimentTest):
    """This test creates a snapshot of the Universal Centaur mask normalized to 
    native space (i.e. `wMCALT_CenTauR.nii.gz`) and overlays it on the subject's
    T1w MRI image. Test passes if the snapshot is created successfully. Fails
    otherwise"""

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'
    file = 'wMCALT_CenTauR.nii.gz'

    def run(self, experiment_id):
        import os
        import tempfile
        import logging as log
        from nilearn import image
        from . import pet_quantification_snapshot

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        r = self.xnat_instance.select.experiment(experiment_id).resource(self.resource_name)
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            log.error(msg)
            return Results(False, data=[msg])

        f = r.file('mri.nii.gz')
        if not f.exists():
            return Results(False,
                           data=['File `mri.nii.gz` not found.'])

        fd, t1_fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(t1_fp)
        t1 = image.load_img(t1_fp)

        f = r.file(self.file)
        if not f.exists():
            return Results(False, data=['File `{}` not found.'.format(self.file)])

        fd, mask_fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(mask_fp)
        mask = image.load_img(mask_fp)

        res = pet_quantification_snapshot(mask, t1)

        for item in [mask_fp, t1_fp]:
            os.remove(item)
        return Results(True, res)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report


class CerebellarGrayMatterSnapshot(UniversalMaskSnapshot):
    """This test creates a snapshot of the Cerebellar Gray Matter mask 
    normalized to native space (i.e. `wMCALT_voi_CerebGry_tau_2mm.nii.gz`) and
    overlays it on the subject's T1w MRI image. The mask serves as the reference
    region in the quantification analysis. Test passes if the snapshot is created
    successfully. Fails otherwise"""

    passing = "BBRCDEV_E02957",
    failing = "BBRCDEV_E04629",
    resource_name = 'CENTAURZ'
    file = 'wMCALT_voi_CerebGry_tau_2mm.nii.gz'

    def run(self, experiment_id):
        import os
        import tempfile
        import logging as log
        from nilearn import image
        from nilearn import plotting

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        r = self.xnat_instance.select.experiment(experiment_id).resource(self.resource_name)
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            log.error(msg)
            return Results(False, data=[msg])

        f = r.file('mri.nii.gz')
        if not f.exists():
            return Results(False,
                           data=['File `mri.nii.gz` not found.'])

        fd, t1_fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(t1_fp)
        t1 = image.load_img(t1_fp)

        f = r.file(self.file)
        if not f.exists():
            return Results(False, data=['File `{}` not found.'.format(self.file)])

        fd, mask_fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(mask_fp)
        mask = image.load_img(mask_fp)

        paths = []
        for each in 'xy':
            _, path = tempfile.mkstemp(suffix='.jpg')
            paths.append(path)
            im = plotting.plot_roi(mask,
                                   black_bg=True,
                                   bg_img=t1,
                                   display_mode=each,
                                   draw_cross=False,
                                   cmap='red_transparent')
            im.savefig(path)

        for item in [mask_fp, t1_fp]:
            os.remove(item)
        return Results(True, paths)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report
