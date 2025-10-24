from . import ftm_quantification as ftm_quant


class HasCorrectItems(ftm_quant.HasCorrectItems):
    __doc__ = ftm_quant.HasCorrectItems.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',
    resource_name = 'FDG_QUANTIFICATION2'
    expected_items = ['static_pet.nii.gz',
                      'optimized_static_pet.nii.gz',
                      'static_pet_t1.nii.gz',
                      'c1mri_bin.nii.gz',
                      'c2mri_bin.nii.gz',
                      'c1mri.nii.gz',
                      'c2mri.nii.gz',
                      'c3mri.nii.gz',
                      'rp_pet.txt',
                      'quantification_results.csv',
                      'wstatic_pet_scaled_cgm.nii.gz',
                      'wstatic_pet_scaled_pons.nii.gz',
                      'wstatic_pet_scaled_wcbs.nii.gz',
                      'wstatic_pet_scaled_wc.nii.gz',
                      'wstatic_pet_scaled_wm.nii.gz',
                      'wstatic_pet_scaled_vermis.nii.gz',
                      'woptimized_static_pet_scaled_cgm.nii.gz',
                      'woptimized_static_pet_scaled_pons.nii.gz',
                      'woptimized_static_pet_scaled_wcbs.nii.gz',
                      'woptimized_static_pet_scaled_wc.nii.gz',
                      'woptimized_static_pet_scaled_wm.nii.gz',
                      'woptimized_static_pet_scaled_vermis.nii.gz',
                      'optimized_static_pet_scaled_cgm.nii.gz',
                      'optimized_static_pet_scaled_pons.nii.gz',
                      'optimized_static_pet_scaled_wcbs.nii.gz',
                      'optimized_static_pet_scaled_wc.nii.gz',
                      'optimized_static_pet_scaled_vermis.nii.gz',
                      'wresized_Hammers_mith_atlas_n30r83_SPM5.nii.gz',
                      'rwresized_Hammers_mith_atlas_n30r83_SPM5.nii.gz',
                      'rwresized_Hammers_mith_atlas_n30r83_SPM5_masked.nii.gz',
                      'rrwresized_Hammers_mith_atlas_n30r83_SPM5_masked.nii.gz',
                      'wAAL.nii.gz',
                      'rwAAL.nii.gz',
                      'rwAAL_masked.nii.gz',
                      'rrwAAL_masked.nii.gz',
                      'waparc+aseg_MNI152_T1_2mm.nii.gz',
                      'rwaparc+aseg_MNI152_T1_2mm.nii.gz',
                      'rwaparc+aseg_MNI152_T1_2mm_masked.nii.gz',
                      'rrwaparc+aseg_MNI152_T1_2mm_masked.nii.gz',
                      'wvoi_cerebellumvermis_2mm.nii.gz',
                      'rwvoi_cerebellumvermis_2mm.nii.gz',
                      'rgm_rois.nii.gz',
                      'gm_rois.nii.gz',
                      'pyscript_coregister.m',
                      'pyscript_coregister_icbm152.m',
                      'pyscript_newsegment.m',
                      'pyscript_normalize12.m',
                      'pyscript_normalize_atlas.m',
                      'pyscript_reslice_2_MRI.m',
                      'pyscript_realign_PET.m',
                      'pyscript_setorigin.m',
                      'pyscript_smooth.m',
                      'pyscript_average.m']


class QuantificationResultsShape(ftm_quant.QuantificationResultsShape):
    __doc__ = ftm_quant.QuantificationResultsShape.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')
    __doc__ = __doc__.replace('1840 rows', '2328 rows')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03060',
    resource_name = 'FDG_QUANTIFICATION2'
    csv_shape = (2328, 8)


class HasExpectedAtlasRegions(ftm_quant.HasExpectedAtlasRegions):
    __doc__ = ftm_quant.HasExpectedAtlasRegions.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03060',
    resource_name = 'FDG_QUANTIFICATION2'


class HasCorrectSPMVersion(ftm_quant.HasCorrectSPMVersion):
    __doc__ = ftm_quant.HasCorrectSPMVersion.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',
    resource_name = 'FDG_QUANTIFICATION2'


class HasCorrectMatlabVersion(ftm_quant.HasCorrectMatlabVersion):
    __doc__ = ftm_quant.HasCorrectMatlabVersion.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',
    resource_name = 'FDG_QUANTIFICATION2'


class HasCorrectOSVersion(ftm_quant.HasCorrectOSVersion):
    __doc__ = ftm_quant.HasCorrectOSVersion.__doc__
    __doc__ = __doc__.replace('FTM_QUANTIFICATION2', 'FDG_QUANTIFICATION2')

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',
    resource_name = 'FDG_QUANTIFICATION2'


class IsMaxTranslationConsistent(ftm_quant.IsMaxTranslationConsistent):
    __doc__ = ftm_quant.IsMaxTranslationConsistent.__doc__

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03060',
    resource_name = 'FDG_QUANTIFICATION2'


class MotionParameterSnapshot(ftm_quant.MotionParameterSnapshot):
    __doc__ = ftm_quant.MotionParameterSnapshot.__doc__

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',
    resource = 'FDG_QUANTIFICATION2'


class GMROISnapshot(ftm_quant.GMROISnapshot):
    __doc__ = ftm_quant.GMROISnapshot.__doc__

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',  
    resource = 'FDG_QUANTIFICATION2'


class PETSegmentationSnapshot(ftm_quant.PETSegmentationSnapshot):
    __doc__ = ftm_quant.PETSegmentationSnapshot.__doc__

    passing = 'BBRCDEV_E00745',
    failing = 'BBRCDEV_E03967',  
    resource = 'FDG_QUANTIFICATION2'
