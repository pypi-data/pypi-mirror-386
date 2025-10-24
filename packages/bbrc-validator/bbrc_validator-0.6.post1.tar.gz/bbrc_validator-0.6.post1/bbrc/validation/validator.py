import logging as log
from .test import ExperimentTest, ScanTest
from datetime import datetime
import bbrc


class Validator(object):
    def __init__(self, tests, lut, xnat_instance=None):
        self.version = bbrc.__version__
        self.tests = []
        self.lut = lut
        for each in tests:
            log.info('Adding %s' % each)
            self.tests.append(each(lut, xnat_instance))

    def run(self, experiment_id):
        if len(self.tests) == 0:
            raise Exception('No tests defined')
        for each in self.tests:
            log.info('Running %s' % each)
            if isinstance(each, ExperimentTest):
                each.results = each.__run__(experiment_id)

            elif isinstance(each, ScanTest):
                log.info('Running it over all scans %s' % experiment_id)
                each.results = each.run_over_experiment(experiment_id)

        self.experiment_id = experiment_id

    def dump(self, fp=None):
        import json
        res = dict()
        res['experiment_id'] = self.experiment_id
        res['version'] = self.version
        res['generated'] = '%s' % datetime.now().strftime("%Y-%m-%d, %H:%M")

        for each in self.tests:
            res[each.__class__.__name__] = each.results.to_dict()
        if fp is not None:
            with open(fp, 'w') as f:
                json.dump(res, f)

        return json.dumps(res)

    def report(self, fp):
        import bbrc
        import pdfkit
        import markdown as md
        import os.path as op

        if not hasattr(self, 'tests') or len(self.tests) == 0:
            raise Exception('No tests defined')

        # Headers
        bbrc_logo_fp = op.join(op.dirname(bbrc.__file__), 'data',
                               'barcelonabeta.png')

        x = self.tests[0].xnat_instance
        columns = ['ID', 'label', 'project', 'subject_ID', 'subject_label']
        labels = x.array.experiments(experiment_id=self.experiment_id,
                                     columns=columns).data[0]
        url = self.tests[0].xnat_instance._server + '/data/'\
            'experiments/%s?format=html' % self.experiment_id

        report = ['# BBRC %s Report' % self.__class__.__name__,
                  '<div style="width:180px; position: absolute; '
                  'right: 35px; top:35px; padding-right:10px;">'
                  '<img src=%s></img></div>' % bbrc_logo_fp,
                  'Version: %s  ' % self.version,
                  'Date & time: %s  ' % datetime.now().strftime("%Y-%m-%d, %H:%M"),
                  'Included tests:']
        report.extend('> %s' % each.__class__.__name__ for each in self.tests)
        report.extend(['## Validation Results',
                       'Project: `%s`' % labels['project'],
                       'Subject: `%s`' % labels['subject_label'],
                       'Experiment: `%s` (`%s`)' % (labels['label'],
                                                    self.experiment_id),
                       '&nbsp; [more](%s)' % url, ''])

        # Tests sections
        for each in self.tests:
            log.info('Building report: %s' % each)

            has_passed = {True: '<span style="color:green">PASSED</span>',
                          False: '<span style="color:red">**FAILED**</span>',
                          None: '<span style="color:orange">*SKIPPED*</span>'}[each.results.has_passed]
            elapsed_time = each.results.elapsedtime
            report.extend(['### %s ' % each.__class__.__name__,
                           '<i>%s</i>' % each.__doc__,
                           '',
                           'Returns: %s (completed in %s)' % (has_passed, elapsed_time)])
            r = each.report()
            assert(isinstance(r, list))

            report.extend(['> %s' % e for e in r])
            report.append('')

        # Save to pdf
        report = '\n'.join(report)
        log.info(report)
        html = md.markdown(report, extensions=['markdown.extensions.tables'])

        css = op.join(op.dirname(bbrc.__file__), 'data', 'github.css')
        options = {
            'page-size': 'Letter',
            'margin-top': '0.25in',
            'margin-right': '0.25in',
            'margin-bottom': '0.25in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }

        pdfkit.from_string(html, fp, options=options, css=css)


class ArchivingValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.sanity import data, image
        tests = [data.IsAccessionNumberUnique,
                 data.HasValidAccessionNumber,
                 data.HasDuplicatedSequences,
                 data.HasThumbnails,
                 data.HasNifti,
                 data.HasUncompressedPixelData,
                 data.IsClassicDICOM,
                 data.IsAcquisitionDateConsistent,
                 data.IsInsertDateConsistent,
                 data.HasValidDcm2niixVersion,
                 data.HasPhilipsPrivateTags,
                 data.HasRescaleParametersInScans,
                 data.HasBvecBvalInDWIScans,
                 data.HasCorrectSequences,
                 data.HasCorrectSequenceAttributes,
                 data.IsStudyDescriptionCorrect,
                 data.HasUsableT1,
                 data.IsFreeSurferRunnable,
                 data.HasPreferredT1,
                 data.IsPhilipsVersion519,
                 data.IsPhilipsVersion540,
                 data.IsPhilipsVersion561,
                 data.IsPhilipsVersion1110,
                 image.T1wHasValidGrayscaleRange,
                 data.HasUsableDWI,
                 data.HasUsableReversedDWI,
                 data.IsDtifitRunnable,
                 data.HasUsableT2,
                 data.IsT2T1CoregistrationRunnable,
                 data.HasUsableIR,
                 data.IsASHSRunnable,
                 data.HasUsableFLAIR,
                 data.IsBAMOSRunnable,
                 data.HasUsableASL,
                 data.HasUsableM0,
                 data.IsBASILRunnable,
                 data.HasUsableRS,
                 data.HasUsableSEap,
                 data.HasUsableSEpa,
                 data.IsFMRIPrepRunnable,
                 data.HasUsableSWI,
                 data.IsQSMxTRunnable,
                 data.HasUsableMRSHippo,
                 data.HasUsableMRSCun,
                 data.HasUsableMRSAng,
                 data.IsLCModelRunnable,
                 data.HasUsableCBF,
                 data.IsCBFQuantificationRunnable,
                 data.IsDWIFSLPreprocDtifitRunnable,
                 data.HasUsableMultiBLow,
                 data.HasUsableMultiBMid,
                 data.HasUsableMultiBHigh]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FreeSurferValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import freesurfer as fs
        tests = [fs.HasCorrectItems,
                 fs.HasCorrectFreeSurferVersion,
                 fs.HasCorrectOSVersion,
                 fs.IsT1OnlyHippocampalSegmentation,
                 fs.IsT1T2HippocampalSegmentation,
                 fs.IsT1IRHippocampalSegmentation,
                 fs.IsT2MultispectralHippoSegRunnable,
                 fs.IsIRMultispectralHippoSegRunnable,
                 fs.IsFreeSurferTimewiseConsistent,
                 fs.AreCAVolumesConsistent,
                 fs.ReconAllAsegSnapshot,
                 fs.ReconAllAparcSnapshot,
                 fs.HasAbnormalAsegFeatures]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FreeSurferHiresValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import freesurfer_hires as fs_hires
        tests = [fs_hires.HasCorrectItems,
                 fs_hires.HasCorrectFreeSurferVersion,
                 fs_hires.HasCorrectOSVersion,
                 fs_hires.IsT1OnlyHippocampalSegmentation,
                 # fs_hires.IsT1T2HippocampalSegmentation,
                 # fs_hires.IsT1IRHippocampalSegmentation,
                 fs_hires.IsT2MultispectralHippoSegRunnable,
                 fs_hires.IsIRMultispectralHippoSegRunnable,
                 fs_hires.IsFreeSurferTimewiseConsistent,
                 fs_hires.AreCAVolumesConsistent,
                 fs_hires.ReconAllAsegSnapshot,
                 fs_hires.ReconAllAparcSnapshot,
                 fs_hires.HasAbnormalAsegFeatures]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class SPM12SegmentValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import spm
        tests = [spm.HasCorrectNumberOfItems,
                 spm.HasCorrectItems,
                 spm.HasCorrectSPMVersion,
                 spm.HasCorrectMatlabVersion,
                 spm.HasCorrectOSVersion,
                 spm.SPM12SegmentSnapshot,
                 spm.HasNormalSPM12Volumes,
                 spm.SPM12SegmentExecutionTime]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class PetSessionValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.sanity import data, pet
        tests = [data.IsAccessionNumberUnique,
                 pet.IsSubjectIdCorrect,
                 data.HasDuplicatedSequences,
                 data.HasThumbnails,
                 data.HasNifti,
                 data.HasUncompressedPixelData,
                 data.IsAcquisitionDateConsistent,
                 data.IsInsertDateConsistent,
                 data.HasValidDcm2niixVersion,
                 data.HasCorrectSequences,
                 pet.IsTracerCorrect,
                 pet.IsSeriesDescriptionConsistent,
                 pet.IsScannerVersionCorrect,
                 pet.IsSubjectWeightConsistent,
                 pet.IsTracerDosageConsistent,
                 pet.HasUsableT1,
                 pet.IsCentiloidRunnable,
                 pet.IsFDGQuantificationRunnable,
                 pet.IsInjectionTimeConsistent]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DTIFITValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import dtifit
        tests = [dtifit.HasCorrectNumberOfItems,
                 dtifit.HasCorrectItems,
                 dtifit.HasCorrectMRtrix3Version,
                 dtifit.HasCorrectFSLVersion,
                 dtifit.DTIFITSnapshotFA,
                 dtifit.DTIFITSnapshotRGB,
                 dtifit.DTIFITSnapshotTOPUP,
                 dtifit.HasFewNegativeVoxelsInMD,
                 dtifit.HasAcceptableAverageSNR,
                 dtifit.HasAcceptableAverageCNR,
                 dtifit.HasAcceptableOutliersPercentage]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DWIFSLPreprocDTIFITValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import dwifslpreproc_dtifit
        tests = [dwifslpreproc_dtifit.HasCorrectNumberOfItems,
                 dwifslpreproc_dtifit.HasCorrectItems,
                 dwifslpreproc_dtifit.HasCorrectMRtrix3Version,
                 dwifslpreproc_dtifit.HasCorrectFSLVersion,
                 dwifslpreproc_dtifit.DTIFITSnapshotFA,
                 dwifslpreproc_dtifit.DTIFITSnapshotRGB,
                 dwifslpreproc_dtifit.DTIFITSnapshotTOPUP,
                 dwifslpreproc_dtifit.HasFewNegativeVoxelsInMD,
                 dwifslpreproc_dtifit.HasAcceptableAverageSNR,
                 dwifslpreproc_dtifit.HasAcceptableAverageCNR,
                 dwifslpreproc_dtifit.HasAcceptableOutliersPercentage]
        super(type(self), self).__init__(tests, lut, xnat_instance)        


class QMENTAValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import qmenta
        tests = [qmenta.HasCorrectItems,
                 qmenta.HasCorruptedLargeFiles,
                 qmenta.HasCorrectTabularData,
                 qmenta.HasCorrectStreamlines]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class ANTSValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import ants
        tests = [ants.HasCorrectItems,
                 ants.HasCorrectANTsVersion,
                 ants.ANTSSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class ASHSValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import ashs
        tests = [ashs.HasCorrectItems,
                 ashs.HasCorrectASHSVersion,
                 ashs.AreCAVolumesConsistent,
                 ashs.HasNormalSubfieldVolumes,
                 ashs.HasAllSubfields,
                 ashs.ASHSSnapshot,
                 ashs.HaveRawImagesValidIntensityRange]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class CAT12SegmentValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import cat
        tests = [cat.HasCorrectItems,
                 cat.HasCorrectCATVersion,
                 cat.HasCorrectSPMVersion,
                 cat.HasCorrectMatlabVersion,
                 cat.HasCorrectOSVersion,
                 cat.CAT12SegmentIQRScore,
                 cat.CAT12SegmentExecutionTime,
                 cat.CAT12SegmentSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class SPM12SegmentT1T2Validator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import spm_t1t2
        tests = [spm_t1t2.HasCorrectNumberOfItems,
                 spm_t1t2.HasCorrectItems,
                 spm_t1t2.HasCorrectSPMVersion,
                 spm_t1t2.HasCorrectMatlabVersion,
                 spm_t1t2.HasCorrectOSVersion,
                 spm_t1t2.SPM12SegmentSnapshot,
                 spm_t1t2.HasNormalSPM12Volumes,
                 spm_t1t2.SPM12SegmentExecutionTime,
                 spm_t1t2.SPM12SegmentMultichannelHoles,
                 spm_t1t2.SPM12SegmentMultichannelClusters]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FTMQuantificationValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import ftm_quantification as ftm_quant
        tests = [ftm_quant.HasCorrectItems,
                 ftm_quant.QuantificationResultsShape,
                 ftm_quant.HasExpectedAtlasRegions,
                 ftm_quant.HasCorrectSPMVersion,
                 ftm_quant.HasCorrectMatlabVersion,
                 ftm_quant.HasCorrectOSVersion,
                 ftm_quant.IsMaxTranslationConsistent,
                 ftm_quant.MotionParameterSnapshot,
                 ftm_quant.GMROISnapshot,
                 ftm_quant.PETSegmentationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FDGQuantificationValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import fdg_quantification as fdg_quant
        tests = [fdg_quant.HasCorrectItems,
                 fdg_quant.QuantificationResultsShape,
                 fdg_quant.HasExpectedAtlasRegions,
                 fdg_quant.HasCorrectSPMVersion,
                 fdg_quant.HasCorrectMatlabVersion,
                 fdg_quant.HasCorrectOSVersion,
                 fdg_quant.IsMaxTranslationConsistent,
                 fdg_quant.MotionParameterSnapshot,
                 fdg_quant.GMROISnapshot,
                 fdg_quant.PETSegmentationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class BAMOSValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import bamos
        tests = [bamos.HasCorrectItems,
                 bamos.FLAIRCoregistrationSnapshot,
                 bamos.LesionSegmentationSnapshot,
                 bamos.LobesSegmentationSnapshot,
                 bamos.LayersSegmentationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DONSURFValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import donsurf
        tests = [donsurf.HasCorrectItems,
                 donsurf.HasCorrectMRtrix3Version,
                 donsurf.HasCorrectFSLVersion,
                 donsurf.HasCorrectFreeSurferVersion,
                 donsurf.DWIRegistrationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class TauPetSessionValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.sanity import data, pet, tau_pet
        tests = [data.IsAccessionNumberUnique,
                 pet.IsSubjectIdCorrect,
                 data.HasDuplicatedSequences,
                 data.HasThumbnails,
                 data.HasNifti,
                 data.HasUncompressedPixelData,
                 data.IsAcquisitionDateConsistent,
                 data.IsInsertDateConsistent,
                 data.HasValidDcm2niixVersion,
                 data.HasCorrectSequences,
                 tau_pet.IsScannerVersionCorrect,
                 pet.IsSubjectWeightConsistent,
                 # pet.IsTracerDosageConsistent,
                 tau_pet.HasUsableT1,
                 tau_pet.IsInjectionTimeConsistent,
                 tau_pet.HasUsableReconAC4x5min,
                 tau_pet.IsCenTauRzRunnable,
                 tau_pet.IsAlfaCohort,
                 tau_pet.IsBetaCohort]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FreeSurfer7Validator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import freesurfer7
        tests = [freesurfer7.HasCorrectItems,
                 freesurfer7.HasCorrectFreeSurferVersion,
                 freesurfer7.HasCorrectOSVersion,
                 freesurfer7.IsT1OnlyHippocampalSegmentation,
                 # freesurfer7.IsT1T2HippocampalSegmentation,
                 # freesurfer7.IsT1IRHippocampalSegmentation,
                 freesurfer7.IsT2MultispectralHippoSegRunnable,
                 freesurfer7.IsIRMultispectralHippoSegRunnable,
                 freesurfer7.IsFreeSurferTimewiseConsistent,
                 freesurfer7.AreCAVolumesConsistent,
                 freesurfer7.ReconAllAsegSnapshot,
                 freesurfer7.ReconAllAparcSnapshot]
                 # freesurfer7.HasAbnormalAsegFeatures]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class BASILValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import basil
        tests = [basil.HasCorrectNumberOfItems,
                 basil.HasCorrectItems,
                 basil.HasCorrectFSLVersion,
                 basil.HasCorrectOxfordASLVersion,
                 basil.IsT1Session1,
                 basil.IsT1Session3,
                 basil.IsGMPerfusionMeanConsistent,
                 basil.IsWMPerfusionMeanConsistent,
                 basil.PerfusionSnapshot,
                 basil.HasNormalFSLANATVolumes,
                 basil.FSLANATSegmentationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FreeSurfer7ExtrasValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import freesurfer7_extras as fs7_extras
        tests = [fs7_extras.HasCorrectItems,
                 fs7_extras.HasCorrectFreeSurferVersion,
                 fs7_extras.HasCorrectOSVersion,
                 fs7_extras.HasExpectedHypothalamicSegmentationResolution,
                 fs7_extras.HasAllBrainstemRegions,
                 fs7_extras.HasNormalBrainstemVolumes,
                 fs7_extras.AreBrainstemVolumesConsistent,
                 fs7_extras.HasAllHypothalamicRegions,
                 fs7_extras.HasNormalHypothalamicVolumes,
                 fs7_extras.HasAllThalamicNucleiRegions,
                 fs7_extras.HasNormalThalamicNucleiVolumes,
                 fs7_extras.BrainstemSnapshot,
                 fs7_extras.HypothalamusSnapshot,
                 fs7_extras.ThalamusNucleiSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DickersonValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import dickerson
        tests = [dickerson.HasCorrectItems,
                 dickerson.HasCorrectFreeSurferVersion]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class QSMxTValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import qsmxt
        tests = [qsmxt.HasCorrectItems,
                 qsmxt.HasCorrectQSMxTVersion,
                 qsmxt.IsBasalGangliaMeanQSMConsistent,
                 qsmxt.IsT1Session1,
                 qsmxt.IsT1Session3,
                 qsmxt.HasExpectedAsegStructures]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DartelNorm2MNIValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import dartel
        tests = [dartel.HasCorrectItems,
                 dartel.HasCorrectSPMVersion,
                 dartel.HasCorrectMatlabVersion,
                 dartel.HasCorrectOSVersion]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class DartelNorm2MNIT1T2Validator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import dartel_t1t2
        tests = [dartel_t1t2.HasCorrectItems,
                 dartel_t1t2.HasCorrectSPMVersion,
                 dartel_t1t2.HasCorrectMatlabVersion,
                 dartel_t1t2.HasCorrectOSVersion]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class FMRIPrepValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import fmriprep
        tests = [fmriprep.HasCorrectItems,
                 fmriprep.HasCorrectFMRIPrepVersion,
                 fmriprep.HasCorrectHeuDiConvVersion,
                 fmriprep.HasValidDcm2niixVersion,
                 fmriprep.IsICANumberOfSignalComponentsConsistent,
                 fmriprep.HasFewMotionOutlierVolumes]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class MRtrix3Validator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import mrtrix3
        tests = [mrtrix3.HasCorrectItems,
                 mrtrix3.HasCorrectMRtrixVersion,
                 mrtrix3.FiveTTSegmentationSnapshot,
                 mrtrix3.T1toDWICoregistrationSnapshot,
                 mrtrix3.IsRegionalStructuralConnectivityConsistent,
                 mrtrix3.StructuralConnectivityMatrixSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class XCPDValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import xcp_d
        tests = [xcp_d.HasCorrectItems,
                 xcp_d.HasCorrectXCPDVersion,
                 xcp_d.HasCorrectFMRIPrepVersion,
                 xcp_d.IsNumberOfCensoredVolumesConsistent,
                 xcp_d.HasCensoredVolumesAtEndsOfData,
                 xcp_d.IsMeanFramewiseDisplacementConsistent,
                 xcp_d.IsSubjectMotionRemovalConsistent,
                 xcp_d.IsfMRIToT1wCoregistrationQualityAcceptable,
                 xcp_d.IsNormalizationToTemplateQualityAcceptable,
                 xcp_d.IsRegionalFunctionalConnectivityConsistent,
                 xcp_d.HasFewExcludedLowCoverageRegions,
                 xcp_d.FunctionalConnectivityMatrixSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class LCModelValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import lcmodel
        tests = [lcmodel.HasCorrectItems,
                 lcmodel.HasCorrectLCModelVersion,
                 lcmodel.HasCorrectSPMVersion,
                 lcmodel.HasCorrectMatlabVersion,
                 lcmodel.HasCorrectOSVersion,
                 lcmodel.HasCorrectSNR,
                 lcmodel.HasCorrectFWHM,
                 lcmodel.HasCorrectMetaboliteConcentrationSD,
                 lcmodel.HaveMasksConsistentTissueProbabilities,
                 lcmodel.AngularMaskSnapshot,
                 lcmodel.HippocampusMaskSnapshot,
                 lcmodel.CuneusMaskSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class ASL3DQuantificationValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import asl3d
        tests = [asl3d.HasCorrectItems,
                 asl3d.HasCorrectFSLVersion,
                 asl3d.HasCorrectASLRegVersion,
                 asl3d.IsT1Session1,
                 asl3d.IsT1Session3,
                 asl3d.IsGMPerfusionMeanConsistent,
                 asl3d.IsWMPerfusionMeanConsistent,
                 asl3d.PerfusionSnapshot,
                 asl3d.HasNormalFSLANATVolumes,
                 asl3d.FSLANATSegmentationSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class ALPSValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import alps
        tests = [alps.HasCorrectItems,
                 alps.HasCorrectMRtrix3Version,
                 alps.HasCorrectFSLVersion,
                 alps.FAtoT1RegistrationSnapshot,
                 alps.FAtoMNIRegistrationSnapshot,
                 alps.IsALPSIndexConsistent]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class BAMOSArterialValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import bamos_arterial
        tests = [bamos_arterial.HasCorrectItems,
                 bamos_arterial.HasCorrectANTsVersion,
                 bamos_arterial.HasConsistentGlobalWMHVolume,
                 bamos_arterial.ArterialTerritoriesSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class CenTaurZValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import centaurz
        tests = [centaurz.HasCorrectItems,
                 centaurz.QuantificationResultsShape,
                 centaurz.HasCorrectSPMVersion,
                 centaurz.HasCorrectMatlabVersion,
                 centaurz.IsMaxTranslationConsistent,
                 centaurz.MotionParameterSnapshot,
                 centaurz.UniversalMaskSnapshot,
                 centaurz.CerebellarGrayMatterSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)


class PYMENTValidator(Validator):
    def __init__(self, lut, xnat_instance):
        from bbrc.validation.processing import pyment
        tests = [pyment.HasCorrectItems,
                 pyment.HasCorrectFSLVersion,
                 pyment.PYMENTSnapshot,
                 pyment.GRADCAMSnapshot]
        super(type(self), self).__init__(tests, lut, xnat_instance)