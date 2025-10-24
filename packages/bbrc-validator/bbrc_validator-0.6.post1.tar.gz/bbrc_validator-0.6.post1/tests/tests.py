import unittest
from bbrc import validation as v
from bbrc.validation.utils import __find_all_checks__
import os.path as op
import bbrc
import logging as log
import tempfile
import sys
import json
from pyxnat import Interface


class RunThemAll(unittest.TestCase):

    def setUp(self):
        self.config_file = op.join(op.dirname(bbrc.__file__), '..', '.xnat.cfg')
        self.xnat_instance = Interface(config=self.config_file)

        fp = op.join(op.dirname(bbrc.__file__), 'data', 'scan_type_luts.json')
        lut_file = op.abspath(fp)
        with open(lut_file, 'r') as fp:
            self.lut = json.load(fp)['testenv']

    def __run_check__(self, c):
        check = c(self.lut, self.xnat_instance)

        passing = check.__run__(*check.passing)
        print((c.__name__, check.passing, passing.has_passed))
        failing = check.__run__(*check.failing)
        print((c.__name__, check.failing, failing.has_passed))
        return passing.has_passed and not failing.has_passed

    def test_run_all_checks(self):
        """ Runs all checks on their associated passing/failing sessions """
        checks = __find_all_checks__(v)
        log.info('Found checks %s' % checks)

        for c in checks:
            log.info('* Running %s' % c.__name__)
            res = self.__run_check__(c)
            log.info('-> %s' % str(res))
            if not res:
                log.error('%s FAILED' % c.__name__)
            self.assertTrue(res)

    def test_build_report(self):
        """ This test generates a validation report on a single sample session
        using `report` function from `ArchivingValidator`. """
        val = v.ArchivingValidator(self.lut, self.xnat_instance)
        experiment_id = 'BBRCDEV_E00380'
        fp = tempfile.mkstemp('.pdf')[1]
        val = v.ArchivingValidator(self.lut, self.xnat_instance)
        val.run(experiment_id)

        # STORE results as json file
        val.dump(fp.replace('.pdf', '.json'))

        # GENERATE human-readable reports
        val.report(fp)

    def test_mrsession_validate(self):
        """ This test runs the score collection function."""
        fp = tempfile.mkstemp('.pdf')[1]
        args = ['--config', self.config_file, '-e', 'BBRCDEV_E00368', '-o', fp]
        sys.path.append('./bin')
        from run_validator import create_parser, run_validator
        parser = create_parser()
        args = parser.parse_args(args)
        run_validator(args)

    def test_validation_scores(self):
        """ This test runs the score collection function."""
        fp = tempfile.mkstemp('.xlsx')[1]
        args = ['-v', '223d7fdc', '--config', self.config_file, '-o', fp]
        sys.path.append('./bin')
        from validation_scores import create_parser, validation_scores
        parser = create_parser()
        args = parser.parse_args(args)
        validation_scores(args)

    def test_configfiles(self):
        """ This tests two versions of config files (USER_PASSWORD and
        JSESSIONID)"""
        # First config_file with USER_PASSWORD
        x = Interface(config=self.config_file)
        y = Interface(server='https://devxnat.barcelonabeta.org',
                      verify=True,
                      anonymous=True)
        x._get_entry_point()
        jsession_id = dict([x._jsession.split('=')])

        y._http.cookies.update(jsession_id)


if __name__ == '__main__':
    unittest.main()
