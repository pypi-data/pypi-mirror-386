from ..test import ExperimentTest, ScanTest, Results
from ..utils import __is_valid_scan__, __read_first_dicom__


class IsTracerCorrect(ExperimentTest):
    """PET imaging technique detects gamma rays emitted by a positron-emitting
    radionuclide (tracer) introduced into the body. PET image acquisitions
    register in the DICOM header information about the specific tracer substance
    used, which is retrieved and stored in XNAT. This test passes if the Tracer
    DICOM attribute consistently matches the tracer-related information in the
    Study Description. Fails otherwise."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E00278',

    def run(self, experiment_id):

        pet_baseline_radionuclides = {'fdg': 'Fluorodeoxyglucose',
                                      'flutemetamol': 'Flutemetamol',
                                      'alfa_plus_v2_pet': 'Flutemetamol'}

        exp_info = self.xnat_instance.array.experiments(
            experiment_id=experiment_id,
            experiment_type='xnat:imageSessionData',
            columns=['tracer_name', 'tracer_dose', 'session_type']).data[0]

        registered_tracer = exp_info['tracer_name']
        if not registered_tracer:
            return Results(False, data=['No tracer registered'])

        session_desc = exp_info['session_type']
        expected_tracer = [pet_baseline_radionuclides[tracer]
                           for tracer in pet_baseline_radionuclides.keys()
                           if tracer in session_desc.lower()]
        if not expected_tracer:
            return Results(False,
                           data=['No suitable tracer found in Study '
                                 'Description `%s`' % session_desc])

        result = str(registered_tracer) == str(expected_tracer[0])
        data = []
        if not result:
            data = {'registered': registered_tracer,
                    'expected': expected_tracer[0]}

        return Results(result, data)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, dict):
                report.append('Registered tracer `%s` not matching the expected '
                              'one `%s`' % (self.results.data['registered'],
                                            self.results.data['expected']))
            else:
                report.append(self.results.data[0])

        return report


class IsSeriesDescriptionConsistent(ScanTest):
    """ALFA+ PET protocol includes the tracer in the DICOM Series Description
    (scan type) as well as in the Study Description (session type).
    This test passes if a given scan has tracer-related information consistent
    across Study and Series descriptions. Test skipped if scan is not a PET scan.
    Fails otherwise."""

    passing = 'BBRCDEV_E00745', '5'
    failing = 'BBRCDEV_E00278', '7'

    def run(self, experiment_id, scan_id):

        pet_baseline_radionuclides = {'fdg': 'Fluorodeoxyglucose',
                                      'flutemetamol': 'Flutemetamol'}

        cols = ['xnat:petScanData/type',
                'xnat:petScanData/id',
                'xnat:petSessionData/session_type']
        scan_info = self.xnat_instance.array.scans(
            experiment_id=experiment_id,
            experiment_type='xnat:petSessionData',
            scan_type='xnat:petScanData',
            columns=cols).data

        scan = [e for e in scan_info
                if e.get('xnat:petscandata/id', '') == scan_id]
        if len(scan) == 0:
            return Results(None)

        scan_type = scan[0]['xnat:petscandata/type']
        scan_tracer = [pet_baseline_radionuclides[tracer]
                       for tracer in pet_baseline_radionuclides.keys()
                       if tracer in scan_type.lower()]

        study_desc = scan[0]['xnat:petsessiondata/session_type']
        study_tracer = [pet_baseline_radionuclides[tracer]
                        for tracer in pet_baseline_radionuclides.keys()
                        if tracer in study_desc.lower()]

        result = study_tracer == scan_tracer
        return Results(result)


class IsScannerVersionCorrect(ExperimentTest):
    """The PET scanner manufacturer, model and software version used for
    generating a dataset is registered in the DICOM header. Asserting its
    consistency across acquired datasets might be critical when comparing them
    longitudinally. This test checks if a PET Session was acquired using a
    `SIEMENS Biograph64` scanner. Fails otherwise."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E00281',
    scanner_info = {'Manufacturer': ['SIEMENS'],
                    'ManufacturerModelName': ['Biograph64', 'Biograph64_mCT'],
                    'SoftwareVersions': ['VG51C', 'VG62B']}

    def run(self, experiment_id):
        from pydicom.multival import MultiValue

        pet_dtypes = ['xnat:ctScanData', 'xnat:petScanData']

        e = self.xnat_instance.select.experiment(experiment_id)
        scans = [s.id() for s in e.scans() if s.datatype() in pet_dtypes]
        if not scans:
            return Results(False, ['No PET scans found'])
        scan_id = scans.pop()

        ds = __read_first_dicom__(self.xnat_instance, experiment_id, scan_id)
        if not ds:
            return Results(False,
                           [f'DICOM parsing error (scan {scan_id})'])

        missing_tags = []
        wrong_items, valid_items = {}, {}
        for field in self.scanner_info.keys():
            value = ds.get(field, None)
            if isinstance(value, MultiValue):
                value = value[0]  # SoftwareVersions is a multivalued element

            if not value:
                missing_tags.append(field)
            elif value not in self.scanner_info[field]:
                wrong_items[field] = value
            else:
                valid_items[field] = value

        if missing_tags:
            return Results(False,
                           [f'{missing_tags} DICOM tags not present'])

        result = len(wrong_items) == 0
        if not result:
            return Results(result, wrong_items)
        return Results(result, [valid_items])

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, dict):
                report.append('Unexpected PET Scanner versioning '
                              'settings:<br> %s' % self.results.data)
            else:
                report = self.results.data    
        else:
            report = self.results.data

        return report


class IsSubjectIdCorrect(ExperimentTest):
    """PET scans are acquired in an external site and the internal volunteer IDs
    are afterwards assigned following a (pseudo)manually procedure highly sensitive
    to human errors at data entry. This test checks if the Subject ID is valid,
    i.e. composed by 5 numeric digits. Fails otherwise."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E00281',

    def run(self, experiment_id):

        data = self.xnat_instance.array.experiments(
            experiment_id=experiment_id,
            columns=['label', 'subject_label']).data

        subject_id, project = [data[0][e] for e in ['subject_label', 'project']]
        result = (len(subject_id) == 5 and subject_id.isdigit())
        data = []
        if not result:
            data = ['Invalid SubjectID `%s`' % subject_id]
        return Results(result, data)


class IsSubjectWeightConsistent(ExperimentTest):
    """Check if subject's weight is registered in the DICOM header and if the
    value represents a realistic weight, i.e. ranges between 40 and 150 kgs.
    Fails otherwise."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E02102',

    def run(self, experiment_id):
        options = ['ID', 'label', 'xnat:petsessiondata/dcmPatientWeight']
        data = self.xnat_instance.array.experiments(
            experiment_id=experiment_id,
            experiment_type='xnat:petSessionData',
            columns=options).data

        patient_weight = data[0]['xnat:petsessiondata/dcmpatientweight']
        if not patient_weight:
            return Results(False, ['Weight not registered in the DICOM header'])

        result = (40 <= float(patient_weight) <= 150)
        data = []
        if not result:
            data = ['Potentially invalid weight value: %skg' % patient_weight]
        return Results(result, data)


class IsTracerDosageConsistent(ExperimentTest):
    """Check if total amount of radiopharmaceutical dose administered to the
    patient, measured in Becquerels (Bq), is registered and has a consistent
    value. This test checks if the total amount of radiopharmaceutical injected
    dose is within an acceptable range of 1.5e8 - 3.5e8 Bq. Fails otherwise."""

    passing = 'BBRCDEV_E02102',
    failing = 'BBRCDEV_E02103',

    def run(self, experiment_id):
        options = ['ID', 'label', 'tracer_dose']
        data = self.xnat_instance.array.experiments(
            experiment_id=experiment_id,
            experiment_type='xnat:petSessionData',
            columns=options).data

        tracer_dose = data[0]['tracer_dose']
        if not tracer_dose:
            return Results(False, ['Tracer dose not registered'])

        result = (1.5E+8 < float(tracer_dose) < 3.5E+8)
        data = []
        if not result:
            data = ['Potentially invalid tracer dose value: %s' % tracer_dose]
        return Results(result, data)


class HasUsableT1(ExperimentTest):
    """PET image data require structural information to be used in combination
    with PET data for processing. Specifically, a valid MRI T1 sequence from
    the same subject is needed as close in time to the PET acquisition as possible.
    This test attempts at selecting an MR session with a suitable ALFA+ protocol
    T1 sequence from all the available subject-related MR sessions in XNAT.
    To do so, it uses existing *ArchivingValidator* properties `HasPreferredT1`
    and `IsFreeSurferRunnable` to filter suited MR session candidates and finally
    uses absolute time distance (`timedelta`) between PET and MR acquisitions to
    select the closest MR session available. This test passes if there is an MRI 
    session with a usable T1 sequence (`T1_ALFA1`) from the given subject whose
    acquisition date is closer than 500 days (+5% margin) to the PET acquisition
    data. Fails otherwise. A *WARNING* message is displayed if the time-span
    between PET and MR acquisitions exceeds the 500 days limit by a +5% margin.
    *Requisites:* This test depends on `HasPreferredT1` and `IsFreeSurferRunnable`
    test results of *ArchivingValidator*."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E02102',
    included_projects = ['ALFA_PLUS', 'ALFA_OPCIONAL',
                         'ALFA_PLUS2', 'EPAD', 'testenv',
                         'ALFA_PLUS_V2', 'ALFA_PLUS2_V2',
                         'ALFA_PLUS_VX', 'ALFA_PLUS_V3']

    def get_validation_data(self, experiment_id, experiment_name,
                            validator='ArchivingValidator'):
        import json

        results_json_file = '%s_%s.json' % (validator, experiment_name)
        uri = '/data/experiments/%s/resources/%s/files/%s' \
              % (experiment_id, 'BBRC_VALIDATOR', results_json_file)

        return json.loads(self.xnat_instance.get(uri).text)

    def run(self, experiment_id):
        import datetime as dt
        import dateparser as dp

        fields = ['ID', 'label', 'date', 'project',
                  'subject_ID', 'subject_label']
        labels = self.xnat_instance.array.experiments(
            experiment_id=experiment_id,
            experiment_type='xnat:petSessionData',
            columns=fields).data[0]

        mris = self.xnat_instance.array.mrsessions(
            project_id=None,
            subject_label=labels['subject_label'],
            columns=fields).data
        if not mris:
            return Results(False, ['No MR sessions found.'])

        valid_mris = [i for i in mris if i['project'] in self.included_projects]

        candidate_t1s = []
        for mri in valid_mris:
            try:
                val = self.get_validation_data(mri['ID'], mri['label'])
            except ValueError:
                continue

            if 'HasUsableT1' not in val.keys():
                continue
            else:
                if val['HasUsableT1']['has_passed']:
                    scan_id = val['HasUsableT1']['data'][0]

                    s = self.xnat_instance.select.experiment(mri['ID']).scan(scan_id)
                    if s.attrs.get('type').strip() != 'T1_ALFA1':
                        continue

                    candidate_t1s.append(
                        {'MR_ID': mri['ID'],
                         'MR_date': mri['date'],
                         'MR_project': mri['project'],
                         'MR_scanID': scan_id,
                         'acq_timedelta': abs(
                             dp.parse(labels['date']) - dp.parse(mri['date']))
                         })
                else:
                    continue

        if not candidate_t1s:
            return Results(False, ['No MR sessions with valid T1 scans found.'])

        valid_t1 = sorted(candidate_t1s,
                          key=lambda item: item['acq_timedelta'],
                          reverse=False)[0]
        # Restriction: MR and PET aquisitions should be closer than 500 days time (+5% margin)
        if valid_t1['acq_timedelta'] > dt.timedelta(days=525):
            return Results(False, ['MR sessions with valid T1 scans exceed 520 (+5%)'
                                   'days time-distance required between MR '
                                   'and PET acquisitions.'])

        if dt.timedelta(days=525) > valid_t1['acq_timedelta'] > dt.timedelta(days=500):
            valid_t1['notes'] = ('WARNING: The selected MR session exceeds the '
                                 'expected limit by an acceptable margin '
                                 f'({valid_t1["acq_timedelta"].days} days).')

        # timedelta objects are not JSON serializable, exclude it from results
        valid_t1.pop('acq_timedelta')
        return Results(bool(valid_t1), data=[valid_t1])

    def report(self):
        report = []
        data = self.results.data[0]
        if self.results.has_passed and 'notes' in data.keys():
            report.append(f'**{data["notes"]}**<br>')
            data.pop('notes')
        report.append(data)
        return report


class IsCentiloidRunnable(ExperimentTest):
    """This check validates that the given PETSession fulfills the requirements
    for quantifying the brain's amyloid load using the `Centiloid` method. This
    test passes if: session's PET tracer is `Flutemetamol`, scanning sequences
    `PET_Flutemetamol_4x5min` or `PETAC_Standard_recon2` are suitable for
    processing and if `HasUsableT1` test has successfully passed. Fails otherwise."""

    passing = 'BBRCDEV_E02124',
    failing = 'BBRCDEV_E02102',
    scan_labels = ['PET_Flutemetamol_4x5min', 'PETAC_Standard_recon2']
    scan_frames = 436

    def run(self, experiment_id):

        from .data import HasNifti, IsClassicDICOM, HasUncompressedPixelData

        columns = ['xnat:petScanData/type',
                   'xnat:petScanData/quality',
                   'xnat:petScanData/frames']

        data = self.xnat_instance.array.scans(experiment_id=experiment_id,
                                              scan_type='xnat:petScanData',
                                              columns=columns).data
        scans = {s['xnat:petscandata/id']: s for s in data}

        # filter out unsuitable scan_data items
        valid_pet_scans = {
            str(scan_id): scan_data for scan_id, scan_data in scans.items()
            if __is_valid_scan__(self.xnat_instance, scan_data)
            and scan_data['xnat:petscandata/type'].strip() in self.scan_labels
            and int(scan_data['xnat:petscandata/frames']) == self.scan_frames}

        if not valid_pet_scans:
            return Results(False, data=['No usable scans found. '
                                        'Not runnable.'])
        elif len(valid_pet_scans) > 1:
            return Results(False, data=['Multiple scans found. '
                                        'Not runnable.'])

        pet_scan_id = list(valid_pet_scans.keys())[0]

        # built-in checks
        scan_required = [HasNifti,
                         IsClassicDICOM,
                         HasUncompressedPixelData,
                         IsSeriesDescriptionConsistent]
        for each in scan_required:
            c = each(self.lut, self.xnat_instance).run(experiment_id, pet_scan_id)
            if not c.has_passed:
                msg = 'Test %s failed. Pipeline not runnable.' % each.__name__
                return Results(False, data=[msg])

        exp_required = [IsTracerCorrect, HasUsableT1]

        for each in exp_required:
            c = each(self.lut, self.xnat_instance).run(experiment_id)
            if not c.has_passed:
                msg = 'Test %s failed. Pipeline not runnable.' % each.__name__
                return Results(False, data=[msg])

        return Results(True, data=[])


class IsFDGQuantificationRunnable(IsCentiloidRunnable):
    __doc__ = """This check validates that the given PETSession fulfills the 
    requirements for quantifying the cerebral glucose metabolic rate. This test 
    passes if: session's PET tracer is `Fluorodeoxyglucose`, scanning sequence
    `PET_FDG_4x5min` is suitable for processing and if `HasUsableT1` test has
    successfully passed. Fails otherwise."""

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E02103',
    scan_labels = ['PET_FDG_4x5min']
    scan_frames = 436


class IsInjectionTimeConsistent(ExperimentTest):
    """PET technique requires injecting a positron-emitting radiopharmaceutical
    (tracer) into the subject's bloodstream a certain amount of time before
    imaging the subject. The timespan required between tracer injection and the
    image acquisition event depends mostly on the compound used, body part
    scanned and/or imaging protocol. PET modalities register both, the injection
    time (ie. `Radiopharmaceutical Start Time`) and the scan acquisition time
    (ie. `SeriesTime`) as attributes in the DICOM header.
    Test passes if the time elapsed between tracer injection and scan
    acquisition (as registered in the DICOM header attributes) is consistent
    with the expected values for each type of PET session
    (Flutemetamol PET: 90 min ± 20%; Fluorodeoxyglucose PET: 45 min ± 20%).
    Fails otherwise."""

    passing = 'BBRCDEV_E02124',
    failing = 'BBRCDEV_E00278',

    injection_times = {'flutemetamol': 90,
                       'fluorodeoxyglucose': 45}

    def pet_times(self, experiment_id, scan_id):
        """Retrieve the radiopharmaceutical start datetime and series
        datetime from the DICOM header of a randomly selected file of the
        given experiment and scan. """

        d = __read_first_dicom__(self.xnat_instance, experiment_id, scan_id)
        series_date = d.SeriesDate
        series_time = d.SeriesTime
        inj_time = d.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime

        return series_date+inj_time, series_date+series_time

    def run(self, experiment_id):
        passed = True
        failed = {}

        scan_data = self.xnat_instance.array.scans(experiment_id=experiment_id,
                                                   scan_type='xnat:petScanData').data
        scans = [item['xnat:petscandata/id'] for item in scan_data]

        e = self.xnat_instance.select.experiment(experiment_id)
        tracer = e.attrs.get('tracer_name').lower()
        if tracer not in self.injection_times.keys():
            return Results(False,
                           data=['Unexpected/missing tracer ({})'.format(tracer)])

        for s in scans:
            s_type = e.scan(s).attrs.get('type')
            inj, acq = self.pet_times(experiment_id, s)

            # parse the date&time strings accordingly and substract injection to acquisition (secs)
            from datetime import datetime
            inj_dt = datetime.strptime(inj, '%Y%m%d%H%M%S.%f')
            acq_dt = datetime.strptime(acq, '%Y%m%d%H%M%S.%f')
            diff = (acq_dt-inj_dt).seconds

            # set low and high timespan limits to threshold ± 20%
            low_limit = self.injection_times[tracer] * 60 * (1 - 0.2)
            high_limit = self.injection_times[tracer] * 60 * (1 + 0.2)
            if not bool(low_limit < float(diff) < high_limit):
                failed[s] = diff

        if failed:
            passed = False
            failed['tracer'] = tracer

        return Results(passed, data=failed)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, list):
                report = self.results.data
            elif isinstance(self.results.data, dict):
                tracer = self.results.data.pop('tracer')
                report.append('Scans with abnormal injection-to-acquisition '
                              'timespan ({} expected value: {} minutes):<br>'
                              .format(tracer.capitalize(),
                                      self.injection_times[tracer]))
                report.append('<br>'.join(['{}: {:.2f} minutes'.format(k, v/60)
                                           for k, v in self.results.data.items()]))
        return report
