from ..test import ExperimentTest, Results
from . import basil


class HasCorrectItems(ExperimentTest):
    """Passes if a `QSMXT` resource is found and this resource has the
    expected items according to the pipeline
    [specifications](https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/qsmxt#outputs)."""

    passing = 'BBRCDEV_E00276',
    failing = 'BBRCDEV_E00381',
    resource_name = 'QSMXT'
    expected_items = ['qsm/qsm_final/*.nii.gz',
                      'segmentation/t1_segmentations/*.nii.gz',
                      'segmentation/qsm_segmentations/*.nii.gz',
                      'region_analysis/*.csv']

    def run(self, experiment_id):
        result = True

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        missing = []
        for item in self.expected_items:
            f = r.files(item).get()
            if not f:
                missing.append(item)

        if missing:
            result = False

        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectQSMxTVersion(ExperimentTest):
    """This test checks the version of QSMxT used. Passes if `QSMXT`
    outputs were created using the expected version (`{version}`)."""

    passing = 'BBRCDEV_E00276',
    failing = 'BBRCDEV_E00381',
    resource_name = 'QSMXT'
    expected_version = 'QSMxT v1.1.13'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        log = r.file('LOGS/stdout.log')
        if not log.exists():
            msg = '{} log file not found.'.format(self.resource_name)
            return Results(False, data=[msg])

        log_data = self.xnat_instance.get(log._uri).text
        version = [line[14:].split(' (')[0] for line in log_data.splitlines()
                   if line.strip().startswith('INFO: Running QSMxT')]
        if not version:
            msg = 'Version reference not found in log file.'
            return Results(False, data=[msg])

        for v in set(version):
            if v != self.expected_version:
                return Results(False, data=['Incorrect version: {}'.format(v)])

        return Results(True, data=[])


class IsBasalGangliaMeanQSMConsistent(ExperimentTest):
    """QSM susceptibility values reflect the iron level of brain tissues. The
    basal ganglia is a major iron-accumulating brain area, especially with
    pathological degenerative changes. Test passes if iron-rich subcortical
    structures from basal ganglia (i.e. `Pallidum`, `Putamen` and `Caudate`) have
    a positive (> 0) magnetic susceptibility average value. Fails otherwise."""

    passing = 'BBRCDEV_E00276',
    failing = 'BBRCDEV_E00381',
    resource_name = 'QSMXT'

    def run(self, experiment_id):
        import numpy as np

        bl_structs = ["Left-Pallidum", "Right-Pallidum",
                      "Left-Putamen", "Right-Putamen",
                      "Left-Caudate", "Right-Caudate"]

        e = self.xnat_instance.select.experiment(experiment_id)
        stats = e.resource(self.resource_name).stats()

        data = {}
        for s in bl_structs:
            values = stats.query('roi == "{}"'.format(s))['mean'].values
            if values.size == 0:
                values = [np.NaN]

            qsm_mean = float(values[0])
            if not qsm_mean > 0.0:
                data[s] = qsm_mean

        if data:
            return Results(False, data=data)

        return Results(True, data=[])

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, dict):
                report.append('Regions with inconsistent (negative/missing) '
                              'QSM mean value:<br>')
                report.append('<br>'.join(['`{}`: {}'.format(k, v)
                                           for k, v in self.results.data.items()]))
            else:
                report.append(self.results.data)

        return report


class IsT1Session1(basil.IsT1Session1):
    __doc__ = basil.IsT1Session1.__doc__
    __doc__ = __doc__.replace('BASIL', 'QSMXT')

    passing = 'BBRCDEV_E00276',
    failing = 'BBRCDEV_E00398',
    resource_name = 'QSMXT'


class IsT1Session3(basil.IsT1Session3):
    __doc__ = basil.IsT1Session3.__doc__
    __doc__ = __doc__.replace('BASIL', 'QSMXT')

    passing = 'BBRCDEV_E00398',
    failing = 'BBRCDEV_E00276',
    resource_name = 'QSMXT'


class HasExpectedAsegStructures(ExperimentTest):
    """Passes if all expected anatomical structures from Aseg atlas are found
    in the CSV file containing the regional QSM measures per segmented region.
    Fails otherwise."""

    passing = 'BBRCDEV_E00276',
    failing = 'BBRCDEV_E03079',
    structures = {'3rd-Ventricle', '4th-Ventricle', 'Brain-Stem', 'CSF',
                  'Left-Accumbens-area', 'Left-Amygdala', 'Left-Caudate',
                  'Left-Cerebellum-Cortex', 'Left-Cerebellum-White-Matter',
                  'Left-Cerebral-White-Matter', 'Left-Hippocampus',
                  'Left-Inf-Lat-Vent', 'Left-Lateral-Ventricle', 'Left-Pallidum',
                  'Left-Putamen', 'Left-Thalamus-Proper', 'Left-VentralDC',
                  'Left-choroid-plexus', 'Right-Accumbens-area', 'Right-Amygdala',
                  'Right-Caudate', 'Right-Cerebellum-Cortex',
                  'Right-Cerebellum-White-Matter', 'Right-Cerebral-White-Matter',
                  'Right-Hippocampus', 'Right-Inf-Lat-Vent',
                  'Right-Lateral-Ventricle', 'Right-Pallidum', 'Right-Putamen',
                  'Right-Thalamus-Proper', 'Right-VentralDC',
                  'Right-choroid-plexus', 'Unknown', 'WM-hypointensities',
                  'ctx-lh-caudalanteriorcingulate', 'ctx-lh-caudalmiddlefrontal',
                  'ctx-lh-cuneus', 'ctx-lh-entorhinal', 'ctx-lh-fusiform',
                  'ctx-lh-inferiorparietal', 'ctx-lh-inferiortemporal',
                  'ctx-lh-insula', 'ctx-lh-isthmuscingulate',
                  'ctx-lh-lateraloccipital', 'ctx-lh-lateralorbitofrontal',
                  'ctx-lh-lingual', 'ctx-lh-medialorbitofrontal',
                  'ctx-lh-middletemporal', 'ctx-lh-paracentral',
                  'ctx-lh-parahippocampal', 'ctx-lh-parsopercularis',
                  'ctx-lh-parsorbitalis', 'ctx-lh-parstriangularis',
                  'ctx-lh-pericalcarine', 'ctx-lh-postcentral',
                  'ctx-lh-posteriorcingulate', 'ctx-lh-precentral',
                  'ctx-lh-precuneus', 'ctx-lh-rostralanteriorcingulate',
                  'ctx-lh-rostralmiddlefrontal', 'ctx-lh-superiorfrontal',
                  'ctx-lh-superiorparietal', 'ctx-lh-superiortemporal',
                  'ctx-lh-supramarginal', 'ctx-lh-transversetemporal',
                  'ctx-rh-caudalanteriorcingulate', 'ctx-rh-caudalmiddlefrontal',
                  'ctx-rh-cuneus', 'ctx-rh-entorhinal', 'ctx-rh-fusiform',
                  'ctx-rh-inferiorparietal', 'ctx-rh-inferiortemporal',
                  'ctx-rh-insula', 'ctx-rh-isthmuscingulate', 'ctx-rh-lateraloccipital',
                  'ctx-rh-lateralorbitofrontal', 'ctx-rh-lingual',
                  'ctx-rh-medialorbitofrontal', 'ctx-rh-middletemporal',
                  'ctx-rh-paracentral', 'ctx-rh-parahippocampal',
                  'ctx-rh-parsopercularis', 'ctx-rh-parsorbitalis',
                  'ctx-rh-parstriangularis', 'ctx-rh-pericalcarine',
                  'ctx-rh-postcentral', 'ctx-rh-posteriorcingulate',
                  'ctx-rh-precentral', 'ctx-rh-precuneus',
                  'ctx-rh-rostralanteriorcingulate', 'ctx-rh-rostralmiddlefrontal',
                  'ctx-rh-superiorfrontal', 'ctx-rh-superiorparietal',
                  'ctx-rh-superiortemporal', 'ctx-rh-supramarginal',
                  'ctx-rh-transversetemporal'}

    def run(self, experiment_id):
        r = self.xnat_instance.select.experiment(experiment_id).resource('QSMXT')
        try:
            stats = r.stats()
        except IndexError:
            return Results(False, data=['QSMxT region analysis results missing.'])

        found_structs = set(stats.roi)
        missing_structs = set(self.structures).difference(found_structs)

        result = not bool(missing_structs)
        return Results(result, data=sorted(missing_structs))

    def report(self):
        if len(self.results.data) > 1:
            data = ['`{}`'.format(item) for item in self.results.data]
            report = ['Missing aseg structures ({}): {}'.format(len(data),
                                                                ', '.join(data))]
        else:
            report = self.results.data

        return report
