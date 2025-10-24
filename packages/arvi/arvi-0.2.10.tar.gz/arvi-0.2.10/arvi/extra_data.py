import os
from glob import glob
import json

from numpy import full
from .setup_logger import setup_logger

refs = {
    'HD86226': 'Teske et al. 2020 (AJ, 160, 2)'
}

def get_extra_data(star, instrument=None, path=None, verbose=True,
                   check_for_kms=True):
    from . import timeseries
    logger = setup_logger()
    if path is None:
        path = os.path.dirname(__file__)
        path = os.path.join(path, 'data', 'extra')
        metadata = json.load(open(os.path.join(path, 'metadata.json'), 'r'))
        # print(metadata)
    else:
        metadata = {}

    files = glob(os.path.join(path, star + '*.rdb'))
    files += glob(os.path.join(path, star.replace(' ', '') + '*.rdb'))
    files = [f for f in files if os.path.isfile(f)]
    files = [f for f in files if not f.endswith('_actin.rdb')]
    files = list(set(files))

    if len(files) == 0:
        raise FileNotFoundError

    def get_instruments(files):
        instruments = [os.path.basename(f).split('.')[0] for f in files]
        instruments = [i.split('_', maxsplit=1)[1] for i in instruments]
        return instruments
    
    instruments = get_instruments(files)

    if instrument is not None:
        if not any([instrument in i for i in instruments]):
            raise FileNotFoundError
        files = [f for f in files if instrument in f]
        instruments = get_instruments(files)

    if verbose:
        logger.info(f'loading extra data for {star}')

    units = len(files) * ['ms']
    reference = len(files) * [None]
    did_sa = len(files) * [False]

    for i, file in enumerate(files):
        file_basename = os.path.basename(file)
        if file_basename in metadata:
            if 'instrument' in metadata[file_basename]:
                instruments[i] = metadata[file_basename]['instrument']
            if 'units' in metadata[file_basename]:
                units[i] = metadata[file_basename]['units']
            if 'reference' in metadata[file_basename]:
                reference[i] = metadata[file_basename]['reference']
            if 'corrected_for_secular_acceleration' in metadata[file_basename]:
                did_sa[i] = metadata[file_basename]['corrected_for_secular_acceleration']

    with logger.contextualize(indent='  '):
        s = timeseries.RV.from_rdb(files[0], star=star, instrument=instruments[0], units=units[0])
        if check_for_kms and s.svrad.min() < 0.01:
            units[0] = 'kms'
            s = timeseries.RV.from_rdb(files[0], star=star, instrument=instruments[0], units=units[0])
        if verbose:
            logger.info(f'{instruments[0]:>12s} ├ ({s.N} observations)')

        for file, instrument, unit in zip(files[1:], instruments[1:], units[1:]):
            _s = timeseries.RV.from_rdb(file, star=star, instrument=instrument, units=unit)
            if check_for_kms and _s.svrad.min() < 0.01:
                unit = 'kms'
                _s = timeseries.RV.from_rdb(file, star=star, instrument=instrument, units=unit)
            if verbose:
                logger.info(f'{instrument:>12s} ├ ({_s.N} observations)')

            s = s + _s


    for i, (inst, ref, inst_did_sa) in enumerate(zip(s.instruments, reference, did_sa)):
        _s = getattr(s, inst)
        if ref is not None:
            _s.pub_reference = full(_s.N, ref)
        if inst_did_sa:
            _s._did_secular_acceleration = True

    return s
