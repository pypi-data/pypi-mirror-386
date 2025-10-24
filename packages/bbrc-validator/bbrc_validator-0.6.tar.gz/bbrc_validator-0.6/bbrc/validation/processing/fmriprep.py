from ..test import ExperimentTest, Results


class HasCorrectItems(ExperimentTest):
    """Passes if a `fMRIPrep` resource is found and this resource has the
    expected items according to the pipeline
    [specifications](https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/fmriprep#outputs)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03089',
    resource_name = 'FMRIPREP'
    expected_items = ['{p}_acq-SEfmap_fmapid-auto00000_desc-coeff_fieldmap.nii.gz',
                      '{p}_acq-SEfmap_fmapid-auto00000_desc-epi_fieldmap.nii.gz',
                      '{p}_acq-SEfmap_fmapid-auto00000_desc-pepolar_fieldmap.svg',
                      '{p}_acq-SEfmap_fmapid-auto00000_desc-preproc_fieldmap.json',
                      '{p}_acq-SEfmap_fmapid-auto00000_desc-preproc_fieldmap.nii.gz',
                      '{p}_desc-about_T1w.html',
                      '{p}_desc-aparcaseg_dseg.nii.gz',
                      '{p}_desc-aseg_dseg.nii.gz',
                      '{p}_desc-brain_mask.json',
                      '{p}_desc-brain_mask.nii.gz',
                      '{p}_desc-conform_T1w.html',
                      '{p}_desc-preproc_T1w.json',
                      '{p}_desc-preproc_T1w.nii.gz',
                      '{p}_desc-reconall_T1w.svg',
                      '{p}_desc-summary_T1w.html',
                      '{p}_dseg.nii.gz',
                      '{p}_dseg.svg',
                      '{p}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5',
                      '{p}_from-MNI152NLin6Asym_to-T1w_mode-image_xfm.h5',
                      '{p}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5',
                      '{p}_from-T1w_to-MNI152NLin6Asym_mode-image_xfm.h5',
                      '{p}_from-T1w_to-fsnative_mode-image_xfm.txt',
                      '{p}_from-fsnative_to-T1w_mode-image_xfm.txt',
                      '{p}_hemi-L_curv.shape.gii',
                      '{p}_hemi-L_inflated.surf.gii',
                      '{p}_hemi-L_midthickness.surf.gii',
                      '{p}_hemi-L_pial.surf.gii',
                      '{p}_hemi-L_smoothwm.surf.gii',
                      '{p}_hemi-L_sulc.shape.gii',
                      '{p}_hemi-L_thickness.shape.gii',
                      '{p}_hemi-R_curv.shape.gii',
                      '{p}_hemi-R_inflated.surf.gii',
                      '{p}_hemi-R_midthickness.surf.gii',
                      '{p}_hemi-R_pial.surf.gii',
                      '{p}_hemi-R_smoothwm.surf.gii',
                      '{p}_hemi-R_sulc.shape.gii',
                      '{p}_hemi-R_thickness.shape.gii',
                      '{p}_label-CSF_probseg.nii.gz',
                      '{p}_label-GM_probseg.nii.gz',
                      '{p}_label-WM_probseg.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_T1w.svg',
                      '{p}_space-MNI152NLin2009cAsym_desc-brain_mask.json',
                      '{p}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_desc-preproc_T1w.json',
                      '{p}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_dseg.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz',
                      '{p}_space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz',
                      '{p}_space-MNI152NLin6Asym_T1w.svg',
                      '{p}_task-rest_dir-PA_AROMAnoiseICs.csv',
                      '{p}_task-rest_dir-PA_boldref.nii.gz',
                      '{p}_task-rest_dir-PA_desc-MELODIC_mixing.tsv',
                      '{p}_task-rest_dir-PA_desc-aroma_bold.svg',
                      '{p}_task-rest_dir-PA_desc-bbregister_bold.svg',
                      '{p}_task-rest_dir-PA_desc-carpetplot_bold.svg',
                      '{p}_task-rest_dir-PA_desc-compcorvar_bold.svg',
                      '{p}_task-rest_dir-PA_desc-confoundcorr_bold.svg',
                      '{p}_task-rest_dir-PA_desc-confounds_timeseries.json',
                      '{p}_task-rest_dir-PA_desc-confounds_timeseries.tsv',
                      '{p}_task-rest_dir-PA_desc-rois_bold.svg',
                      '{p}_task-rest_dir-PA_desc-sdc_bold.svg',
                      '{p}_task-rest_dir-PA_desc-summary_bold.html',
                      '{p}_task-rest_dir-PA_desc-validation_bold.html',
                      '{p}_task-rest_dir-PA_from-T1w_to-scanner_mode-image_xfm.txt',
                      '{p}_task-rest_dir-PA_from-scanner_to-T1w_mode-image_xfm.txt',
                      '{p}_task-rest_dir-PA_from-scanner_to-boldref_mode-image_xfm.txt',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_boldref.nii.gz',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-aparcaseg_dseg.nii.gz',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-aseg_dseg.nii.gz',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-brain_mask.json',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-preproc_bold.json',
                      '{p}_task-rest_dir-PA_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
                      '{p}_task-rest_dir-PA_space-MNI152NLin6Asym_desc-smoothAROMAnonaggr_bold.json',
                      '{p}_task-rest_dir-PA_space-MNI152NLin6Asym_desc-smoothAROMAnonaggr_bold.nii.gz']

    def run(self, experiment_id):
        result = True

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)
        files = r.files().get()

        _, subj, ses = e.attrs.mget(['subject_ID', 'subject_label', 'label'])
        prefix = f'sub-{subj}_ses-{ses}'
        
        missing = [item.format(p=prefix) for item in self.expected_items
                   if item.format(p=prefix) not in files]
        if missing:
            result = False

        return Results(result, data=missing)

    def report(self):
        report = []
        if not self.results.has_passed:
            report.append('Missing items: {}.'
                          .format(self.results.data).replace('\'', '`'))
        return report


class HasCorrectFMRIPrepVersion(ExperimentTest):
    """This test checks the version of `fMRIPrep` used. Passes if outputs
    were created using the expected version (`{version}`)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03089',
    resource_name = 'FMRIPREP'
    expected_version = '22.1.1'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        import toml

        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*fmriprep.toml'))
        if len(f) != 1:
            msg = ['File `fmriprep.toml` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        info = toml.loads(file_content)

        result = bool(info['environment']['version'] == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(info['environment']['version'])]

        return Results(result, data=data)


class HasCorrectHeuDiConvVersion(ExperimentTest):
    """`HeuDiConv` is a DICOM converter for organizing brain imaging data into
    BIDS-compliant structured directory layouts. This test checks if the version
    of `HeuDiConv` used matches the expected version (`{version}`)."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03089',
    resource_name = 'FMRIPREP'
    expected_version = '0.11.6'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = r.file('LOGS/stderr.log')
        if not f.exists():
            msg = ['File `stderr.log` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        info = [ln for ln in file_content.splitlines() if 'heudiconv version' in ln]
        if not info:
            msg = ['No `heudiconv` version information found.']
            return Results(False, data=msg)

        version = info[0].split()[4]
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(version)]

        return Results(result, data=data)


class HasValidDcm2niixVersion(ExperimentTest):
    """fMRI data is converted from DICOM to NIFTI format following the BIDS
    specification required to run `fMRIPrep`. Tool `dcm2niiX` is used for
    such conversion. This test checks if the version of `dcm2niiX` used matches
    the expected version (`{version}`). Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03089',
    resource_name = 'FMRIPREP'
    expected_version = 'v1.0.20211006'
    __doc__ = __doc__.format(version=expected_version)

    def run(self, experiment_id):
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = r.file('LOGS/stderr.log')
        if not f.exists():
            msg = ['File `stderr.log` not found.']
            return Results(False, data=msg)

        file_content = self.xnat_instance.get(f._uri).content.decode('utf-8')
        info = [ln for ln in file_content.splitlines() if 'dcm2niiX version' in ln]
        if not info:
            msg = ['No `dcm2niiX` version information found.']
            return Results(False, data=msg)

        version = info[0].split()[6]
        result = bool(version == self.expected_version)
        data = []
        if not result:
            data = ['Incorrect version: `{}`'.format(version)]

        return Results(result, data=data)


class IsICANumberOfSignalComponentsConsistent(ExperimentTest):
    """`ICA-AROMA` is an ICA-based automatic procedure to identify confounding
    time series related to head-motion in the fMRI data. This test passes if the
    number of independent components labeled as `signal` (contrary to those
    labeled as `noise`) by `ICA-AROMA` is larger than 10 and smaller than 60."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03089',
    resource_name = 'FMRIPREP'
    signal_ics_range = range(10, 60)

    def run(self, experiment_id):
        import numpy as np
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*_task-rest_dir-PA_AROMAnoiseICs.csv'))
        if len(f) != 1:
            msg = ['File `AROMAnoiseICs.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        noise_ics = len([int(x) for x in content.split(',')])

        f = list(r.files('*_task-rest_dir-PA_desc-MELODIC_mixing.tsv'))
        if len(f) != 1:
            msg = ['File `AROMAnoiseICs.csv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        ics_lst = [x.split('\t') for x in content.splitlines()]
        timepoints, total_ics = np.asarray(ics_lst, dtype=float).shape

        signal_ics = total_ics - noise_ics
        result = bool(signal_ics in self.signal_ics_range)
        data = []
        if not result:
            msg = 'Total ICs: {}; signal ICs: {} ({:.2f}%)'
            data = [msg.format(total_ics, signal_ics, 100*signal_ics/total_ics)]

        return Results(result, data=data)


class HasFewMotionOutlierVolumes(ExperimentTest):
    """Framewise Displacement (FD) quantifies the estimated bulk-head motion.
    This test passes if the number of volumes with an FD > 0.5mm is lower than
    238 volumes; i.e. a minimum of 100 seconds of motion-free BOLD signal data
    remains available. Fails otherwise."""

    passing = 'BBRCDEV_E03088',
    failing = 'BBRCDEV_E03655',
    resource_name = 'FMRIPREP'
    max_fd = 0.5
    max_outliers = 238

    def run(self, experiment_id):
        import pandas as pd
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource(self.resource_name)

        f = list(r.files('*-confounds_timeseries.tsv'))
        if len(f) != 1:
            msg = ['File `confounds_timeseries.tsv` not found.']
            return Results(False, data=msg)

        content = self.xnat_instance.get(f[0]._uri).content.decode('utf-8')
        confounds_lst = [x.split('\t') for x in content.splitlines()]

        df = pd.DataFrame(confounds_lst[1:], columns=confounds_lst[0])
        outliers_df = df['framewise_displacement'][1:].apply(pd.to_numeric)
        outlier_vols = len(outliers_df[outliers_df > self.max_fd])

        result = bool(outlier_vols < self.max_outliers)
        return Results(result, data=[outlier_vols])

    def report(self):
        data = self.results.data
        if isinstance(data[0], str):
            return data
        return ['{} volumes annotated as motion outliers'.format(data[0])]
