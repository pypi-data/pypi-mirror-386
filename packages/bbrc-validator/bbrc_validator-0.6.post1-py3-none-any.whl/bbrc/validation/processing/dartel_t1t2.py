from ..test import ExperimentTest, Results
from . import spm


class HasCorrectItems(spm.HasCorrectItems):
    __doc__ = spm.HasCorrectItems.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'DARTEL_NORM2MNI_T1T2')

    passing = 'BBRCDEV_E02989',
    failing = 'BBRCDEV_E03056',
    resource_name = 'DARTEL_NORM2MNI_T1T2'
    expected_items = ['smwfixed_c1*.nii.gz',
                      'pyscript_dartelnorm2mni.m']


class HasCorrectSPMVersion(spm.HasCorrectSPMVersion):
    __doc__ = spm.HasCorrectSPMVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'DARTEL_NORM2MNI_T1T2')
    __doc__ = __doc__.replace('SPM12 Release 7219', 'SPM12 Release 7771')

    passing = 'BBRCDEV_E02989',
    failing = 'BBRCDEV_E03056',
    resource_name = 'DARTEL_NORM2MNI_T1T2'
    expected_version = 'SPM version: SPM12 Release: 7771'


class HasCorrectMatlabVersion(spm.HasCorrectMatlabVersion):
    __doc__ = spm.HasCorrectMatlabVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'DARTEL_NORM2MNI_T1T2')
    __doc__ = __doc__.replace('7.10.0.499', '9.7.0.1737446')
    __doc__ = __doc__.replace('R2010a', 'R2019b')

    passing = 'BBRCDEV_E02989',
    failing = 'BBRCDEV_E03056',
    resource_name = 'DARTEL_NORM2MNI_T1T2'
    expected_version = 'MATLAB Version: 9.7.0.1737446 (R2019b) Update 9'


class HasCorrectOSVersion(spm.HasCorrectOSVersion):
    __doc__ = spm.HasCorrectOSVersion.__doc__
    __doc__ = __doc__.replace('SPM12_SEGMENT', 'DARTEL_NORM2MNI_T1T2')

    passing = 'BBRCDEV_E02989',
    failing = 'BBRCDEV_E03056',
    resource_name = 'DARTEL_NORM2MNI_T1T2'
