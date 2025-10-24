from ..test import ExperimentTest, Results
from .mrtrix3 import StructuralConnectivityMatrixSnapshot


class HasCorrectItems(ExperimentTest):
    """Passes if a `XCP-D` resource is found and this resource has the
    expected items according to the pipeline
    [specifications](https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/xcp_d#outputs)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03098',
    resource_name = 'XCP_D'
    expected_items = [
        '{s}_atlas-Glasser_dseg.nii.gz',
        '{s}_atlas-Gordon_dseg.nii.gz',
        '{s}_atlas-Tian_dseg.nii.gz',
        '{s}_atlas-HCP_dseg.nii.gz',
        '{p}_{s}_desc-preproc_T1w.nii.gz',
        '{p}_{s}_dseg.nii.gz',
        '{p}_task-rest_dir-PA_desc-preproc_design.tsv',
        '{p}_task-rest_dir-PA_motion.tsv',
        '{p}_task-rest_dir-PA_outliers.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-DK_coverage.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-DK_measure-pearsoncorrelation_conmat.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-DK_timeseries.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Glasser_coverage.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Glasser_measure-pearsoncorrelation_conmat.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Glasser_timeseries.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Glasser_reho.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Gordon_coverage.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Gordon_measure-pearsoncorrelation_conmat.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Gordon_timeseries.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Gordon_reho.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-HCP_coverage.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-HCP_measure-pearsoncorrelation_conmat.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-HCP_timeseries.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-HCP_reho.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Tian_coverage.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Tian_measure-pearsoncorrelation_conmat.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Tian_timeseries.tsv',
        '{p}_task-rest_dir-PA_{s}_atlas-Tian_reho.tsv',
        '{p}_task-rest_dir-PA_{s}_desc-denoised_bold.nii.gz',
        '{p}_task-rest_dir-PA_{s}_desc-denoisedSmoothed_bold.nii.gz',
        '{p}_task-rest_dir-PA_{s}_desc-linc_qc.csv',
        '{p}_task-rest_dir-PA_{s}_reho.nii.gz',
    ]

    def run(self, experiment_id):
        space = 'space-MNI152NLin2009cAsym'
        result = True

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        files = r.files().get()

        _, subj, ses = e.attrs.mget(['subject_ID', 'subject_label', 'label'])
        prefix = f'sub-{subj}_ses-{ses}'

        missing = [item.format(p=prefix, s=space) for item in self.expected_items
                   if item.format(p=prefix, s=space) not in files]
        if missing:
            result = False

        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectXCPDVersion(ExperimentTest):
    """This test checks the version of `XCP-D` used. Passes if outputs
    were created using the expected version (`{version}`)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03098',
    resource_name = 'XCP_D'
    expected_version = '0.5.1'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = r.file('LOGS/stdout.log')
        if not f.exists():
            msg = ['File `stdout.log` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        info = [ln for ln in file_content.splitlines() if 'xcp_d version' in ln]
        if not info:
            msg = ['No `XCP-D` version information found.']
            return Results(False, data=msg)

        version = info[0].split()[-1].rstrip(':')
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(version)]

        return Results(result, data=data)


class HasCorrectFMRIPrepVersion(ExperimentTest):
    """XCP-D post-processes the outputs of `fMRIPrep`. This test checks the version
    of `fMRIPrep` used and passes if outputs were created using the expected version
    (`{version}`)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'
    expected_version = '22.1.1'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = r.file('LOGS/stdout.log')
        if not f.exists():
            msg = ['File `stdout.log` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        info = [ln for ln in file_content.splitlines() if '*fMRIPrep* version' in ln]
        if not info:
            msg = ['No `fMRIPrep` version information found.']
            return Results(False, data=msg)

        version = info[0].split('*fMRIPrep* version')[1].strip()
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(version)]

        return Results(result, data=data)


class IsNumberOfCensoredVolumesConsistent(ExperimentTest):
    """Participant motion is one of the main sources of artefacts in fMRI data,
    motion can substantially affect signal estimates of functional connectivity.
    `XCP-D` excludes volumes with a framewise displacement (FD) > 0.5 mm. This
    test passes if the number of censored volumes is lower than 100. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'
    max_outliers = 100

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_outliers.tsv'))
        if len(f) != 1:
            msg = ['File `*_outliers.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        outlier_vols = len([line for line in content.splitlines() if line == '1'])

        result = bool(outlier_vols < self.max_outliers)

        return Results(result, data=outlier_vols)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, int):
                report.append('{} volumes censored as motion '
                              'outliers'.format(self.results.data))
            else:
                report.append(self.results.data)

        return report


class IsMeanFramewiseDisplacementConsistent(ExperimentTest):
    """Head motion affects overall data quality, and decreases the strength of
    the relationship between motion and functional connectivity. Mean framewise
    displacement (FD) is the weighted average of rotational and translational
    displacements across imaging frames for all time-series volumes. This
    test passes if the mean FD < 0.5 mm. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03093',
    resource_name = 'XCP_D'
    mean_fd_threshold = 0.5

    def run(self, experiment_id):
        from io import StringIO
        import pandas as pd

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_desc-linc_qc.csv'))
        if len(f) != 1:
            msg = ['File `*_desc-linc_qc.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        df = pd.read_csv(StringIO(content))

        if 'mean_fd' not in df.columns:
            msg = ['Metric `mean_fd` not found']
            return Results(False, data=msg)

        mean_fd = df.mean_fd[0]
        result = bool(mean_fd < self.mean_fd_threshold)

        return Results(result, data=mean_fd)

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, float):
                report.append('High mean FD ({})'.format(self.results.data))
            else:
                report.append(self.results.data)
        return report


class HasCensoredVolumesAtEndsOfData(ExperimentTest):
    """The high-motion censored volumes detected are replaced by an interpolation
    of the signal in those gaps to perform a bandpass filtering step. When the
    censored volumes are at the ends of the data, the interpolation procedure
    turns into an _extrapolation_, predicting signal values outside the range of
    data available, with unpredictable outcomes if not restricted. The current
    pipeline is replacing out-of-bounds censored volumes by the first/last available
    known/valid data points (volumes) to avoid this issue. This test passes if no
    censored volumes are located in both ends of the data. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_outliers.tsv'))
        if len(f) != 1:
            msg = ['File `*_outliers.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        outliers = [int(item) for item in content.splitlines()[1:]]

        result = True
        message = []
        extrapolate = bool(outliers[0] or outliers[-1])
        if extrapolate:
            result = False
            message = ['High-motion censored volumes found at the ends of '
                       'the data run.']

        return Results(result, data=message)


class IsSubjectMotionRemovalConsistent(ExperimentTest):
    """The correlation between head realignment (RMS) and how much the intensity
    of a brain image changes across timepoints (DVARS) depicts the extent to which
    BOLD signal fluctuations relate to subject movement. `XCP-D` computes this
    correlation before (`fd_dvars_correlation_initial`) and after
    (`fd_dvars_correlation_final`) confound regression on BOLD data. This test
    passes if `fd_dvars_correlation_final` correlation coefficient is lower than
    `fd_dvars_correlation_initial`. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'
    metrics = ['fd_dvars_correlation_initial', 'fd_dvars_correlation_final']

    def run(self, experiment_id):
        from io import StringIO
        import pandas as pd

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_desc-linc_qc.csv'))
        if len(f) != 1:
            msg = ['File `*_desc-linc_qc.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        df = pd.read_csv(StringIO(content))

        if not set(self.metrics).issubset(df.columns):
            msg = ['FD-DVARS correlation metrics not found']
            return Results(False, data=msg)

        motion_dv_corrs = [df.fd_dvars_correlation_initial[0],
                           df.fd_dvars_correlation_final[0]]

        result = bool(motion_dv_corrs[0] > motion_dv_corrs[1])

        return Results(result, data=motion_dv_corrs)

    def report(self):
        report = []
        if not self.results.has_passed:
            if len(self.results.data) == 1:
                report.append(self.results.data)
            else:
                msg = ('`{}` ({}) >= `{}` ({}).'.format(self.metrics[1],
                                                        self.results.data[1],
                                                        self.metrics[0],
                                                        self.results.data[0]))
                report.append(msg)
        return report


class IsfMRIToT1wCoregistrationQualityAcceptable(ExperimentTest):
    """The quality of the coregistration between fMRI and T1w images is quantified
    by `XCP-D` using Dice's coefficient, which calculates the percentage of the
    T1w image that also lies within the coregistered fMRI image. This test passes
    if coregistration Dice coefficient > 0.85 (QC measure `coreg_dice`). Fails
    otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'
    metric = 'coreg_dice'
    thresh = 0.85

    def run(self, experiment_id):
        from io import StringIO
        import pandas as pd

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_desc-linc_qc.csv'))
        if len(f) != 1:
            msg = ['File `*_desc-linc_qc.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        df = pd.read_csv(StringIO(content))

        if self.metric not in df.columns:
            msg = [f'Metric `{self.metric}` not found']
            return Results(False, data=msg)

        result = bool(df[self.metric][0] > self.thresh)

        return Results(result, data=df[self.metric][0])

    def report(self):
        report = []
        if not self.results.has_passed:
            if isinstance(self.results.data, list):
                report.append(self.results.data)
            else:
                report.append('Low Dice coefficient '
                              '({})'.format(self.results.data))
        return report


class IsNormalizationToTemplateQualityAcceptable(IsfMRIToT1wCoregistrationQualityAcceptable):
    """The quality of the normalization of fMRI and T1w images to the MNI template
    is quantified by `XCP-D` using Dice's coefficient, which calculates the percentage
    of the template image that also lies within the normalized images. This test
    passes if normalization Dice coefficient > 0.85 (QC measure `norm_dice`). Fails
    otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    metric = 'norm_dice'


class IsRegionalFunctionalConnectivityConsistent(ExperimentTest):
    """This test passes if the functional connectivity (time-series correlation
    coefficient between two signals) for a subset of well-connected region pairs
    (i.e. {}) is greater than 0.5. Test fails if more than 2 region pairs have a
    lower correlation coefficient."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03103',
    resource_name = 'XCP_D'
    min_conn = 0.5
    max_failed = 2
    connected_regions = {
        'ctx-lh-cuneus': 'ctx-rh-cuneus',
        'ctx-lh-precentral': 'ctx-rh-precentral',
        'ctx-lh-lateraloccipital': 'ctx-rh-lateraloccipital',
        'ctx-lh-paracentral': 'ctx-rh-paracentral',
        'ctx-lh-postcentral': 'ctx-rh-postcentral',
        'ctx-lh-pericalcarine': 'ctx-rh-pericalcarine',
        'ctx-lh-lingual': 'ctx-rh-lingual',
        'Left-Putamen': 'Right-Putamen',
        'Left-Caudate': 'Right-Caudate',
        'Left-Cerebellum-Cortex': 'Right-Cerebellum-Cortex',
        'Left-Thalamus': 'Right-Thalamus',
        'Left-Hippocampus': 'Right-Hippocampus',
        'Left-Cerebellum-White-Matter': 'Right-Cerebellum-White-Matter',
    }

    __doc__ = __doc__.format('; '.join(f'`{r1}`-`{r2}`'
                                       for r1, r2 in connected_regions.items()))

    def run(self, experiment_id):
        import pandas as pd
        from io import StringIO

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = list(r.files('*_atlas-DK_measure-pearsoncorrelation_conmat.tsv'))
        if len(f) != 1:
            msg = ['File `*_atlas-DK_measure-pearsoncorrelation_conmat.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        conmat = pd.read_table(StringIO(content), sep='\t').drop(columns=['Node'])
        conmat = conmat.dropna(axis=0, how='all').dropna(axis=1, how='all')
        conmat.index = conmat.columns

        failed_region_pairs = []
        for r1, r2 in self.connected_regions.items():
            try:
                conn_value = conmat[r1][r2]
            except KeyError:
                conn_value = None  # missing regions

            if not conn_value or (conn_value < self.min_conn):
                failed_region_pairs.append([r1, r2, conn_value])

        result = bool(len(failed_region_pairs) <= self.max_failed)

        return Results(result, data=failed_region_pairs)

    def report(self):
        if self.results.has_passed:
            report = []
        elif isinstance(self.results.data[0], str):
            report = self.results.data
        else:
            data = '<br> '.join(f'`{r1}`-`{r2}` ({val})'
                                for r1, r2, val in self.results.data)
            report = [f'Regions with weak functional connectivity: <br>{data}']

        return report


class HasFewExcludedLowCoverageRegions(ExperimentTest):
    """Atlas regions are sometimes lost when warping/downsampling atlas to the BOLD
    images. `XCP-D` calculates the coverage ratio of each of the (Desikan-Killiany)
    atlas regions by the masked BOLD. For quality purposes, those regions without
    a minimium coverage ratio of 50% of the region voxels are discarded and its
    time-series replaced with NaNs. This test checks that the number of excluded
    atlas regions due to low coverage is smaller than 8. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03104',
    resource_name = 'XCP_D'
    max_missing_regions = 8

    def run(self, experiment_id):
        import pandas as pd
        from io import StringIO

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = list(r.files('*_atlas-DK_coverage.tsv'))
        if len(f) != 1:
            msg = ['File `*_atlas-DK_coverage.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        coverage = pd.read_table(StringIO(content), sep='\t')

        miss = coverage.query(f'coverage < 0.5').to_dict('records')
        result = bool(len(miss) < self.max_missing_regions)

        return Results(result, data=miss)

    def report(self):
        if self.results.has_passed:
            report = []
        elif isinstance(self.results.data[0], str):
            report = self.results.data
        else:
            data = '<br> '.join(f'`{i["Node"]}` ({round(i["coverage"], 2)})'
                                for i in self.results.data)
            report = [f'Low-coverage missing regions: <br>{data}']

        return report


class FunctionalConnectivityMatrixSnapshot(StructuralConnectivityMatrixSnapshot):
    """This test creates a snapshot of the quantified functional connectivity
    between parcellation pairs in the Desikan-Killiany atlas
    (`*_atlas-DK_measure-pearsoncorrelation_conmat.csv` file). Passes if the
    snapshot is created successfully. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E02872',
    resource_name = 'XCP_D'

    def run(self, experiment_id):
        import os
        import pandas as pd
        from io import StringIO

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        f = list(r.files('*_atlas-DK_measure-pearsoncorrelation_conmat.tsv'))
        if len(f) != 1:
            msg = ['File `*atlas-DK_measure-pearsoncorrelation_conmat.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        df = pd.read_table(StringIO(content), sep='\t').drop(columns=['Node'])
        df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')

        path = self.__heatmap__(data=df.to_numpy(),
                                label=f"{experiment_id} functional connectivity matrix",
                                cmap='viridis', vmin=0, vmax=1)

        return Results(True, [path])
