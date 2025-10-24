from ..test import ExperimentTest, Results


class HasCorrectItems(ExperimentTest):
    """Passes if a `BAMOS_ARTERIAL` resource is found and this resource has the
    expected items according to the pipeline [specifications](
    https://gitlab.com/bbrc/xnat/docker-images/-/tree/master/bamos_arterial#outputs)."""

    passing = 'BBRCDEV_E04327',
    failing = 'BBRCDEV_E04328',
    resource_name = 'BAMOS_ARTERIAL'
    expected_items = ['t1_brain.nii.gz',
                      't1_brain_2_MNI_1InverseWarp.nii.gz',
                      't1_brain_2_MNI_InverseWarped.nii.gz',
                      't1_brain_2_MNI_Warped.nii.gz',
                      't1_brain_2_MNI_0GenericAffine.mat',
                      't1_brain_2_MNI_1Warp.nii.gz',
                      'ArterialAtlas_fixed.nii.gz',
                      'ArterialAtlas_2_t1_brain.nii.gz',
                      'bamos_arterial_stats.csv']

    def run(self, experiment_id):
        
        result = True

        e = self.xnat_instance.select.experiment(experiment_id)
        res = e.resource(self.resource_name)

        missing = []
        for item in self.expected_items:
            files = res.files(item).get()
            if not files:
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


class HasCorrectANTsVersion(ExperimentTest):
    """This test checks the version of ANTs used. Passes if `BAMOS_ARTERIAL`
    outputs were created using the expected version (`2.5.0.dev1-g592625b`)."""

    passing = 'BBRCDEV_E04327',
    failing = 'BBRCDEV_E04328',
    resource_name = 'BAMOS_ARTERIAL'
    expected_version = 'ANTs Version: 2.5.0.dev1-g592625b'

    def run(self, experiment_id):
        
        e = self.xnat_instance.select.experiment(experiment_id)
        log = e.resource(self.resource_name).file('LOGS/stdout.log')
        if not log.exists():
            msg = '{} log file not found.'.format(self.resource_name)
            return Results(False, data=[msg])

        log_data = self.xnat_instance.get(log.attributes()['URI']).text
        version = [line for line in log_data.splitlines()
                   if line.strip().startswith('ANTs Version')]
        if not version:
            return Results(False, data=['No ANTS version '
                                        'registered in the logs.'])
        if version[0] != self.expected_version:
            return Results(False, data=version)

        return Results(True, data=[])
    

class HasConsistentGlobalWMHVolume(ExperimentTest):
    """This test checks if the sum of regional WMH volumes quantified by
    `BAMOS_ARTERIAL` closely matches the global volume reported by `BAMOS`,
    ensuring the accuracy and reliability of the WMH volume calculations. Test
    passes if the absolute difference between the summed volumes and the global
    volume is < 0.01 mm3. Fails otherwise."""

    passing = 'BBRCDEV_E04327',
    failing = 'BBRCDEV_E04328',
    resource_name = 'BAMOS_ARTERIAL'
    threshold = 0.01

    def run(self, experiment_id):
        import os
        import tempfile
        import pandas as pd

        r = self.xnat_instance.select.experiment(experiment_id)\
            .resource('BAMOS')
        if not r.exists():
            msg = f'Resource BAMOS not found for experiment {experiment_id}.'
            return Results(False, data=[msg])
        global_vol = r.volume()

        r = self.xnat_instance.select.experiment(experiment_id)\
            .resource(self.resource_name)
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            return Results(False, data=[msg])
        
        f = r.file('bamos_arterial_stats.csv')
        if not f.exists():
            return Results(False,
                           data=['File bamos_arterial_stats.csv not found.'])
        fd, fp = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        f.get(fp)
        df = pd.read_csv(fp)
        diff = abs(global_vol - sum(df['volume']))
        if diff > self.threshold:
            return Results(False, data=['Global volume difference > '
                                        f'{self.threshold}'])
        
        return Results(True, data=[])


class ArterialTerritoriesSnapshot(ExperimentTest):
    """This test generates a snapshot of the WMH lesion arterial territories atlas
    registered to the native space by `BAMOS_ARTERIAL`. Snapshot consists of a FLAIR
    MRI background image with the atlas arterial territories overlaid. The test
    passes if the snapshot is created successfully, and fails otherwise. Test
    does not provide any information about the quality or accuracy of the arterial
    territories atlas itself."""

    passing = 'BBRCDEV_E04327',
    failing = 'BBRCDEV_E04328',
    resource_name = 'BAMOS_ARTERIAL'

    def run(self, experiment_id):
        import os
        import tempfile
        from nilearn import plotting

        if os.getenv('SKIP_SNAPSHOTS_TESTS') == 'True':
            return Results(experiment_id == self.passing[0],
                           data=['Skipping it. (SKIP_SNAPSHOTS_TESTS)'])
        
        e = self.xnat_instance.select.experiment(experiment_id)
        r = e.resource('BAMOS')
        if not r.exists():
            msg = 'BAMOS resource not found'
            return Results(False, data=[msg])
        
        fpaths = []
        fn = f'FLAIR_{e.label()}.nii.gz'
        f = r.file(fn)
        if not f.exists():
            return Results(False,
                           data=[f'File {fn} not found.'])
        fd, fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(fp)
        fpaths.append(fp)

        r = e.resource('BAMOS_ARTERIAL')
        if not r.exists():
            msg = f'{self.resource_name} resource not found'
            return Results(False, data=[msg])
        
        fn = 'ArterialAtlas_2_t1_brain.nii.gz'
        f = r.file(fn)
        if not f.exists():
            return Results(False,
                            data=[f'File {fn} not found.'])
        fd, fp = tempfile.mkstemp(suffix='.nii.gz')
        os.close(fd)
        f.get(fp)
        fpaths.append(fp)

        res = []
        for each in 'xyz':
            _, path = tempfile.mkstemp(suffix='.jpg')
            res.append(path)
            im = plotting.plot_anat(fpaths[0],
                                    black_bg=True,
                                    bg_img=None,
                                    display_mode=each,
                                    draw_cross=False,
                                    cut_coords=6)
            im.add_overlay(fpaths[1], vmin=0, vmax=34, 
                           cmap='nipy_spectral', alpha=0.3, colorbar=True)

            im.savefig(path)

        for item in fpaths:
            os.remove(item)
        return Results(True, res)

    def report(self):
        report = []
        if self.results.has_passed:
            for path in self.results.data:
                report.append('![snapshot]({})'.format(path))
        else:
            report = self.results.data

        return report