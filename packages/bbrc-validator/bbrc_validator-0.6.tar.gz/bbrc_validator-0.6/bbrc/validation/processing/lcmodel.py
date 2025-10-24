import logging

from ..test import ExperimentTest, Results
from . import spm
import operator
from . import Snapshot

class HasCorrectItems(ExperimentTest):
    """Passes if a `LCMODEL` resource is found and this resource has the
    expected items according to the LCModel pipeline [specifications](
    https://gitlab.com/bbrc/xnat/xnat-pipelines/-/tree/master/lcmodel#outputs)."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    expected_items = ['lcmodel/lcmodel.xlsx',
                      'lcmodel/met/error',
                      'lcmodel/met/RAW',
                      'lcmodel/met/cpStart',
                      'lcmodel/met/dump',
                      'lcmodel/met/extraInfo',
                      'lcmodel/h2o/RAW',
                      'tissue_correction/rAT1_ALFA2_{e}.nii.gz',
                      'tissue_correction/mrs_tissue_corr.xlsx',
                      'LOGS/pyscript_spm_coreg.m',
                      'LOGS/pyscript_spm_matrix.m']

    def run(self, experiment_id):
        result = True

        rois = [r.split('MRS')[1] for r in self.lut.keys() if r.startswith('MRS')]
        for r in rois:
            roi_list = [f'lcmodel/SV_PRESS_100_Myo_CHESS_{r}_{experiment_id}.ps',
                        f'lcmodel/SV_PRESS_100_Myo_CHESS_{r}_{experiment_id}.pdf',
                        f'lcmodel/SV_PRESS_100_Myo_CHESS_{r}_{experiment_id}.txt',
                        f'lcmodel/SV_PRESS_100_Myo_CHESS_{r}_{experiment_id}.csv',
                        f'lcmodel/SV_PRESS_100_Myo_CHESS_{r}_{experiment_id}_sl.CONTROL',
                        f'tissue_correction/mask_{r}_{experiment_id}.nii.gz',
                        f'tissue_correction/rAmask_{r}_{experiment_id}.nii.gz']
            self.expected_items += roi_list
        
        # use-case PENSA
        if self.lut['T1'] == ['T1_ALFA1']:
            items_to_remove = ['tissue_correction/rAT1_ALFA2_{e}.nii.gz',
                               'LOGS/pyscript_spm_coreg.m',
                               f'tissue_correction/rAmask_Cun_{experiment_id}.nii.gz']
            self.expected_items = [item for item in self.expected_items 
                                   if not item in items_to_remove]

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        missing = [item.format(e=experiment_id) for item in self.expected_items
                   if not r.files(item.format(e=experiment_id)).get()]
        if missing:
            result = False

        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectLCModelVersion(spm.HasCorrectSPMVersion):
    """This test checks the version of `LCModel` used. Passes if outputs were
    created using the expected version (i.e. `LCModel (Version 6.3-1R)`)."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    expected_version = 'LCModel (Version 6.3-1R)'

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        txt_fp = f'lcmodel/SV_PRESS_100_Myo_CHESS_Cun_{experiment_id}.txt'
        f = r.file(txt_fp)
        if not f.exists():
            msg = [f'File `{txt_fp}` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f.attributes()['URI']).text
        version_info = [line.strip() for line in file_content.splitlines()
                        if line.startswith(' LCModel')]
        if not version_info:
            msg = ['No `LCModel` version information found.']
            return Results(False, data=msg)

        version = version_info.pop()
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = [f'Incorrect version: `{version}`']

        return Results(result, data=data)


class HasCorrectSPMVersion(spm.HasCorrectSPMVersion):
    __doc__ = spm.HasCorrectSPMVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'LCMODEL')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    expected_version = 'SPM version: SPM12 Release: 7219'


class HasCorrectMatlabVersion(spm.HasCorrectMatlabVersion):
    __doc__ = spm.HasCorrectMatlabVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'LCMODEL')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    expected_version = 'MATLAB Version 7.10.0.499 (R2010a)'


class HasCorrectOSVersion(spm.HasCorrectOSVersion):
    __doc__ = spm.HasCorrectOSVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'LCMODEL')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'


class HasCorrectSNR(ExperimentTest):
    """The accuracy and precision of automated spectral quantitation and
    metabolite identification are strongly dependent on the signal-to-noise
    ratio (SNR). This test checks the SNR value estimated by `LCModel`. A low
    SNR coefficient may indicate the presence of artifacts. This test passes if
    SNR > 10 (Angular gyrus and Cuneus regions) and SNR > 5 (Hippocampus).
    Fails otherwise."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    operation = '<'
    measurement = 'SNR'
    threshold1 = 10
    threshold2 = 5

    def run(self, experiment_id):
        import tempfile
        import pandas as pd
        import os

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = r.file('lcmodel/lcmodel.xlsx')
        if not f.exists():
            msg = ['File `lcmodel/lcmodel.xlsx` not found.']
            return Results(False, data=msg)

        fd, fp = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)

        f.get(fp)
        df = pd.read_excel(fp)
        q1 = f'measurement == "{self.measurement}" and region != "hippocampus" ' \
             f'and value {self.operation} {self.threshold1}'
        q2 = f'measurement == "{self.measurement}" and region == "hippocampus" ' \
             f'and value {self.operation} {self.threshold2}'
        data = df.query(q1)[['region', 'value']].to_dict('records') + \
               df.query(q2)[['region', 'value']].to_dict('records')
        os.remove(fp)

        result = not bool(data)
        return Results(result, data=data)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data[0], dict):
                    report.append(f'Regions with inconsistent *{self.measurement}*:<br>')
                    msg = ', '.join(f"`{entry['region']}`: {entry['value']}"
                                    for entry in self.results.data)
                    report.append(msg)
            else:
                report = self.results.data

        return report


class HasCorrectFWHM(HasCorrectSNR):
    """The full width at half-maximum (FWHM) estimates the linewidth in the in
    vivo spectrum, an objective measure of MRS data quality. This test checks the
    FWHM value estimated by `LCModel` in parts per million (ppm). A high FWHM
    value may indicate the presence of artifacts. This test passes if FWHM <
    0.0625 (Angular gyrus and Cuneus regions) and FWHM < 0.1 (Hippocampus).
    Fails otherwise."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'
    operation = '>'
    measurement = 'FWHM'
    threshold1 = 0.0625
    threshold2 = 0.1


class HasCorrectMetaboliteConcentrationSD(ExperimentTest):
    """This test checks the standard deviation (SD) of the metabolite
    concentration estimated by `LCModel` for the following subset of metabolites:
    `Ins` (Myo-inositol), `NAA+NAAG` (N-acetyl aspartate), `Cr+PCr` (Creatine +
    Phosphocreatine) and `GPC+PCh` (Choline). This test passes if each of these
    metabolites have an estimated concentration SD < 20%. Fails otherwise."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'

    def run(self, experiment_id):
        import tempfile
        import pandas as pd
        import os

        threshold = 20.0
        metabolites = ['Ins', 'NAA+NAAG', 'GPC+PCh', 'Cr+PCr']

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = r.file('lcmodel/lcmodel.xlsx')
        if not f.exists():
            msg = ['File `lcmodel/lcmodel.xlsx` not found.']
            return Results(False, data=msg)

        fd, fp = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)

        f.get(fp)
        df = pd.read_excel(fp)
        q = f'table == "concentration_SD" ' \
            f'and measurement in @metabolites ' \
            f'and value >= {threshold}'
        data = df.query(q)[['region', 'measurement', 'value']].to_dict('records')
        os.remove(fp)

        result = not bool(data)
        return Results(result, data=data)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data[0], dict):
                    report.append('Metabolities with inconsistent '
                                  '*concentration SD*:<br>')
                    msg = [f"`{it['measurement']}`: {it['value']}% " \
                           f"({it['region']})" for it in self.results.data]
                    report.append(', '.join(msg))

            else:
                report = self.results.data

        return report


class HaveMasksConsistentTissueProbabilities(ExperimentTest):
    """This test checks whether the `LCModel` masks are located in the expected
    brain regions by assessing the probabilities of each segmented tissue (`GM`,
    `WM` and `CSF`) within those masks. Test passes if the probability of `GM` >
    `CSF` and the probability of `WM` > `CSF` as well. Meaning that `GM` and `WM`
    brain tissues have higher chance than `CSF` to be present in the masks'
    regions. Test fails otherwise."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E03096',
    resource_name = 'LCMODEL'

    def run(self, experiment_id):
        import tempfile
        import pandas as pd
        import os

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = r.file('tissue_correction/mrs_tissue_corr.xlsx')
        if not f.exists():
            msg = ['File `tissue_correction/mrs_tissue_corr.xlsx` not found.']
            return Results(False, data=msg)

        fd, fp = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)

        f.get(fp)
        df = pd.read_excel(fp)
        df['csf/gm'] = df['csf']/df['gm']
        df['csf/wm'] = df['csf'] / df['wm']

        cols = ['region', 'gm', 'wm', 'csf']
        q = f'csf > gm or csf > wm'
        data = df.query(q)[cols].to_dict('records')
        os.remove(fp)

        result = not bool(data)
        return Results(result, data=data)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data[0], dict):
                report.append(f'Regions with inconsistent *tissue probabilities*:<br>')
                msg = '<br>'.join(f"`{entry.pop('region')}`: {entry}".replace("'", "`")
                                for entry in self.results.data)
                report.append(msg)
            else:
                report = self.results.data

        return report


class AngularMaskSnapshot(ExperimentTest, Snapshot):
    """This test creates a snapshot of the mask generated in the `Angular Gyrus`
    location by LCModel pipeline. Passes if the snapshot is created successfully.
    Fails otherwise."""

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E00276',
    resource_name = 'LCMODEL'
    fn = 'rAmask_Ang*.nii.gz'
    axes = 'xyz'
    rowsize = 5
    figsize = {'x': (4, 1), 'y': (4, 1), 'z': (4, 1)}
    step = 5
    threshold = 0
    n_slices = {'x': 5, 'y': 5, 'z': 5}
    contours = False
    margin = 150

    def run(self, experiment_id):
        return Snapshot.run(self, experiment_id)

    def report(self):
        return Snapshot.report(self)


class HippocampusMaskSnapshot(AngularMaskSnapshot):
    __doc__ = AngularMaskSnapshot.__doc__.replace('Angular Gyrus', 'Hippocampus')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E00276',
    resource_name = 'LCMODEL'
    fn = 'rAmask_Hippo*.nii.gz'
    axes = 'xyz'
    rowsize = 5
    figsize = {'x': (4, 1), 'y': (4, 1), 'z': (4, 1)}
    step = 5
    threshold = 0
    n_slices = {'x': 5, 'y': 5, 'z': 5}
    contours = False
    margin = 120

    def run(self, experiment_id):
        return Snapshot.run(self, experiment_id)

    def report(self):
        return Snapshot.report(self)


class CuneusMaskSnapshot(AngularMaskSnapshot):
    __doc__ = AngularMaskSnapshot.__doc__.replace('Angular Gyrus', 'Cuneus')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E00276',
    resource_name = 'LCMODEL'
    fn = '*mask_Cun*.nii.gz'
    axes = 'xyz'
    rowsize = 5
    figsize = {'x': (4, 1), 'y': (4, 1), 'z': (4, 1)}
    step = 5
    threshold = 0
    n_slices = {'x': 5, 'y': 5, 'z': 5}
    contours = False
    margin = 150

    def run(self, experiment_id):
        return Snapshot.run(self, experiment_id)

    def report(self):
        return Snapshot.report(self)
