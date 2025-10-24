from . import pet
from ..test import ExperimentTest, Results
from ..utils import __is_valid_scan__, __read_first_dicom__


class IsScannerVersionCorrect(pet.IsScannerVersionCorrect):

    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E02948',
    scanner_info = {'Manufacturer': ['SIEMENS'],
                    'ManufacturerModelName': ['Biograph64', 'Biograph64_mCT', 'Biograph64_Vision X'],
                    'SoftwareVersions': ['VG62B', 'VG62C', 'VG80C']}
    __doc__ = pet.IsScannerVersionCorrect.__doc__


class HasUsableT1(pet.HasUsableT1):
    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E02948',
    included_projects = ['testenv', 'ALFA_PLUS_V2', 'ALFA_PLUS2_V2',
                         'ALFA_PLUS_VX', 'ALFA_PLUS_V3', 'ALFA_PLUS2_V3',
                         'BETA_AARC', 'BETA_AARC_V3', 'BETA_AARC_VX', 'BETA_AARC_V5']
    __doc__ = pet.HasUsableT1.__doc__


class IsInjectionTimeConsistent(pet.IsInjectionTimeConsistent):
    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E02948',
    injection_times = {'t807': 80,
                       'fluorodeoxyglucose': 80}

    __doc__ = pet.IsInjectionTimeConsistent.__doc__
    __doc__ = __doc__.replace(
        'Flutemetamol PET: 90 min ± 20%; Fluorodeoxyglucose PET: 45 min ± 20%',
        'TAU PET: 80 min ± 20%')
    

class HasUsableReconAC4x5min(ExperimentTest):
    """This test determines whether a session contains a usable tau PET scan,
    defined as an attenuation-corrected (AC) PSF TOF reconstruction acquired as
    4x5 min frames, suitable for further processing. The test passes if exactly
    one valid tau PET scan is found, or multiple scans are present but only one
    is labeled as `usable`. Fails otherwise."""

    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E04551',
    scan_type = 'ReconAC4x5min'

    def _compare_dicom_tags(self, ds, expected_attributes):
        diff = []
        for k, v in expected_attributes.items():
            if ds[k].value == v:
                continue
            else:
                diff.append((k, ds[k].value, v))
        return diff

    def run(self, experiment_id):
        import json
        import bbrc
        import os
        import os.path as op
        from .data import HasNifti

        scan_labels = self.lut.get(self.scan_type, [])

        columns = ['xnat:petScanData/type',
                   'xnat:petScanData/quality',
                   'xnat:petScanData/frames']

        data = self.xnat_instance.array.scans(experiment_id=experiment_id,
                                                scan_type='xnat:petScanData',
                                                columns=columns).data
        scans = {s['xnat:petscandata/id']: s for s in data}

        protocols_location = op.join(op.dirname(bbrc.__file__), 'data',
                                     'protocol_validation')
        protocols = [op.splitext(item)[0].strip()
                     for item in os.listdir(protocols_location)]

        protocol_attributes = {}
        for p in protocols:
            if p.startswith('PET'):
                fp = op.join(protocols_location, f'{p}.json')
                with open(fp, 'r') as f:
                    protocol_attributes[p] = json.load(f)

        valid_scans = {
                    str(scan_id): scan_data for scan_id, scan_data in scans.items()
                    if __is_valid_scan__(self.xnat_instance, scan_data)
                    and scan_data['xnat:petscandata/type'] in scan_labels}
        
        if not valid_scans:
            return Results(False,
                           data=[f'No valid {self.scan_type} scans found'])
        if len(valid_scans) > 1:
            return Results(False,
                           data=[f'Multiple {self.scan_type} scans.'])

        scan_id = list(valid_scans.keys())[0]

        c = HasNifti(self.lut, self.xnat_instance).run(experiment_id, scan_id)
        if not c.has_passed:
            msg = 'Test HasNifti failed.'
            return Results(False, data=[msg])

        ds = __read_first_dicom__(self.xnat_instance, experiment_id, scan_id)
        stype = scans[scan_id]['xnat:petscandata/type'].replace(' ', '_')
        diff = self._compare_dicom_tags(ds, protocol_attributes[stype])
        validation_result = bool(len(diff) == 0)

        if not validation_result:
            msg = [f'Scan {scan_id} does not match {stype} protocol.']
            for d in diff:
                msg.append(f'DICOM tag {d[0]}: found {d[1]}, expected {d[2]}')
            return Results(False, data=msg)
        
        return Results(True, data=[scan_id])
        

class IsCenTauRzRunnable(ExperimentTest):
    """This check validates whether the given PET session meets the requirements
    for quantifying brain tau load using the CenTauRz method. Test passes if one
    PET scan within the session is suitable for CenTauRz processing. Fails
    otherwise."""

    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E04551',
    tests = [HasUsableReconAC4x5min, HasUsableT1]

    def run(self, experiment_id):

        for test in self.tests:
            res = test(self.lut, self.xnat_instance).run(experiment_id)
            if not res.has_passed:
                return Results(False, data=['%s failed: %s. Not runnable.'
                                            % (test.__name__, res.data[0])])

        return Results(True, data=[])
    

class IsAlfaCohort(ExperimentTest):
    """Validate if a participant belongs to the ALFA cohort within the TAU_PET
    project. The test passes if the participant has an MRI session containing a
    usable T1-weighted sequence from an ALFA-related project; it fails otherwise."""

    passing = 'BBRCDEV_E02957',
    failing = 'BBRCDEV_E04551',
    cohort = 'ALFA'
    
    def run(self, experiment_id):

        c = HasUsableT1(self.lut, self.xnat_instance).run(experiment_id)
        if not c.has_passed:
            msg = 'Test HasUsableT1 failed.'
            return Results(False, data=[msg])
        
        mr_exp = c.data[0]['MR_ID']
        scan_id = c.data[0]['MR_scanID']
        ds = __read_first_dicom__(self.xnat_instance, mr_exp, scan_id)
        if not ds:
            return Results(False,
                           [f'DICOM parsing error (scan {scan_id})'])
        
        study_description = ds.StudyDescription.lower()
        if self.cohort.lower() not in study_description:
            msg = 'Participant does not belong to {} ' \
                  'cohort (Study description: `{}`)'.format(self.cohort,
                                                            ds.StudyDescription)
            return Results(False, data=[msg])

        return Results(True, data=[])
    

class IsBetaCohort(IsAlfaCohort):
    __doc__ = IsAlfaCohort.__doc__.replace('ALFA', 'BETA')

    passing = 'BBRCDEV_E04551',
    failing = 'BBRCDEV_E02957',
    cohort = 'BETA'
