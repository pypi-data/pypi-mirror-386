from ..test import ExperimentTest, Results
from . import dtifit


class HasCorrectNumberOfItems(dtifit.HasCorrectNumberOfItems):
    __doc__ = (dtifit.HasCorrectNumberOfItems.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT').
               replace('(i.e. 48)', '(i.e. 52)'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    CORRECT_NUMBER = 52
    resource_name = 'DWIFSLPREPROC_DTIFIT'


class HasCorrectItems(dtifit.HasCorrectItems):
    __doc__ = (dtifit.HasCorrectItems.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT').
               replace('xnat-pipelines', 'docker-images').
               replace('dtifit#outputs', 'dwifslpreproc_dtifit#outputs'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    expected_items = ['PA_AP_b0.nii.gz',
                      'PA_b0_0.nii.gz',
                      'log.txt',
                      '*_dn.nii.gz',
                      'topup/topup_datain.txt',
                      'topup/field_fieldcoef.nii.gz',
                      'topup/field_movpar.txt',
                      'topup/topup_in.topup_log',
                      'topup/unwarped_b0.nii.gz',
                      'topup/applytopup_config.txt',
                      'topup/applytopup_indices.txt',
                      'eddy/eddy_command_txt',
                      'eddy/eddy_movement_rms',
                      'eddy/eddy_outlier_map',
                      'eddy/eddy_outlier_n_sqr_stdev_map',
                      'eddy/eddy_outlier_n_stdev_map',
                      'eddy/eddy_outlier_report',
                      'eddy/eddy_parameters',
                      'eddy/eddy_post_eddy_shell_alignment_parameters',
                      'eddy/eddy_post_eddy_shell_PE_translation_parameters',
                      'eddy/eddy_restricted_movement_rms',
                      'eddy/eddy_values_of_all_input_parameters',
                      'eddy/eddy_mask.nii',
                      'eddy/eddy_config.txt',
                      'eddy/eddy_indices.txt',
                      'eddy/quad/qc.json',
                      'eddy/quad/qc.pdf',
                      '*_dn_ec.eddy_rotated_bvecs',
                      '*_dn_ec_fit_FA.nii.gz',
                      '*_dn_ec_fit_L1.nii.gz',
                      '*_dn_ec_fit_L2.nii.gz',
                      '*_dn_ec_fit_L3.nii.gz',
                      '*_dn_ec_fit_MD.nii.gz',
                      '*_dn_ec_fit_MO.nii.gz',
                      '*_dn_ec_fit_RD.nii.gz',
                      '*_dn_ec_fit_S0.nii.gz',
                      '*_dn_ec_fit_V1.nii.gz',
                      '*_dn_ec_fit_V2.nii.gz',
                      '*_dn_ec_fit_V3.nii.gz',
                      '*_dn_ec.nii.gz']


class HasCorrectMRtrix3Version(ExperimentTest):
    __doc__ = (dtifit.HasCorrectMRtrix3Version.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT').
               replace('3.0.2', '3.0.4'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    expected_version = '== dwifslpreproc 3.0.4 =='
    init_line = expected_version[:16]

    def run(self, experiment_id):
        
        e = self.xnat_instance.select.experiment(experiment_id)
        log = e.resource(self.resource_name).file('LOGS/stdout.log')
        if not log.exists():
            msg = '{} log file not found.'.format(self.resource_name)
            return Results(False, data=[msg])

        log_data = self.xnat_instance.get(log.attributes()['URI']).text
        version = [line for line in log_data.splitlines()
                   if line.strip().startswith(self.init_line)]
        if not version:
            return Results(False, data=['No MRtrix3 version '
                                        'registered in the logs.'])
        if version[0] != self.expected_version:
            return Results(False, data=version)

        return Results(True, data=[])


class HasCorrectFSLVersion(ExperimentTest):
    __doc__ = (dtifit.HasCorrectFSLVersion.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT').
               replace('6.0.4:ddd0a010', '6.0.7.7'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    expected_version = 'FSL Version: 6.0.7.7'

    def run(self, experiment_id):
        
        e = self.xnat_instance.select.experiment(experiment_id)
        log = e.resource(self.resource_name).file('LOGS/stdout.log')
        if not log.exists():
            msg = '{} log file not found.'.format(self.resource_name)
            return Results(False, data=[msg])

        log_data = self.xnat_instance.get(log.attributes()['URI']).text
        version = [line for line in log_data.splitlines()
                   if line.startswith('FSL Version')]
        if not version:
            return Results(False, data=['No FSL version '
                                        'registered in the logs.'])
        if not version[0].startswith(self.expected_version):
            return Results(False, data=version)

        return Results(True, data=[])


class DTIFITSnapshotFA(dtifit.DTIFITSnapshotFA):
    __doc__ = (dtifit.DTIFITSnapshotFA.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'


class DTIFITSnapshotRGB(dtifit.DTIFITSnapshotRGB):
    __doc__ = (dtifit.DTIFITSnapshotRGB.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'


class DTIFITSnapshotTOPUP(dtifit.DTIFITSnapshotTOPUP):
    __doc__ = (dtifit.DTIFITSnapshotTOPUP.__doc__.
               replace('TOPUP_DTIFIT', 'DWIFSLPREPROC_DTIFIT'))

    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03058',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    files = ['PA_b0_0.nii.gz', 'topup/unwarped_b0.nii.gz']


class HasFewNegativeVoxelsInMD(dtifit.HasFewNegativeVoxelsInMD):
    __doc__ = dtifit.HasFewNegativeVoxelsInMD.__doc__
    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03964',
    resource_name = 'DWIFSLPREPROC_DTIFIT'


class HasAcceptableAverageSNR(dtifit.HasAcceptableAverageSNR):
    __doc__ = dtifit.HasAcceptableAverageSNR.__doc__
    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03963',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    eddyqc_file = 'eddy/quad/qc.json'


class HasAcceptableAverageCNR(dtifit.HasAcceptableAverageCNR):
    __doc__ = dtifit.HasAcceptableAverageCNR.__doc__
    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03963',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    eddyqc_file = 'eddy/quad/qc.json'


class HasAcceptableOutliersPercentage(dtifit.HasAcceptableOutliersPercentage):
    __doc__ = dtifit.HasAcceptableOutliersPercentage.__doc__
    passing = 'BBRCDEV_E03863',
    failing = 'BBRCDEV_E03963',
    resource_name = 'DWIFSLPREPROC_DTIFIT'
    eddyqc_file = 'eddy/quad/qc.json'
