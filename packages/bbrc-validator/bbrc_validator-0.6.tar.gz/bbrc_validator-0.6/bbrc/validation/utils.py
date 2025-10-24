import pkgutil
import inspect
import logging as log
from .test import Test, ScanTest, ExperimentTest


def __get_modules__(m):
    modules = []
    prefix = m.__name__ + '.'
    log.info('prefix : %s' % prefix)
    for importer, modname, ispkg in pkgutil.iter_modules(m.__path__, prefix):
        module = __import__(modname, fromlist='dummy')
        if not ispkg:
            modules.append(module)
        else:
            modules.extend(__get_modules__(module))
    return modules


def __find_all_checks__(m):
    """ Browses bbrc.validation and looks for any class inheriting from Test"""
    modules = []
    classes = []
    modules = __get_modules__(m)
    forbidden_classes = [Test, ScanTest, ExperimentTest]
    for m in modules:
        for name, obj in inspect.getmembers(m):
            if inspect.isclass(obj) and Test in obj.mro() \
                    and obj not in forbidden_classes:
                classes.append(obj)
    return classes


def __md5__(fname):
    import hashlib
    hash_md5 = hashlib.md5()
    if fname.endswith('.pyc'):
        fname = fname[:-1]
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def __is_valid_scan__(xnat_instance, scan):
    """ Determines if a given scan is usable.
    Quality flag should be `usable` and ID should not start with 0.

    Args:
        scan: should be a dict eg. as returned by
                Interface.array.scans(columns=['xnat:imageScanData/quality',
                                               'xnat:imageScanData/type',
                                               'xsiType'])."""

    import fnmatch
    prefix = [i.split('/')[0] for i in scan.keys()
              if fnmatch.fnmatch(i, '*scandata/id')][0]
    if not prefix:
        raise Exception
    sc = scan['%s/id' % prefix]
    quality = scan['%s/quality' % prefix]
    datatype = xnat_instance.select.experiment(scan['ID']).scan(sc).datatype()
    columns = ['xnat:mrScanData', 'xnat:petScanData', 'xnat:ctScanData', 'xnat:otherDicomScanData']

    valid = (sc.isdigit() and not sc.startswith('0') and quality == 'usable'
             and datatype in columns)

    return valid


def __dicomdump__(xnat_instance, options, max_retries=5):
    """Calls the XNAT dicomdump service and returns a JSON object with the DICOM
    header attributes dumped.

    Args:
        options: should be a dict with 'format', 'src' and optionally 'field' keys
        max_retries: max number of attempts to get a non-empty dump result

    """
    import pandas as pd
    from io import StringIO

    # compose the URL for the XNAT dicomdump service
    uri = '/data/services/dicomdump'
    df = None
    for n in range(max_retries):
        ans = xnat_instance.get(uri, params=options).text
        df = pd.read_csv(StringIO(ans), sep=",", header=None)
        df.columns = df.iloc[0]
        df = df[1:]
        if not df.empty:
            break
        else:
            log.warning('Retrying dicomdump for {} time...'.format(n))
    return df.to_dict('records')


def collect_reports(xnat, validator_name='ArchivingValidator', project=None):
    import json
    from tqdm import tqdm

    url = '/data/experiments/%s/resources/BBRC_VALIDATOR/files/%s'
    if project:
        projects = [project]
    else:
        projects = list(xnat.select.projects().get())

    reports = {}
    experiments = []
    columns = ['ID', 'label', 'xsiType']

    log.info('Collecting experiments from %s project(s)' % len(projects))
    for p in tqdm(projects):
        expes = xnat.array.experiments(project_id=p, columns=columns).data
        experiments.extend(expes)

    from json.decoder import JSONDecodeError

    log.info('Collecting %s tests from experiments' % validator_name)
    for e in tqdm(experiments):
        try:
            eid = e['ID']
            label = e['label']
            uri = url % (eid, '%s_%s.json' % (validator_name, label))
            j = json.loads(xnat.get(uri).text)
            reports[eid] = j
        except KeyboardInterrupt:
            return reports
        except JSONDecodeError:
            pass

    return reports


def __read_first_dicom__(xnat, experiment_id, scan_id):
    """Reads the first DICOM file from a given scan resource.

    Returns:
        A pydicom.dataset.FileDataset object if a DICOM file is successfully
        read and parsed, otherwise None.
    """
    import os
    import tempfile
    import pydicom
    from pydicom.errors import InvalidDicomError

    e = xnat.select.experiment(experiment_id)
    r = e.scan(scan_id).resource('DICOM')
    if not r.exists():
        r = e.scan(scan_id).resource('secondary')
        if not r.exists():
            log.warning(f"No DICOM resource available (scan {scan_id})")
            return None
    
    f = r.files().first()
    if f is None:
        log.warning(f"No files found in the DICOM resource (scan {scan_id})")
        return None

    fh, fp = tempfile.mkstemp(suffix='.dcm')
    os.close(fh)
    f.get(fp)
    try:
        f.get(fp)
        ds = pydicom.dcmread(fp)
    except InvalidDicomError:
        os.remove(fp)
        log.warning(f"DICOM parsing error on file {f} (scan {scan_id})")
        return None

    os.remove(fp)
    return ds
