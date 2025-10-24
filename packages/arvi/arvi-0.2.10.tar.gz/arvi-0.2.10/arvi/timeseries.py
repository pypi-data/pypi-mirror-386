import os
from dataclasses import dataclass, field
from typing import Union
from functools import partial, partialmethod
from glob import glob
import warnings
from copy import deepcopy
from datetime import datetime, timezone

import numpy as np

from .setup_logger import setup_logger
logger = setup_logger()

from .config import config
from .translations import translate
from .dace_wrapper import do_download_filetype, do_symlink_filetype, get_observations, get_arrays
from .simbad_wrapper import simbad
from .gaia_wrapper import gaia
from .exofop_wrapper import exofop
from .extra_data import get_extra_data
from .stats import wmean, wrms
from .binning import bin_ccf_mask, binRV
from .HZ import getHZ_period
from .instrument_specific import ISSUES
from .reports import REPORTS
from .utils import sanitize_path, strtobool, there_is_internet, timer, chdir
from .setup_logger import setup_logger
logger = setup_logger()

# units = lazy_import('astropy.units')
# units = lazy.load('astropy.units')
from astropy import units

class ExtraFields:
    @property
    def fields(self):
        return list(self.__dict__.keys())


@dataclass(order=False)
class RV(ISSUES, REPORTS):
    """
    A class holding RV observations

    Args:
        star (str):
            Name of the star
        instrument (str, list):
            Name of the instrument or list of instruments
        verbose (bool):
            Print logging messages
        do_maxerror:
            Mask points based on a maximum RV uncertainty
        do_secular_acceleration:
            Apply secular acceleration correction. This only applies
            to certain instruments.
        do_sigma_clip (bool):
            Apply sigma clipping on the RVs
        do_adjust_means (bool):
            Subtract individual weighted mean RV from each instrument
        only_latest_pipeline (bool):
            Select only the latest pipeline from each instrument
        load_extra_data (bool):
        check_drs_qc (bool):
            Mask points based on DRS quality control flags
        user (str):
            User name for DACE queries (should be a section in `~/.dacerc` file)

    Examples:
        >>> s = RV('Proxima')
        >>> s = RV('HD10180', instrument='HARPS')

    """
    # Attributes:
    #     star (str):
    #         The name of the star
    #     N (int):
    #         Total number of observations
    #     NN (dict):
    #         Number of observations per instrument
    #     instruments (list):
    #         List of instruments for which there are RVs. Each instrument is also
    #         stored as an attribute (e.g. `self.CORALIE98` or `self.HARPS`)
    #     simbad (simbad):
    #         Information on the target from Simbad
    #     gaia (gaia):
    #         Information on the target from Gaia DR3
    star: str
    instrument: Union[str, list] = field(init=True, repr=False, default=None)
    verbose: bool = field(init=True, repr=False, default=True)
    do_maxerror: float = field(init=True, repr=False, default=None)
    do_secular_acceleration: bool = field(init=True, repr=False, default=True)
    do_sigma_clip: bool = field(init=True, repr=False, default=False)
    do_adjust_means: bool = field(init=True, repr=False, default=True)
    only_latest_pipeline: bool = field(init=True, repr=False, default=True)
    load_extra_data: Union[bool, str] = field(init=True, repr=False, default=False)
    check_drs_qc: bool = field(init=True, repr=False, default=True)
    check_sophie_archive: bool = field(init=True, repr=False, default=False)
    user: Union[str, None] = field(init=True, repr=False, default=None)
    #
    units = 'm/s'
    _child: bool = field(init=True, repr=False, default=False)
    #
    _did_secular_acceleration : bool = field(init=False, repr=False, default=False)
    _did_sigma_clip           : bool = field(init=False, repr=False, default=False)
    _did_adjust_means         : bool = field(init=False, repr=False, default=False)
    _did_simbad_query         : bool = field(init=False, repr=False, default=False)
    _did_gaia_query           : bool = field(init=False, repr=False, default=False)
    _did_toi_query            : bool = field(init=False, repr=False, default=False)
    _raise_on_error  : bool = field(init=True, repr=False, default=True)
    __masked_numbers : bool = field(init=False, repr=False, default=False)
    #
    _simbad = None
    _gaia = None
    _toi = None

    def __repr__(self):
        ni = len(self.instruments)
        if self.N == 0:
            return f"RV(star='{self.star}', N=0)"

        if self._child:
            i = ''
        else:
            i = f', {ni} instrument' + ('s' if ni > 1 else '')

        if self.time.size == self.mtime.size:
            return f"RV(star='{self.star}', N={self.N}{i})"
        else:
            nmasked = self.N - self.mtime.size
            return f"RV(star='{self.star}', N={self.N}, masked={nmasked}{i})"

    @property
    def simbad(self):
        if self._simbad is not None:
            return self._simbad

        if self._child:
            return None

        if self._did_simbad_query:
            return None

        if self.verbose:
            logger.info('querying Simbad...')

        # complicated way to query Simbad with self.__star__ or, if that
        # fails, try after removing a trailing 'A'
        for target in set([self.__star__, self.__star__.replace('A', '')]):
            try:
                self._simbad = simbad(target)
                break
            except ValueError:
                continue
        else:
            if self.verbose:
                logger.error(f'simbad query for {self.__star__} failed')

        self._did_simbad_query = True
        return self._simbad

    @property
    def gaia(self):
        if self._gaia is not None:
            return self._gaia

        if self._child:
            return None

        if self._did_gaia_query:
            return None

        if self.verbose:
            logger.info('querying Gaia...')

        # complicated way to query Gaia with self.__star__ or, if that fails,
        # try after removing a trailing 'A'
        for target in set([self.__star__, self.__star__.replace('A', '')]):
            try:
                self._gaia = gaia(target)
                break
            except ValueError:
                continue
        else:
            if self.verbose:
                logger.error(f'Gaia query for {self.__star__} failed')

        self._did_gaia_query = True
        return self._gaia

    @property
    def toi(self):
        if self._toi is not None:
            return self._toi

        if 'TOI' not in self.__star__ or 'TIC' not in self.__star__ or self._child or self._did_toi_query:
            return None

        if self.verbose:
            logger.info('querying ExoFOP...')

        try:
            self._toi = exofop(self.__star__)
        except ValueError:
            if self.verbose:
                logger.error(f'ExoFOP query for {self.__star__} failed')

        self._did_toi_query = True
        return self._toi

    def __post_init_special_sun(self):
        import pickle
        from .extra_data import get_sun_data
        path = get_sun_data(download=not self._child)
        self.dace_result = pickle.load(open(path, 'rb'))


    def __post_init__(self):
        self.__star__ = translate(self.star)

        if self.star.lower() == 'sun':
            self.__post_init_special_sun()
            self.do_secular_acceleration = False
            self.units = 'km/s'

        else:
            if not self._child:
                if config.check_internet and not there_is_internet():
                    raise ConnectionError('There is no internet connection?')

                # make Simbad and Gaia queries in parallel
                import concurrent.futures
                with timer('simbad and gaia queries'):
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        executor.map(self.__getattribute__, ('simbad', 'gaia', 'toi'))

                # with timer('simbad query'):
                #     self.simbad
                # with timer('gaia query'):
                #     self.gaia

                # query DACE
                if self.verbose:
                    logger.info(f'querying DACE for {self.__star__}...')
                try:
                    if hasattr(self, 'simbad') and self.simbad is not None:
                        mid = self.simbad.main_id
                    else:
                        mid = None

                    with timer('dace query'):
                        self.dace_result = get_observations(self.__star__, self.instrument,
                                                            user=self.user, main_id=mid, verbose=self.verbose)
                except ValueError as e:
                    # querying DACE failed, should we raise an error?
                    if self._raise_on_error:
                        raise e
                    else:
                        self.time = np.array([])
                        self.instruments = []
                        self.units = ''
                        return

                # store the date of the last DACE query
                time_stamp = datetime.now(timezone.utc)  #.isoformat().split('.')[0]
                self._last_dace_query = time_stamp

        _replacements = (('-', '_'), ('.', '_'), (' ', '_'), ('__', '_'))
        def do_replacements(s):
            for a, b in _replacements:
                s = s.replace(a, b)
            return s

        # build children
        if not self._child:
            arrays = get_arrays(self.dace_result,
                                latest_pipeline=self.only_latest_pipeline,
                                verbose=self.verbose)

            for (inst, pipe, mode), data in arrays:
                child = RV.from_dace_data(self.star, inst, pipe, mode, data, _child=True,
                                          check_drs_qc=self.check_drs_qc, verbose=self.verbose)
                inst = do_replacements(inst)
                pipe = do_replacements(pipe)
                if self.only_latest_pipeline:
                    # save as self.INST
                    setattr(self, inst, child)
                else:
                    # save as self.INST_PIPE
                    setattr(self, f'{inst}_{pipe}', child)

        # build joint arrays
        if not self._child:
            #! sorted?
            if self.only_latest_pipeline:
                self.instruments = [
                    do_replacements(inst)
                    for (inst, _, _), _ in arrays
                ]
            else:
                self.instruments = [
                    do_replacements(inst) + '_' + do_replacements(pipe)
                    for (inst, pipe, _), _ in arrays
                ]
            # all other quantities
            self._build_arrays()

            if self.load_extra_data:
                if isinstance(self.load_extra_data, str):
                    path = self.load_extra_data
                else:
                    path = None
                try:
                    self.__add__(get_extra_data(self.star, instrument=self.instrument,
                                                path=path, verbose=self.verbose),
                                 inplace=True)

                except FileNotFoundError:
                    pass

                # all other quantities
                self._build_arrays()

                # self.actin = get_actin_data(self, verbose=self.verbose)


        # check for SOPHIE observations
        cond = not self._child
        cond = cond and self.instrument is None
        cond = cond and self.check_sophie_archive
        if cond:
            try:
                from arvi.sophie_wrapper import query_sophie_archive
                self.__add__(query_sophie_archive(self.star, verbose=self.verbose),
                             inplace=True)
            except Exception as e:
                print(e)

        # do clip_maxerror, secular_acceleration, sigmaclip, adjust_means
        if not self._child:
            if self.do_maxerror:
                self.clip_maxerror(self.do_maxerror)

            if self.do_secular_acceleration:
                self.secular_acceleration()

            if self.do_sigma_clip:
                self.sigmaclip()

            if self.do_adjust_means:
                self.adjust_means()

        _star_no_space = self.star.replace(' ', '')
        _directory = sanitize_path(_star_no_space)
        self._download_directory = f'{_directory}_downloads'

    def __add__(self, other, inplace=False):
        # if not isinstance(other, self.__class__):
        #     raise TypeError('unsupported operand type(s) for +: '
        #                     f"'{self.__class__.__name__}' and '{other.__class__.__name__}'")
        if other is None:
            if inplace:
                return
            else:
                return deepcopy(self)

        if np.isin(self.instruments, other.instruments).any():
            logger.error('the two objects share instrument(s), cannot add them')
            return

        if self._did_adjust_means or other._did_adjust_means:
            self.adjust_means()
            other.adjust_means()

        if inplace:
            #? could it be as simple as this?
            for i in other.instruments:
                self.instruments.append(i)
                setattr(self, i, getattr(other, i))
            self._build_arrays()
        else:
            # make a copy of ourselves
            new_self = deepcopy(self)
            #? could it be as simple as this?
            for i in other.instruments:
                new_self.instruments.append(i)
                setattr(new_self, i, getattr(other, i))
            new_self._build_arrays()
            return new_self

    def __iter__(self):
        for inst in self.instruments:
            yield getattr(self, inst)

    @property
    def _masked_numbers(self):
        return self.__masked_numbers

    @_masked_numbers.setter
    def _masked_numbers(self, value):
        self.__masked_numbers = value
        if not self._child:
            for s in self:
                s._masked_numbers = value

    def reload(self):
        self._did_secular_acceleration = False
        self._did_sigma_clip = False
        self._did_adjust_means = False
        self._did_correct_berv = False
        self.__post_init__()

    def snapshot(self, directory=None, delete_others=False, compress=False):
        if compress:
            try:
                import compress_pickle as pickle
            except ImportError:
                logger.warning('compress_pickle not installed, not compressing')
                import pickle
                compress = False
        else:
            import pickle
        import re
        from datetime import datetime

        ts = datetime.now().timestamp()
        star_name = self.star.replace(' ', '')
        file = f'{star_name}_{ts}.pkl'

        server = None
        if directory is None:
            directory = '.'
        else:
            if ':' in directory:
                server, directory = directory.split(':')
                delete_others = False
            else:
                os.makedirs(directory, exist_ok=True)

        metadata = {
            'star': self.star,
            'timestamp': ts,
            'description': 'arvi snapshot'
        }


        if server:
            import posixpath
            from .utils import server_sftp, server_file
            with server_sftp(server=server) as sftp:
                try:
                    sftp.chdir(directory)
                except FileNotFoundError:
                    sftp.mkdir(directory)
                finally:
                    sftp.chdir(directory)
                with sftp.open(file, 'wb') as f:
                    print('saving snapshot to server...', end='', flush=True)
                    pickle.dump((self, metadata), f, protocol=0)
                    print('done')
            file = posixpath.join(directory, file)
        else:
            if delete_others:
                other_pkls = [
                    f for f in os.listdir(directory)
                    if re.search(fr'{star_name}_\d+.\d+.pkl', f)
                ]
                for pkl in other_pkls:
                    os.remove(os.path.join(directory, pkl))

            file = os.path.join(directory, file)

            if compress:
                file += '.gz'

            with open(file, 'wb') as f:
                pickle.dump((self, metadata), f)

        if self.verbose:
            logger.info(f'saved snapshot to {file}')

        return file

    @property
    def N(self) -> int:
        """Total number of observations"""
        if self._masked_numbers:
            return self.mtime.size
        return self.time.size

    @property
    def NN(self):
        """ Total number of observations per instrument """
        if self._child:
            return {self.instruments[0]: self.N}
        return {inst: getattr(self, inst).N for inst in self.instruments}

    @property
    def N_nights(self) -> int:
        """ Number of individual nights """
        def get_nights(t):
            return binRV(t, None, None, binning_bins=True).size - 1

        if self._masked_numbers:
            if self._child:
                return get_nights(self.mtime)
            else:
                return sum([get_nights(s.mtime) for s in self])
        else:
            if self._child:
                return get_nights(self.time)
            else:
                return sum([get_nights(s.time) for s in self])
        # return binRV(_t, None, None, binning_bins=True).size - 1
        # return sum(list(self.NN.values()))

    @property
    def NN_nights(self):
        return {inst: getattr(self, inst).N_nights for inst in self.instruments}

    @property
    def _NN_as_table(self) -> str:
        table = ''
        table += ' | '.join(self.instruments) + '\n'
        table += ' | '.join([i*'-' for i in map(len, self.instruments)]) + '\n'
        table += ' | '.join(map(str, self.NN.values())) + '\n'
        return table

    @property
    def point(self):
        return [(t.round(4), v.round(4), sv.round(4)) for t, v, sv in zip(self.time, self.vrad, self.svrad)]

    @property
    def mtime(self) -> np.ndarray:
        """ Masked array of times """
        return self.time[self.mask]

    @property
    def mvrad(self) -> np.ndarray:
        """ Masked array of radial velocities """
        return self.vrad[self.mask]

    @property
    def msvrad(self) -> np.ndarray:
        """ Masked array of radial velocity uncertainties """
        return self.svrad[self.mask]

    @property
    def instrument_array(self):
        return np.concatenate([[i] * n for i, n in self.NN.items()])

    def _instrument_mask(self, instrument):
        if isinstance(instrument, str):
            return np.char.find(self.instrument_array, instrument) == 0
        elif isinstance(instrument, (list, tuple, np.ndarray)):
            m = np.full_like(self.time, False, dtype=bool)
            for i in instrument:
                m |= np.char.find(self.instrument_array, i) == 0
            return m

    @property
    def rms(self) -> float:
        """ Weighted rms of the (masked) radial velocities """
        if self.mask.sum() == 0:  # only one point
            return np.nan
        else:
            return wrms(self.vrad[self.mask], self.svrad[self.mask])

    @property
    def sigma(self):
        """ Average radial velocity uncertainty """
        if self.mask.sum() == 0:  # only one point
            return np.nan
        else:
            return self.svrad[self.mask].mean()

    error = sigma  # alias!

    @property
    def _time_sorter(self):
        return np.argsort(self.time)

    @property
    def _mtime_sorter(self):
        return np.argsort(self.mtime)

    @property
    def timespan(self):
        """ Total time span of the (masked) observations """
        return np.ptp(self.mtime)

    def _index_from_instrument_index(self, index, instrument):
        ind = np.where(self.instrument_array == instrument)[0]
        return ind[getattr(self, instrument).mask][index]

    # @property
    def _tt(self, f=20) -> np.ndarray:
        return np.linspace(self.mtime.min(), self.mtime.max(), f*self.N)

    @classmethod
    def from_dace_data(cls, star, inst, pipe, mode, data, **kwargs):
        verbose = kwargs.pop('verbose', False)
        check_drs_qc = kwargs.pop('check_drs_qc', True)
        s = cls(star, **kwargs)
        #
        ind = np.argsort(data['rjd'])
        # time, RVs, uncertainties
        s.time = data['rjd'][ind]
        s.vrad = data['rv'][ind]
        s.svrad = data['rv_err'][ind]

        # mask
        s.mask = np.full_like(s.time, True, dtype=bool)
        s.mask[np.isnan(s.svrad)] = False
        ## be careful with bogus values
        s.mask[s.svrad < 0] = False


        # all other quantities
        s._quantities = []
        for arr in data.keys():
            if arr not in ('rjd', 'rv', 'rv_err'):
                if arr == 'mask':
                    # change name mask -> ccf_mask
                    setattr(s, 'ccf_mask', data[arr][ind])
                    s._quantities.append('ccf_mask')
                else:
                    # be careful with bogus values in rhk and rhk_err
                    # --> not just in rhk and rhk_err...
                    if data[arr].dtype == float and (bad := data[arr] == -99999).any():
                        data[arr][bad] = np.nan
                    if data[arr].dtype == float and (bad := data[arr] == -99).any():
                        data[arr][bad] = np.nan
                    setattr(s, arr, data[arr][ind])
                    s._quantities.append(arr)

        s._quantities = np.array(s._quantities)

        # mask out drs_qc = False
        if check_drs_qc and not s.drs_qc.all():
            n = (~s.drs_qc).sum()
            if verbose:
                logger.warning(f'masking {n} points where DRS QC failed for {inst}')
            s.mask &= s.drs_qc

        s.instruments = [inst]
        s.pipelines = [pipe]
        s.modes = [str(mode)]

        return s

    @classmethod
    def from_arrays(cls, star, time, vrad, svrad, inst, **kwargs):
        s = cls(star, _child=True)
        time, vrad, svrad = map(np.atleast_1d, (time, vrad, svrad))

        if time.size != vrad.size:
            logger.error(f'wrong dimensions: time({time.size}) != vrad({vrad.size})')
            raise ValueError from None
        if time.size != svrad.size:
            logger.error(f'wrong dimensions: time({time.size}) != svrad({svrad.size})')
            raise ValueError from None

        # time, RVs, uncertainties
        s.time = time
        s.vrad = vrad
        s.svrad = svrad

        s.mask = kwargs.pop('mask', np.full_like(s.time, True, dtype=bool))
        s.units = kwargs.pop('units', 'm/s')

        for k, v in kwargs.items():
            setattr(s, k, np.atleast_1d(v))

        s.instruments = [inst]
        s._quantities = np.array(list(kwargs.keys()))

        return s

    @classmethod
    def from_snapshot(cls, file=None, star=None, verbose=True):
        import pickle
        from datetime import datetime
        if star is None:
            assert file.endswith(('.pkl', '.pkl.gz')), 'expected a .pkl file'
            basefile = os.path.basename(file)
            star, timestamp = basefile.replace('.pkl.gz', '').replace('.pkl', '').split('_')
        else:
            try:
                file = sorted(glob(f'{star}_*.*.pkl*'))[-1]
            except IndexError:
                raise ValueError(f'cannot find any file matching {star}_*.pkl')
            star, timestamp = file.replace('.pkl.gz', '').replace('.pkl', '').split('_')

        dt = datetime.fromtimestamp(float(timestamp))
        if verbose:
            logger.info(f'reading snapshot of {star} from {dt}')

        with open(file, 'rb') as f:
            if file.endswith('.gz'):
                import compress_pickle as pickle
            s = pickle.load(f)

        if isinstance(s, tuple) and len(s) == 2:
            s, _metadata = s

        s._snapshot = file
        return s

    @classmethod
    def from_rdb(cls, files, star=None, instrument=None, instrument_suffix=None,
                 units='ms', header_skip=2, **kwargs):
        """ Create an RV object from an rdb file or a list of rdb files

        Args:
            files (str, list):
                File name, file object, or list of file names
            star (str, optional):
                Name of the star. If None, try to infer it from file name
            instrument (str, list, optional):
                Name of the instrument(s). If None, try to infer it from file name
            units (str, optional):
                Units of the radial velocities. Defaults to 'ms'.
            header_skip (int, optional):
                Number of lines to skip in the header. Defaults to 2.

        Examples:
            >>> s = RV.from_rdb('star_HARPS.rdb')
        """
        from glob import glob
        from os.path import splitext, basename

        verbose = kwargs.pop('verbose', True)

        file_object = False

        if isinstance(files, str):
            if '*' in files:
                files = glob(files)
            else:
                files = [files]
        elif isinstance(files, list):
            pass
        else:
            file_object = hasattr(files, 'read')
            files = [files]

        if len(files) == 0:
            if verbose:
                logger.error('from_rdb: no files found')
            return

        def get_star_name(file):
            return splitext(basename(file))[0].split('_')[0].replace('-', '_')
        
        def get_instrument(file):
            return splitext(basename(file))[0].split('_')[1]

        if file_object:
            if star is None:
                try:
                    star = get_star_name(files[0].name)
                except Exception:
                    star ='unknown'
                if verbose:
                    logger.info(f'assuming star is {star}')

            if instrument is None:
                try:
                    instrument = get_instrument(files[0].name)
                except Exception:
                    instrument = 'unknown'
                if verbose:
                    logger.info(f'assuming instrument is {instrument}')

            instruments = np.array([instrument])
        else:
            if star is None:
                star = np.unique([get_star_name(f) for f in files])[0]
                if verbose:
                    logger.info(f'assuming star is {star}')
            else:
                star = 'unknown'

            if instrument is None:
                instruments = np.array([splitext(basename(f))[0].split('_')[1] for f in files])
                if verbose:
                    logger.info(f'assuming instruments: {instruments}')
            else:
                instruments = np.atleast_1d(instrument)

        if instruments.size == 1 and len(files) > 1:
            instruments = np.repeat(instruments, len(files))

        if instrument_suffix is not None:
            instruments = [i + instrument_suffix for i in instruments]

        factor = 1e3 if units == 'kms' else 1.0

        s = cls(star, _child=True, **kwargs)

        def find_column(data, names):
            has_col = np.array([name.casefold() in data.dtype.fields for name in names])
            if any(has_col):
                col = np.where(has_col)[0][0]
                return np.atleast_1d(data[names[col]])
            return False

        for i, (f, instrument) in enumerate(zip(files, instruments)):
            data = np.loadtxt(f, skiprows=header_skip, usecols=range(3), unpack=True)
            if data.ndim == 1:
                data = data.reshape(-1, 1)

            _s = cls(star, _child=True, **kwargs)
            time = data[0]
            _s.time = time
            _s.vrad = data[1] * factor
            _s.svrad = data[2] * factor

            _quantities = []

            #! hack
            if file_object:
                header = f.readline().strip()
            else:
                with open(f) as ff:
                    header = ff.readline().strip()

            if '\t' in header:
                names = header.split('\t')
            else:
                names = header.split()

            if len(names) > 3:
                # if f.endswith('.rdb'):
                #     kw = dict(skip_header=2, dtype=None, encoding=None)
                # else:
                comments = '#'
                kw = dict(skip_header=2, comments=comments,
                          names=names, dtype=None, encoding=None)
                if '\t' in header:
                    data = np.genfromtxt(f, **kw, delimiter='\t')
                else:
                    data = np.genfromtxt(f, **kw)

                # if data.ndim in (0, 1):
                #     data = data.reshape(-1, 1)

                if len(names) == len(data.dtype.names):
                    data.dtype.names = names
            else:
                data = np.array([], dtype=np.dtype([]))

            # try to find FWHM and uncertainty
            if (v := find_column(data, ['fwhm'])) is not False:  # walrus !!
                _s.fwhm = v * factor
                if (sv := find_column(data, ['sfwhm', 'fwhm_err', 'sig_fwhm'])) is not False:
                    _s.fwhm_err = sv * factor
                    logger.debug('found columns for FWHM and uncertainty') if verbose else None
                else:
                    _s.fwhm_err = 2 * _s.svrad
                    logger.debug('found column for FWHM') if verbose else None
            else:
                _s.fwhm = np.full_like(time, np.nan)
                _s.fwhm_err = np.full_like(time, np.nan)

            _quantities.append('fwhm')
            _quantities.append('fwhm_err')

            # try to find R'HK and uncertainty
            if (v := find_column(data, ['rhk'])) is not False:
                _s.rhk = v
                _s.rhk_err = np.full_like(time, np.nan)
                if (sv := find_column(data, ['srhk', 'rhk_err', 'sig_rhk'])) is not False:
                    _s.rhk_err = sv
                    logger.debug('found columns for logRhk and uncertainty') if verbose else None
            else:
                _s.rhk = np.full_like(time, np.nan)
                _s.rhk_err = np.full_like(time, np.nan)

            _quantities.append('rhk')
            _quantities.append('rhk_err')

            # try to find BISPAN and uncertainty
            if (v := find_column(data, ['bis', 'bispan'])) is not False:
                _s.bispan = v * factor
                _s.bispan_err = np.full_like(time, np.nan)
                if (sv := find_column(data, ['sbispan', 'sig_bispan', 'bispan_err'])) is not False:
                    _s.bispan_err = sv * factor
            else:
                _s.bispan = np.full_like(time, np.nan)
                _s.bispan_err = np.full_like(time, np.nan)

            _quantities.append('bispan')
            _quantities.append('bispan_err')

            # try to find BERV
            if (v := find_column(data, ['berv', 'HIERARCH ESO QC BERV'])) is not False:
                _s.berv = v
            else:
                _s.berv = np.full_like(time, np.nan)
            _quantities.append('berv')

            # other quantities
            msg = ''

            for q, possible in {
                'caindex': ['caindex', 'ca', 'caII'],
                'ccf_asym': ['ccf_asym'],
                'contrast': ['contrast'],
                'haindex': ['haindex', 'ha', 'halpha'],
                'heindex': ['heindex', 'he', 'heII'],
                'naindex': ['naindex', 'na'],
                'sindex': ['sindex', 's_mw'],
            }.items():
                # try to find columns for each quantity
                if (v := find_column(data, possible)) is not False:
                    msg += f'{q}, '
                    setattr(_s, q, v)
                    # try to find uncertainty column for each quantity
                    possible_errors = ['s' + p for p in possible] + ['sig_' + p for p in possible] + [p + '_err' for p in possible]
                    if (sv := find_column(data, possible_errors)) is not False:
                        setattr(_s, q + '_err', sv)
                    else:
                        setattr(_s, q + '_err', np.full_like(time, np.nan))
                else:
                    setattr(_s, q, np.full_like(time, np.nan))
                    setattr(_s, q + '_err', np.full_like(time, np.nan))
                _quantities.append(q)
                _quantities.append(q + '_err')

            if verbose and msg != '':
                if msg.endswith(', '):
                    msg = msg[:-2]
                logger.debug('found columns for ' + msg)


            # more values
            for q in ['texp', ]:
                if (v := find_column(data, q)) is not False:
                    setattr(_s, q, v)
                else:
                    setattr(_s, q, np.full_like(time, np.nan))
                _quantities.append(q)

            # strings
            for q in ['ccf_mask', 'date_night', 'prog_id', 'raw_file', 'pub_reference']:
                if (v := find_column(data, q)) is not False:
                    setattr(_s, q, v)
                else:
                    setattr(_s, q, np.full(time.size, ''))
                _quantities.append(q)

            # booleans
            for q in ['drs_qc', ]:
                setattr(_s, q, np.full(time.size, True))
                _quantities.append(q)

            _s.extra_fields = ExtraFields()
            for name in data.dtype.names:
                # don't repeat some quantities
                if name not in _quantities + ['bjd', 'rjd', 'vrad', 'svrad']:
                    name_ = name.replace(' ', '_').replace('-', '_')
                    setattr(_s.extra_fields, name_, data[name])
                    # _quantities.append(field)

            #! end hack

            _s.mask = np.ones_like(time, dtype=bool)
            _s.obs = np.full_like(time, i + 1)

            _s.instruments = [str(instrument)]
            _s._quantities = np.array(_quantities)
            setattr(s, instrument, _s)

        s._child = False
        s.instruments = list(map(str, instruments))
        s.filenames = list(map(str, files))

        s._build_arrays()

        if kwargs.get('do_adjust_means', False):
            s.adjust_means()

        return s

    @classmethod
    def from_ccf(cls, files, star=None, instrument=None, **kwargs):
        """ Create an RV object from a CCF file or a list of CCF files

        !!! Note
            This function relies on the `iCCF` package

        Args:
            files (str or list):
                CCF file or list of CCF files
            star (str):
                Star name. If not provided, it will be inferred from the header
                of the CCF file
            instrument (str):
                Instrument name. If not provided, it will be inferred from the
                header of the CCF file
        
        """
        try:
            import iCCF
        except ImportError:
            logger.error('iCCF is not installed. Please install it with `pip install iCCF`')
            return

        verbose = kwargs.get('verbose', True)

        if isinstance(files, str):
            files = [files]

        hdu_number = kwargs.pop('hdu_number', 1)
        data_index = kwargs.pop('data_index', -1)
        CCFs = iCCF.from_file(files, hdu_number=hdu_number, data_index=data_index)

        if not isinstance(CCFs, list):
            CCFs = [CCFs]

        try:
            objects = np.unique([i.OBJECT for i in CCFs])
        except AttributeError:
            objects = np.unique([i.HDU[0].header['OBJECT'].replace(' ', '') for i in CCFs])

        if len(objects) != 1:
            logger.warning(f'found {objects.size} different stars in the CCF files ({objects}), '
                           'choosing the first one')
        star = objects[0]

        s = cls(star, _child=True)
        instruments = list(np.unique([i.instrument for i in CCFs]))

        for instrument in instruments:
            # time, RVs, uncertainties
            time = np.array([i.bjd for i in CCFs])
            vrad = np.array([i.RV*1e3 for i in CCFs])
            svrad = np.array([i.RVerror*1e3 for i in CCFs])
            _s = RV.from_arrays(star, time, vrad, svrad, inst=instrument)

            _quantities = []

            _s.fwhm = np.array([i.FWHM*1e3 for i in CCFs])
            _s.fwhm_err = np.array([i.FWHMerror*1e3 for i in CCFs])
            _quantities.append('fwhm')
            _quantities.append('fwhm_err')

            _s.contrast = np.array([i.contrast for i in CCFs])
            _s.contrast_err = np.array([i.contrast_error for i in CCFs])
            _quantities.append('contrast')
            _quantities.append('contrast_err')

            _s.bispan = np.array([i.BIS*1e3 for i in CCFs])
            _s.bispan_err = np.array([i.BISerror*1e3 for i in CCFs])
            _quantities.append('bispan')
            _quantities.append('bispan_err')

            _s.rhk = np.full_like(time, np.nan)
            _s.rhk_err = np.full_like(time, np.nan)
            _quantities.append('rhk')
            _quantities.append('rhk_err')

            _s.texp = np.array([i.HDU[0].header['EXPTIME'] for i in CCFs])
            _quantities.append('texp')

            _s.berv = np.array([i.HDU[0].header['HIERARCH ESO QC BERV'] for i in CCFs])
            _quantities.append('berv')

            _s.date_night = np.array([
                i.HDU[0].header['DATE-OBS'].split('T')[0] for i in CCFs
            ])
            _quantities.append('date_night')

            _s.mask = np.full_like(_s.time, True, dtype=bool)

            _s.drs_qc = np.array([i.HDU[0].header['*QC SCIRED CHECK'][0] for i in CCFs], dtype=bool)
            # mask out drs_qc = False
            if not _s.drs_qc.all():
                n = (~ _s.drs_qc).sum()
                if verbose:
                    logger.warning(f'masking {n} points where DRS QC failed for {instrument}')
                _s.mask &= _s.drs_qc

            _s._quantities = np.array(_quantities)
            setattr(s, instrument, _s)

        s._child = False
        s.instruments = instruments
        s._build_arrays()

        if instruments == ['ESPRESSO']:
            from .instrument_specific import divide_ESPRESSO
            divide_ESPRESSO(s)
        elif instruments == ['HARPS']:
            from .instrument_specific import divide_HARPS
            divide_HARPS(s)

        if kwargs.get('do_adjust_means', False):
            s.adjust_means()

        return s

    @classmethod
    # @lru_cache(maxsize=60)
    def from_KOBE_file(cls, star, directory='.', force_download=False, **kwargs):
        assert 'KOBE' in star, f'{star} is not a KOBE star?'
        import requests
        from requests.auth import HTTPBasicAuth
        from io import BytesIO
        import tarfile
        from time import time as pytime
        from astropy.io import fits
        from .config import config
        from .utils import get_data_path

        try:
            config.kobe_password
        except KeyError:
            logger.error('please set arvi.config.kobe_password')
            return

        tar = None
        local_targz_file = os.path.join(get_data_path(), 'KOBE_fitsfiles.tar.gz')
        fits_file = f'{star}_RVs.fits'

        local_exists = os.path.exists(local_targz_file)
        local_recent = local_exists and os.path.getmtime(local_targz_file) > pytime() - 60*60*2

        if os.path.exists(os.path.join(directory, fits_file)):
            logger.info(f'found file "{fits_file}" in "{directory}"')
            hdul = fits.open(fits_file)

        elif local_exists and local_recent and not force_download:
            tar = tarfile.open(local_targz_file)

            if fits_file not in tar.getnames():
                logger.error(f'KOBE file not found for {star}')
                return

            hdul = fits.open(tar.extractfile(fits_file))

        else:
            resp = requests.get(f'https://kobe.caha.es/internal/fitsfiles/{fits_file}',
                                auth=HTTPBasicAuth('kobeteam', config.kobe_password))

            if resp.status_code != 200:
                # something went wrong, try to extract the file by downloading the
                # full tar.gz archive

                logger.warning(f'could not find "{fits_file}" on server, trying to download full archive')
                resp = requests.get('https://kobe.caha.es/internal/fitsfiles.tar.gz',
                                    auth=HTTPBasicAuth('kobeteam', config.kobe_password))

                if resp.status_code != 200:
                    logger.error(f'KOBE file not found for {star}')
                    return

                # save tar.gz file for later
                with open(local_targz_file, 'wb') as tg:
                    tg.write(resp.content)

                tar = tarfile.open(fileobj=BytesIO(resp.content))

                if fits_file not in tar.getnames():
                    logger.error(f'KOBE file not found for {star}')
                    return

                hdul = fits.open(tar.extractfile(fits_file))

            else:
                logger.info(f'found file "{fits_file}" on server')
                # found the file on the server, read it directly
                hdul = fits.open(BytesIO(resp.content))

        s = cls(star, _child=True)

        s.time = hdul[1].data['BJD']

        s.vrad = hdul[1].data['RVc']
        s.svrad = hdul[1].data['eRVc']
        s.vrad_preNZP = hdul[1].data['RVd']
        s.vrad_preNZP_err = hdul[1].data['eRVd']

        s.fwhm = hdul[1].data['FWHM']
        s.fwhm_err = hdul[1].data['eFWHM']

        s.crx = hdul[1].data['CRX']
        s.crx_err = hdul[1].data['eCRX']
        s.dlw = hdul[1].data['DLW']
        s.dlw_err = hdul[1].data['eDLW']
        s.contrast = hdul[1].data['CONTRAST']
        s.contrast_err = hdul[1].data['eCONTRAST']
        s.bispan = hdul[1].data['BIS']
        s.bispan_err = hdul[1].data['eBIS']


        s.drift = hdul[1].data['drift']
        s.drift_err = hdul[1].data['e_drift']

        s.nzp = hdul[1].data['NZP']
        s.nzp_err = hdul[1].data['eNZP']

        s.texp = hdul[1].data['ExpTime']
        s.berv = hdul[1].data['BERV']
        s.units = 'km/s'

        s.obs = np.ones_like(s.time, dtype=int)
        s.mask = np.full_like(s.time, True, dtype=bool)
        s.instruments = ['CARMENES']
        s._quantities = np.array(['berv', ])

        # so meta!
        setattr(s, 'CARMENES', s)

        s._kobe_result = hdul[1].data

        s.mask = s._kobe_result['rvflag']
        s._propagate_mask_changes()

        if tar is not None:
            tar.close()
        hdul.close()

        s._child = False
        return s


    def _check_instrument(self, instrument, strict=False, log=False):# -> list | None:
        """
        Check if there are observations from `instrument`.

        Args:
            instrument (str, None): Instrument name to check
            strict (bool): Whether to match `instrument` exactly
        Returns:
            instruments (list):
                List of instruments matching `instrument`, or None if there
                are no matches.
        """
        if instrument is None:
            return self.instruments

        if isinstance(instrument, list):
            if strict:
                return [inst for inst in instrument if inst in self.instruments]
            else:
                r = []
                for i in instrument:
                    if any([i in inst for inst in self.instruments]):
                        r += [inst for inst in self.instruments if i in inst]
                return r

        else:
            if strict:
                if instrument in self.instruments:
                    return [instrument]
            else:
                if any([instrument in inst for inst in self.instruments]):
                    return [inst for inst in self.instruments if instrument in inst]

        if log:
            logger.error(f"No data from instrument '{instrument}'")
            logger.info(f'available: {self.instruments}')
            return

    def _build_arrays(self):
        """ build all concatenated arrays of `self` from each of the `.inst`s """
        if self._child:
            return
        # time
        self.time = np.concatenate(
            [getattr(self, inst).time for inst in self.instruments]
        )
        # RVs
        self.vrad = np.concatenate(
            [getattr(self, inst).vrad for inst in self.instruments]
        )
        # uncertainties
        self.svrad = np.concatenate(
            [getattr(self, inst).svrad for inst in self.instruments]
        )

        # mask
        self.mask = np.concatenate(
            [getattr(self, inst).mask for inst in self.instruments]
        )

        # "observatory" (or instrument id)
        self.obs = np.concatenate(
            [np.full(getattr(self, inst).N, i+1) for i, inst in enumerate(self.instruments)],
            dtype=int
        )


        # all other quantities
        self._quantities = getattr(self, self.instruments[0])._quantities
        if len(self.instruments) > 1:
            for inst in self.instruments[1:]:
                self._quantities = np.intersect1d(self._quantities, getattr(self, inst)._quantities)

        for q in self._quantities:
            if q not in ('rjd', 'rv', 'rv_err'):
                arr = np.concatenate(
                    [getattr(getattr(self, inst), q) for inst in self.instruments]
                )
                setattr(self, q, arr)

    @property
    def download_directory(self):
        """ Directory where to download data """
        return self._download_directory

    @download_directory.setter
    def download_directory(self, value):
        self._download_directory = value

    def download_ccf(self, instrument=None, index=None, limit=None,
                     directory=None, clobber=False, symlink=False, load=True, **kwargs):
        """ Download CCFs from DACE

        Args:
            instrument (str): Specific instrument for which to download data
            index (int): Specific index of point for which to download data (0-based)
            limit (int): Maximum number of files to download.
            directory (str): Directory where to store data.
            clobber (bool): Whether to overwrite existing files.
        """
        directory = directory or self.download_directory

        strict = kwargs.pop('strict', False)
        instrument = self._check_instrument(instrument, strict=strict)
        files = []
        for inst in instrument:
            files += list(getattr(self, inst).raw_file)

        if index is not None:
            index = np.atleast_1d(index)
            files = list(np.array(files)[index])

        # remove empty strings
        files = list(filter(None, files))

        if symlink:
            if 'top_level' not in kwargs:
                logger.warning('may need to provide `top_level` in kwargs to find file')
            do_symlink_filetype('CCF', files[:limit], directory, **kwargs)
        else:
            downloaded = do_download_filetype('CCF', files[:limit], directory, 
                                              clobber=clobber, verbose=self.verbose, 
                                              user=self.user, **kwargs)

        if load:
            try:
                from os.path import basename, join, exists
                from .utils import sanitize_path
                import iCCF
                downloaded = [
                    sanitize_path(join(directory, basename(f).replace('.fits', '_CCF_A.fits')))
                    for f in files[:limit]
                ]
                downloaded = [
                    skysub
                    if exists(skysub := f.replace('CCF_A.fits', 'CCF_SKYSUB_A.fits')) else f
                    for f in downloaded
                ]
                if self.verbose:
                    logger.info('loading the CCF(s) into `.CCF` attribute')

                self.CCF = iCCF.from_file(downloaded, verbose=False)
                if len(self.CCF) == 1:
                    self.CCF = [self.CCF]

                if self.simbad is None:
                    if self.verbose:
                        logger.info('querying Simbad with RA/DEC from CCF header')
                    ra = self.CCF[0].HDU[0].header['RA']
                    dec = self.CCF[0].HDU[0].header['DEC']
                    self._simbad = simbad.from_ra_dec(ra, dec)

            except (ImportError, ValueError, FileNotFoundError):
                logger.error('could not load CCF(s) into `.CCF` attribute')

    def download_s1d(self, instrument=None, index=None, limit=None,
                     directory=None, clobber=False, apply_mask=True, symlink=False, **kwargs):
        """ Download S1Ds from DACE

        Args:
            instrument (str): Specific instrument for which to download data
            index (int): Specific index of point for which to download data (0-based)
            limit (int): Maximum number of files to download.
            directory (str): Directory where to store data.
            clobber (bool): Whether to overwrite existing files.
            apply_mask (bool): Apply mask to the observations before downloading.
        """
        directory = directory or self.download_directory

        strict = kwargs.pop('strict', False)
        instrument = self._check_instrument(instrument, strict=strict)
        files = []
        for inst in instrument:
            _s = getattr(self, inst)
            if apply_mask:
                files += list(_s.raw_file[_s.mask])
            else:
                files += list(_s.raw_file)

        if index is not None:
            index = np.atleast_1d(index)
            files = list(np.array(files)[index])

        # remove empty strings
        files = list(filter(None, files))

        if symlink:
            if 'top_level' not in kwargs:
                logger.warning('may need to provide `top_level` in kwargs to find file')
            do_symlink_filetype('S1D', files[:limit], directory, **kwargs)
        else:
            do_download_filetype('S1D', files[:limit], directory, clobber=clobber,
                                 verbose=self.verbose, user=self.user, **kwargs)

    def download_s2d(self, instrument=None, index=None, limit=None,
                     directory=None, clobber=False, symlink=False, **kwargs):
        """ Download S2Ds from DACE

        Args:
            instrument (str): Specific instrument for which to download data
            index (int): Specific index of point for which to download data (0-based)
            limit (int): Maximum number of files to download.
            directory (str): Directory where to store data.
            clobber (bool): Whether to overwrite existing files.
        """
        directory = directory or self.download_directory

        strict = kwargs.pop('strict', False)
        instrument = self._check_instrument(instrument, strict=strict)
        files = []
        for inst in instrument:
            files += list(getattr(self, inst).raw_file)

        if index is not None:
            index = np.atleast_1d(index)
            files = list(np.array(files)[index])

        # remove empty strings
        files = list(filter(None, files))

        if symlink:
            if 'top_level' not in kwargs:
                logger.warning('may need to provide `top_level` in kwargs to find file')
            do_symlink_filetype('S2D', files[:limit], directory, **kwargs)
        else:
            do_download_filetype('S2D', files[:limit], directory, 
                                 verbose=self.verbose, user=self.user, **kwargs)



    from .plots import plot, plot_fwhm, plot_bispan, plot_contrast, plot_rhk, plot_berv, plot_quantity
    from .plots import gls, gls_fwhm, gls_bispan, gls_rhk, gls_quantity, window_function

    # from .reports import report
    # from .instrument_specific import known_issues

    def change_instrument_name(self, old_name, new_name, strict=False):
        """ Change the name of an instrument

        Args:
            old_name (str):
                The old name of the instrument
            new_name (str):
                The new name of the instrument, or postfix if `strict` is False
            strict (bool):
                Whether to match (each) `instrument` exactly
        """
        if new_name == '':
            if self.verbose:
                logger.error('new name cannot be empty string')
            return

        instruments = self._check_instrument(old_name, strict, log=True)
        if instruments is not None:
            several = len(instruments) >= 2
            for instrument in instruments:
                if several:
                    new_name_instrument = f'{instrument}_{new_name}'
                else:
                    new_name_instrument = new_name
                if self.verbose:
                    logger.info(f'Renaming {instrument} to {new_name_instrument}')

                setattr(self, new_name_instrument, getattr(self, instrument))
                delattr(self, instrument)
                self.instruments[self.instruments.index(instrument)] = new_name_instrument

            self._build_arrays()


    def remove_instrument(self, instrument, strict=False):
        """ Remove all observations from one instrument

        Args:
            instrument (str or list):
                The instrument(s) for which to remove observations.
            strict (bool):
                Whether to match (each) `instrument` exactly

        Note:
            A common name can be used to remove observations for several subsets
            of a given instrument. For example

            ```py
            s.remove_instrument('HARPS')
            ```

            will remove observations from `HARPS03` and `HARPS15`, if they
            exist. But

            ```py
            s.remove_instrument('HARPS03')
            ```

            will only remove observations from the specific subset.
        """
        instruments = self._check_instrument(instrument, strict)

        if instruments is None:
            if self.verbose:
                logger.error(f"No data from instrument '{instrument}'")
                logger.info(f'available: {self.instruments}')
            return

        for instrument in instruments:
            ind = self.instruments.index(instrument) + 1
            remove = np.where(self.obs == ind)
            self.obs = np.delete(self.obs, remove)
            self.obs[self.obs > ind] -= 1
            #
            self.time = np.delete(self.time, remove)
            self.vrad = np.delete(self.vrad, remove)
            self.svrad = np.delete(self.svrad, remove)
            #
            self.mask = np.delete(self.mask, remove)
            #
            # all other quantities
            for q in self._quantities:
                if q not in ('rjd', 'rv', 'rv_err'):
                    new = np.delete(getattr(self, q), remove)
                    setattr(self, q, new)
            #
            self.instruments.remove(instrument)
            #
            delattr(self, instrument)

            if self.verbose:
                logger.info(f"Removed observations from '{instrument}'")

        if config.return_self:
            return self

    def remove_condition(self, condition):
        """ Remove all observations that satisfy a condition

        Args:
            condition (ndarray):
                Boolean array of the same length as the observations
        """
        if self.verbose:
            inst = np.unique(self.instrument_array[condition])
            logger.info(f"Removing {condition.sum()} points from instruments {inst}")
        self.mask = self.mask & ~condition
        self._propagate_mask_changes()

    def remove_point(self, index):
        """
        Remove individual observations at a given index (or indices).
        
        !!! Note
            Like Python, the index is 0-based.

        Args:
            index (int, list, ndarray):
                Single index, list, or array of indices to remove.
        """
        index = np.atleast_1d(index)
        try:
            instrument_index = self.obs[index]
            np.array(self.instruments)[instrument_index - 1]
        except IndexError:
            logger.error(f'index {index} is out of bounds for N={self.N}')
            return

        if self.verbose:
            inst = np.unique(self.instrument_array[index])
            if len(index) == 1:
                logger.info(f'removing point {index[0]} from {inst[0]}')
            else:
                logger.info(f'removing points {index} from {inst}')

        self.mask[index] = False
        self._propagate_mask_changes()
        # for i, inst in zip(index, instrument):
        #     index_in_instrument = i - (self.obs < instrument_index).sum()
        #     getattr(self, inst).mask[index_in_instrument] = False
        if config.return_self:
            return self

    def restore_point(self, index):
        """
        Restore previously deleted individual observations at a given index (or
        indices). 
        
        !!! Note
            Like Python, the index is 0-based

        Args:
            index (int, list, ndarray):
                Single index, list, or array of indices to restore
        """
        index = np.atleast_1d(index)
        try:
            instrument_index = self.obs[index]
            np.array(self.instruments)[instrument_index - 1]
        except IndexError:
            logger.error(f'index {index} is out of bounds for N={self.N}')
            return

        if self.verbose:
            logger.info(f'restoring point{"s" if index.size > 1 else ""} {index}')

        self.mask[index] = True
        self._propagate_mask_changes()
        if config.return_self:
            return self

    def remove_non_public(self):
        """ Remove non-public observations """
        if self.verbose:
            n = (~self.public).sum()
            logger.info(f'masking non-public observations ({n})')
        self.mask = self.mask & self.public
        self._propagate_mask_changes()

    def remove_public(self):
        """ Remove public observations """
        if self.verbose:
            n = self.public.sum()
            logger.info(f'masking public observations ({n})')
        self.mask = self.mask & (~self.public)
        self._propagate_mask_changes()

    def remove_single_observations(self):
        """ Remove instruments for which there is a single observation """
        singles = [i for i in self.instruments if getattr(self, i).mtime.size == 1]
        for inst in singles:
            self.remove_instrument(inst, strict=True)

    def remove_prog_id(self, prog_id):
        """ Remove observations from a given program ID """
        from glob import has_magic
        if has_magic(prog_id):
            from fnmatch import filter
            matching = np.unique(filter(self.prog_id, prog_id))
            mask = np.full_like(self.time, False, dtype=bool)
            for m in matching:
                mask |= np.isin(self.prog_id, m)
            ind = np.where(mask)[0]
            self.remove_point(ind)
        else:
            if prog_id in self.prog_id:
                ind = np.where(self.prog_id == prog_id)[0]
                self.remove_point(ind)
            else:
                if self.verbose:
                    logger.warning(f'no observations for prog_id "{prog_id}"')

    def remove_after_bjd(self, bjd: float):
        """ Remove observations after a given BJD """
        if (self.time > bjd).any():
            ind = np.where(self.time > bjd)[0]
            self.remove_point(ind)

    def remove_before_bjd(self, bjd: float):
        """ Remove observations before a given BJD """
        if (self.time < bjd).any():
            ind = np.where(self.time < bjd)[0]
            self.remove_point(ind)

    def remove_between_bjds(self, bjd1: float, bjd2: float):
        """ Remove observations between two BJDs """
        to_remove = (self.time > bjd1) & (self.time < bjd2)
        if to_remove.any():
            ind = np.where(to_remove)[0]
            self.remove_point(ind)

    def choose_n_points(self, n: int, seed=None, instrument=None):
        """ Randomly choose `n` observations and mask out the remaining ones

        Args:
            n (int):
                Number of observations to keep.
            seed (int, optional):
                Random seed for reproducibility.
            instrument (str or list, optional):
                For which instrument to choose points (default is all).
        """
        instruments = self._check_instrument(instrument)
        rng = np.random.default_rng(seed=seed)
        for inst in instruments:
            # s = getattr(self, inst)
            mask_for_this_inst = self.obs == self.instruments.index(inst) + 1
            # only choose if there are more than n points
            if self.mask[mask_for_this_inst].sum() > n:
                if self.verbose:
                    logger.info(f'selecting {n} points from {inst}')
                # indices of points for this instrument which are not masked already
                available = np.where(self.mask & mask_for_this_inst)[0]
                # choose n randomly
                i = rng.choice(available, size=n, replace=False)
                # mask the others out
                self.mask[np.setdiff1d(available, i)] = False
        self._propagate_mask_changes()


    def _propagate_mask_changes(self, _remove_instrument=True):
        """ link self.mask with each self.`instrument`.mask """
        masked = np.where(~self.mask)[0]
        for m in masked:
            inst = self.instruments[self.obs[m] - 1]
            n_before = (self.obs < self.obs[m]).sum()
            getattr(self, inst).mask[m - n_before] = False
        if _remove_instrument:
            for inst in self.instruments:
                if getattr(self, inst).mtime.size == 0:
                    self.remove_instrument(inst, strict=True)

    def secular_acceleration(self, epoch=None, just_compute=False, force_simbad=False):
        """ 
        Remove secular acceleration from RVs. This uses the proper motions from
        Gaia (in `self.gaia`) if available, otherwise from Simbad (in
        `self.simbad`), unless `force_simbad=True`.


        Args:
            epoch (float, optional):
                The reference epoch (DACE uses 55500, 31/10/2010)
            just_compute (bool, optional):
                Just compute the secular acceleration and return, without
                changing the RVs
            force_simbad (bool, optional):
                Use Simbad proper motions even if Gaia is available
        """
        # don't do it twice
        if self._did_secular_acceleration and not just_compute:
            return

        from astropy import units

        #as_yr = units.arcsec / units.year
        mas_yr = units.milliarcsecond / units.year
        mas = units.milliarcsecond

        # store the source of coordinates and parallax, either Gaia or Simbad
        using = ''

        try:
            if force_simbad:
                raise AttributeError

            self.gaia
            self.gaia.plx

            if self.gaia.plx < 0:
                if self.verbose:
                    logger.error('negative Gaia parallax, falling back to Simbad')
                raise AttributeError

            using = 'Gaia'

            if epoch is None:
                # Gaia DR3 epoch (astropy.time.Time('J2016.0', format='jyear_str').jd)
                epoch = 57389.0

            π = self.gaia.plx * mas
            d = π.to(units.pc, equivalencies=units.parallax())
            μα = self.gaia.pmra * mas_yr
            μδ = self.gaia.pmdec * mas_yr
            μ = μα**2 + μδ**2
            sa = (μ * d).to(units.m / units.second / units.year,
                            equivalencies=units.dimensionless_angles())
        except AttributeError:
            try:
                self.simbad
                if self.simbad is None:
                    raise AttributeError
            except AttributeError:
                if self.verbose:
                    logger.error('no information from simbad, cannot remove secular acceleration')
                return

            if self.simbad.plx is None:
                if self.verbose:
                    logger.error('no parallax from simbad, cannot remove secular acceleration')
                return

            using = 'Simbad'

            if epoch is None:
                epoch = 55500

            π = self.simbad.plx * mas
            d = π.to(units.pc, equivalencies=units.parallax())
            μα = self.simbad.pmra * mas_yr
            μδ = self.simbad.pmdec * mas_yr
            μ = μα**2 + μδ**2
            sa = (μ * d).to(units.m / units.second / units.year,
                            equivalencies=units.dimensionless_angles())

        if just_compute:
            return sa

        sa = sa.value

        if self.units == 'km/s':
            sa /= 1000

        actually_removed_sa = False

        if self._child:
            self.vrad = self.vrad - sa * (self.time - epoch) / 365.25
            actually_removed_sa = True
        else:
            for inst in self.instruments:
                s = getattr(self, inst)

                # if RVs come from a publication, don't remove the secular
                # acceleration
                if np.all(s.pub_reference != ''):
                    continue

                if 'HIRES' in inst or 'HAMILTON' in inst:
                    continue

                if hasattr(s, '_did_secular_acceleration') and s._did_secular_acceleration:
                    continue

                s.vrad = s.vrad - sa * (s.time - epoch) / 365.25

                actually_removed_sa = True

            self._build_arrays()

        if actually_removed_sa and self.verbose:
            logger.info(f'using {using} information to remove secular acceleration')
            logger.info('removing secular acceleration from RVs')

        self._did_secular_acceleration = True
        self._did_secular_acceleration_epoch = epoch
        self._did_secular_acceleration_simbad = force_simbad

        if config.return_self:
            return self

    def _undo_secular_acceleration(self):
        if self._did_secular_acceleration:
            _old_verbose = self.verbose
            self.verbose = False
            sa = self.secular_acceleration(just_compute=True,
                                           force_simbad=self._did_secular_acceleration_simbad)
            self.verbose = _old_verbose
            sa = sa.value

            if self._child:
                self.vrad = self.vrad + sa * (self.time - self._did_secular_acceleration_epoch) / 365.25
            else:
                for inst in self.instruments:
                    if 'HIRES' in inst:  # never remove it from HIRES...
                        continue
                    if 'NIRPS' in inst:  # never remove it from NIRPS...
                        continue

                    s = getattr(self, inst)

                    s.vrad = s.vrad + sa * (s.time - self._did_secular_acceleration_epoch) / 365.25

                self._build_arrays()

            self._did_secular_acceleration = False

    def sigmaclip(self, sigma=5, quantity='vrad', instrument=None,
                  strict=True):
        """
        Sigma-clip RVs or other quantities (per instrument!), by MAD away from
        the median.

        Args:
            sigma (float):
                Number of MADs away from the median
            quantity (str):
                Quantity to sigma-clip (by default the RVs)
            instrument (str, list):
                Instrument(s) to sigma-clip
            strict (bool):
                Passed directly to self._check_instrument
        """
        #from scipy.stats import sigmaclip as dosigmaclip
        from .stats import sigmaclip_median as dosigmaclip

        if self._child or self._did_sigma_clip:
            return

        instruments = self._check_instrument(instrument, strict)
        changed_instruments = []

        for inst in instruments:
            m = self.instrument_array == inst
            d = getattr(self, quantity)

            if np.isnan(d[m]).all():
                continue

            result = dosigmaclip(d[m], low=sigma, high=sigma)
            # n = self.vrad[m].size - result.clipped.size

            ind = m & self.mask & ((d < result.lower) | (d > result.upper))
            n = ind.sum()

            if self.verbose and n > 0:
                s = 's' if (n == 0 or n > 1) else ''
                logger.warning(f'sigma-clip {quantity} will remove {n} point{s} for {inst}')

            if n > 0:
                self.mask[ind] = False
                changed_instruments.append(inst)

            # # check if going to remove all observations from one instrument
            # if n in self.NN.values(): # all observations
            #     # insts = np.unique(self.instrument_array[~ind])
            #     # if insts.size == 1: # of the same instrument?
            #     if self.verbose:
            #         logger.warning(f'would remove all observations from {insts[0]}, skipping')
            #     if config.return_self:
            #         return self
            #     continue

        self._propagate_mask_changes()

        if len(changed_instruments) > 0 and self._did_adjust_means:
            self._did_adjust_means = False
            self.adjust_means(instrument=changed_instruments)

        if config.return_self:
            return self

    def clip_maxerror(self, maxerror:float, instrument=None):
        """
        Mask out points with RV error larger than a given value. If `instrument`
        is given, mask only observations from that instrument.

        Args:
            maxerror (float): Maximum error to keep.
            instrument (str, list, tuple, ndarray): Instrument(s) to clip
        """
        if self._child:
            return

        self.maxerror = maxerror

        if instrument is None:
            inst_mask = np.ones_like(self.svrad, dtype=bool)
        else:
            inst_mask = self._instrument_mask(instrument)
        
        above = self.svrad > maxerror
        old_mask = self.mask.copy()

        self.mask[inst_mask & above] = False

        if self.verbose and above.sum() > 0:
            n = (above[inst_mask] & old_mask[inst_mask]).sum()
            s = 's' if (n == 0 or n > 1) else ''
            logger.warning(f'clip_maxerror ({maxerror} {self.units}) removed {n} point' + s)

        self._propagate_mask_changes()
        if config.return_self:
            return self

    def sigmaclip_ew(self, sigma=5):
        """ Sigma-clip EW (FWHM x contrast), by MAD away from the median """
        from .stats import sigmaclip_median as dosigmaclip, weighted_median

        S = deepcopy(self)
        for _s in S:
            m = _s.mask
            _s.fwhm -= weighted_median(_s.fwhm[m], 1 / _s.fwhm_err[m])
            _s.contrast -= weighted_median(_s.contrast[m], 1 / _s.contrast_err[m])
        S._build_arrays()
        ew = S.fwhm * S.contrast
        ew_err = np.hypot(S.fwhm_err * S.contrast, S.fwhm * S.contrast_err)

        wmed = weighted_median(ew[S.mask], 1 / ew_err[S.mask])
        data = (ew - wmed) / ew_err
        result = dosigmaclip(data, low=sigma, high=sigma)
        ind = (data < result.lower) | (data > result.upper)
        self.mask[ind] = False

        if self.verbose and ind.sum() > 0:
            n = ind.sum()
            s = 's' if (n == 0 or n > 1) else ''
            logger.warning(f'sigmaclip_ew removed {n} point' + s)

        self._propagate_mask_changes()
        if config.return_self:
            return self



    def bin(self):
        """
        Nightly bin the observations.

        !!! Warning
            This creates and returns a new object and does not modify self.
        """

        # create copy of self to be returned
        snew = deepcopy(self)
        # store original object
        snew._unbinned = deepcopy(self)

        all_bad_quantities = []

        for inst in snew.instruments:
            s = getattr(snew, inst)

            # only one observation?
            if s.N == 1:
                continue

            # are all observations masked?
            if s.mtime.size == 0:
                continue

            tb, vb, svb = binRV(s.mtime, s.mvrad, s.msvrad)
            s.vrad = vb
            s.svrad = svb

            bad_quantities = []

            for q in s._quantities:
                Q = getattr(s, q)

                # treat date_night specially, basically doing a group-by
                if q == 'date_night':
                    inds = binRV(s.mtime, None, None, binning_indices=True)
                    setattr(s, q, Q[s.mask][inds])
                    continue

                # treat ccf_mask specially, doing a 'unique' bin
                if q == 'ccf_mask':
                    ccf_mask = getattr(s, q)[s.mask]
                    setattr(s, q, bin_ccf_mask(s.mtime, ccf_mask))
                    continue

                if Q.dtype != np.float64:
                    bad_quantities.append(q)
                    all_bad_quantities.append(q)
                    continue

                if np.isnan(Q).all():
                    yb = np.full_like(tb, np.nan)
                    setattr(s, q, yb)

                elif q + '_err' in s._quantities:
                    Qerr = getattr(s, q + '_err')
                    if (Qerr == 0.0).all(): # if all errors are NaN, don't use them
                        _, yb = binRV(s.mtime, Q[s.mask], stat='mean', tstat='mean')
                    else:
                        if (Qerr <= 0.0).any(): # if any error is <= 0, set it to NaN
                            Qerr[Qerr <= 0.0] = np.nan

                        _, yb, eb = binRV(s.mtime, Q[s.mask], Qerr[s.mask], remove_nans=False)
                        setattr(s, q + '_err', eb)

                    setattr(s, q, yb)

                elif not q.endswith('_err'):
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', category=RuntimeWarning)
                        try:
                            _, yb = binRV(s.mtime, Q[s.mask],
                                        stat=np.nanmean, tstat=np.nanmean)
                            setattr(s, q, yb)
                        except TypeError:
                            pass

            if snew.verbose and len(bad_quantities) > 0:
                logger.warning(f"{inst}, skipping non-float quantities in binning:")
                logger.warning(' ' + str(list(map(str, bad_quantities))))
                for bq in bad_quantities:
                    s._quantities = np.delete(s._quantities, s._quantities==bq)
                    delattr(s, bq)  #! careful here

            s.time = tb
            s.mask = np.full(tb.shape, True)

        if snew.verbose and len(all_bad_quantities) > 0:
            logger.warning('\nnew object will not have these quantities')

        for q in np.unique(all_bad_quantities):
            delattr(snew, q)

        snew._did_bin = True
        snew._build_arrays()
        return snew

    def nth_day_mean(self, n=1.0, masked=True):
        """ Calculate the n-th day rolling mean of the radial velocities """
        if masked:
            mask = np.abs(self.mtime[:, None] - self.mtime[None, :]) < n
            z = np.full((self.mtime.size, self.mtime.size), np.nan)
            z[mask] = np.repeat(self.mvrad[:, None], self.mtime.size, axis=1)[mask]
        else:
            mask = np.abs(self.time[:, None] - self.time[None, :]) < n
            z = np.full((self.time.size, self.time.size), np.nan)
            z[mask] = np.repeat(self.vrad[:, None], self.time.size, axis=1)[mask]
        return np.nanmean(z, axis=0)

    def subtract_mean(self):
        """ Subtract (a single) non-weighted mean RV from all instruments """
        self._meanRV = meanRV = self.mvrad.mean()
        for inst in self.instruments:
            s = getattr(self, inst)
            s.vrad -= meanRV
        self._build_arrays()

    def _add_back_mean(self):
        """ Add the (single) mean RV removed by self.subtract_mean() """
        if not hasattr(self, '_meanRV'):
            logger.warning("no mean RV stored, run 'self.subtract_mean()'")
            return

        for inst in self.instruments:
            s = getattr(self, inst)
            s.vrad += self._meanRV
        self._build_arrays()

    def adjust_means(self, just_rv=False, exclude_rv=False, instrument=None, **kwargs):
        """
        Subtract individual weighted mean RV from each instrument or from
        specific instruments
        """
        if self._child or self._did_adjust_means:
            return

        if just_rv and exclude_rv:
            logger.error('cannot use `just_rv` and `exclude_rv` at the same time')
            return

        # if self.verbose:
        #     print_as_table = len(self.instruments) > 2 and len(self.instruments) < 7
        #     rows = [self.instruments]
        #     row = []
        #     if print_as_table:
        #         logger.info('subtracted weighted average from each instrument:')

        others = ('fwhm', 'bispan', )

        instruments = self._check_instrument(instrument, strict=kwargs.get('strict', False))

        for inst in instruments:
            s = getattr(self, inst)

            if s.mtime.size == 0:
                if self.verbose:
                    logger.info(f'all observations of {inst} are masked')
                continue

            if s.N == 1:
                if self.verbose:
                    msg = (f'only 1 observation for {inst}, '
                           'adjust_means will set it exactly to zero')
                    logger.warning(msg)
                s.rv_mean = s.vrad[0]
                s.vrad = np.zeros_like(s.time)
                continue

            if not exclude_rv:
                s.rv_mean = wmean(s.mvrad, s.msvrad)
                s.vrad -= s.rv_mean

                if self.verbose:
                    logger.info(f'subtracted weighted average from {inst:10s}: ({s.rv_mean:.3f} {self.units})')

            if just_rv:
                continue

            for i, other in enumerate(others):
                try:
                    y, ye = getattr(s, other), getattr(s, other + '_err')
                except AttributeError:
                    continue
                m = wmean(y[s.mask], ye[s.mask])
                setattr(s, f'{other}_mean', m)
                setattr(s, other, getattr(s, other) - m)

        if self.verbose:
            logger.info(f'subtracted weighted averages from {others}')

        # if print_as_table:
        #     from .utils import pretty_print_table
        #     rows.append(row)
        #     pretty_print_table(rows, logger=logger)

        self._build_arrays()
        self._did_adjust_means = True
        if config.return_self:
            return self

    def detrend(self, degree: int=1):
        """
        Detrend the RVs of all instruments using a polynomial of degree `degree`
        """
        instrument_indices = np.unique_inverse(self.instrument_array).inverse_indices
        instrument_indices_masked = np.unique_inverse(self.instrument_array[self.mask]).inverse_indices

        def fun(p, t, degree, ninstruments, just_model=False, index=None, masked=True):
            polyp, offsets = p[:degree], p[-ninstruments:]
            polyp = np.r_[polyp, 0.0]
            if index is None:
                if masked:
                    model = offsets[instrument_indices_masked] + np.polyval(polyp, t)
                else:
                    model = offsets[instrument_indices] + np.polyval(polyp, t)
            else:
                model = offsets[index] + np.polyval(polyp, t)
            if just_model:
                return model
            return self.mvrad - model

        coef = np.polyfit(self.mtime, self.mvrad, degree)
        x0 = np.append(coef, [0.0] * (len(self.instruments) - 1))
        # print(x0)
        fun(x0, self.mtime, degree, len(self.instruments))

        from scipy.optimize import leastsq
        xbest, _ = leastsq(fun, x0, args=(self.mtime, degree, len(self.instruments)))

        fig, ax = self.plot()
        ax.remove()
        ax = fig.add_subplot(2, 1, 1)
        self.plot(ax=ax)
        for i, inst in enumerate(self.instruments):
            s = getattr(self, inst)
            ax.plot(s.time,
                    fun(xbest, s.time, degree, len(self.instruments), just_model=True, index=i, masked=False),
                    color=f'C{i}')
        ax.set_title('original', loc='left', fontsize=10)
        ax.set_title(f'coefficients: {xbest[:degree]}', loc='right', fontsize=10)

        self.add_to_vrad(-fun(xbest, self.time, degree, len(self.instruments), just_model=True, masked=False))
        ax = fig.add_subplot(2, 1, 2)
        self.plot(ax=ax)
        ax.set_title('detrended', loc='left', fontsize=10)

        # axs[0].plot(self.time, fun(xbest, self.time, degree, len(self.instruments), just_model=True))
        # axs[1].errorbar(self.mtime, fun(xbest, self.mtime, degree, len(self.instruments)), self.msvrad, fmt='o')

        return




    def add_to_vrad(self, values):
        """ Add a value or array of values to the RVs of all instruments """
        values = np.atleast_1d(values)
        if values.size == 1:
            values = np.full_like(self.vrad, values)

        masked = False
        if values.size != self.vrad.size:
            if values.size == self.mvrad.size:
                logger.warning('adding to masked RVs only')
                masked = True
            else:
                raise ValueError(f"incompatible sizes: len(values) must equal self.N, got {values.size} != {self.vrad.size}")

        for inst in self.instruments:
            s = getattr(self, inst)
            if masked:
                mask = self.instrument_array[self.mask] == inst
                s.vrad[s.mask] += values[mask]
            else:
                mask = self.instrument_array == inst
                s.vrad += values[mask]
        self._build_arrays()

    def add_to_quantity(self, quantity, values):
        """
        Add a value or array of values to the given quantity of all instruments
        """
        if not hasattr(self, quantity):
            logger.error(f"cannot find '{quantity}' attribute")
            return
        q = getattr(self, quantity)

        values = np.atleast_1d(values)
        if values.size == 1:
            values = np.full_like(q, values)
        if values.size != q.size:
            raise ValueError(f"incompatible sizes: len(values) must equal self.N, got {values.size} != {q.size}")

        for inst in self.instruments:
            s = getattr(self, inst)
            mask = self.instrument_array == inst
            setattr(s, quantity, getattr(s, quantity) + values[mask])
        self._build_arrays()

    def replace_vrad(self, values):
        """ Replace the RVs of all instruments with a value or array of values """
        values = np.atleast_1d(values)
        if values.size == 1:
            values = np.full_like(self.vrad, values)

        masked = False
        if values.size != self.vrad.size:
            if values.size == self.mvrad.size:
                logger.warning('adding to masked RVs only')
                masked = True
            else:
                raise ValueError(f"incompatible sizes: len(values) must equal self.N, got {values.size} != {self.vrad.size}")

        for inst in self.instruments:
            s = getattr(self, inst)
            if masked:
                mask = self.instrument_array[self.mask] == inst
                s.vrad[s.mask] = values[mask]
            else:
                mask = self.instrument_array == inst
                s.vrad = values[mask]
        self._build_arrays()

    def replace_svrad(self, values):
        """ Replace the RV uncertainties of all instruments with a value or array of values """
        values = np.atleast_1d(values)
        if values.size == 1:
            values = np.full_like(self.svrad, values)

        masked = False
        if values.size != self.svrad.size:
            if values.size == self.msvrad.size:
                logger.warning('adding to masked RV uncertainties only')
                masked = True
            else:
                raise ValueError(f"incompatible sizes: len(values) must equal self.N, got {values.size} != {self.svrad.size}")

        for inst in self.instruments:
            s = getattr(self, inst)
            if masked:
                mask = self.instrument_array[self.mask] == inst
                s.svrad[s.mask] = values[mask]
            else:
                mask = self.instrument_array == inst
                s.svrad = values[mask]
        self._build_arrays()

    def replace_quantity(self, quantity, values):
        """ Replace the given quantity of all instruments by a value or array of values """
        if not hasattr(self, quantity):
            logger.error(f"cannot find '{quantity}' attribute")
            return
        q = getattr(self, quantity)

        values = np.atleast_1d(values)
        if values.size == 1:
            values = np.full_like(q, values)
        if values.size != q.size:
            raise ValueError(f"incompatible sizes: len(values) must equal self.N, got {values.size} != {q.size}")

        for inst in self.instruments:
            s = getattr(self, inst)
            mask = self.instrument_array == inst
            setattr(s, quantity, values[mask])
        self._build_arrays()



    def change_units(self, new_units):
        possible = {'m/s': 'm/s', 'km/s': 'km/s', 'ms': 'm/s', 'kms': 'km/s'}
        if new_units not in possible:
            msg = f"new_units must be one of 'm/s', 'km/s', 'ms', 'kms', got '{new_units}'"
            raise ValueError(msg)
        
        new_units = possible[new_units]
        if new_units == self.units:
            return

        if self.verbose:
            logger.info(f"changing units from {self.units} to {new_units}")

        if new_units == 'm/s' and self.units == 'km/s':
            factor = 1e3
        elif new_units == 'km/s' and self.units == 'm/s':
            factor = 1e-3
        
        for inst in self.instruments:
            s = getattr(self, inst)
            s.vrad *= factor
            s.svrad *= factor
            try:
                s.fwhm *= factor
                s.fwhm_err *= factor
            except AttributeError:
                pass

            for q in (
                'bispan',
                'nzp', 'vrad_preNZP',
            ):
                try:
                    setattr(s, q, getattr(s, q) * factor)
                    setattr(s, f'{q}_err', getattr(s, f'{q}_err') * factor)
                except AttributeError:
                    pass

        self._build_arrays()
        self.units = new_units


    def put_at_systemic_velocity(self, factor=1.0, ignore=None):
        """
        For instruments in which mean(RV) < `factor` * ptp(RV), "move" RVs to
        the systemic velocity from simbad. This is useful if some instruments
        are centered at zero while others are not, and instead of calling
        `.adjust_means()`, but it only works when the systemic velocity is
        smaller than `factor` * ptp(RV).
        """
        changed = False
        for inst in self.instruments:
            if ignore is not None:
                if inst in ignore or any([i in inst for i in ignore]):
                    continue
            changed_inst = False
            s = getattr(self, inst)
            if s.mask.any():
                if np.abs(s.mvrad.mean()) < factor * np.ptp(s.mvrad):
                    s.vrad += self.simbad.rvz_radvel * 1e3
                    changed = changed_inst = True
            else:  # all observations are masked, use non-masked arrays
                if np.abs(s.vrad.mean()) < factor * np.ptp(s.vrad):
                    s.vrad += self.simbad.rvz_radvel * 1e3
                    changed = changed_inst = True
            if changed_inst and self.verbose:
                logger.info(f"putting {inst} RVs at systemic velocity")
        if changed:
            self._build_arrays()

    def sort_instruments(self, by_first_observation=True, by_last_observation=False):
        """ Sort instruments by first or last observation date.

        Args:
            by_first_observation (bool, optional):
                Sort by first observation date
            by_last_observation (bool, optional):
                Sort by last observation date
        """
        if by_last_observation:
            by_first_observation = False
        if by_first_observation:
            self.instruments = sorted(self.instruments, key=lambda i: getattr(self, i).time.min())
            self._build_arrays()
        if by_last_observation:
            self.instruments = sorted(self.instruments, key=lambda i: getattr(self, i).time.max())
            self._build_arrays()

    def put_instrument_last(self, instrument):
        if not self._check_instrument(instrument, strict=True, log=True):
            return
        self.instruments = [i for i in self.instruments if i != instrument] + [instrument]
        self._build_arrays()

    def save(self, directory=None, instrument=None, format='rdb',
             indicators=False, join_instruments=False, postfix=None,
             save_masked=False, save_nans=True, **kwargs):
        """ Save the observations in .rdb or .csv files.

        Args:
            directory (str, optional):
                Directory where to save the .rdb files.
            instrument (str, optional):
                Instrument for which to save observations.
            format (str, optional):
                Format to use ('rdb' or 'csv').
            indicators (bool, str, list[str], optional):
                Save only RVs and errors (False) or more indicators. If True,
                use a default list, if `str`, use an existing list, if list[str]
                provide a sequence of specific indicators.
            join_instruments (bool, optional):
                Join all instruments in a single file.
            postfix (str, optional):
                Postfix to add to the filenames ([star]_[instrument]_[postfix].rdb).
            save_masked (bool, optional)
                If True, also save masked observations (those for which
                self.mask == False)
            save_nans (bool, optional)
                Whether to save NaN values in the indicators, if they exist. If
                False, the full observation which contains NaN values is not saved.
        """
        if format not in ('rdb', 'csv'):
            logger.error(f"format must be 'rdb' or 'csv', got '{format}'")
            return

        star_name = self.star.replace(' ', '')

        if directory is not None:
            os.makedirs(directory, exist_ok=True)

        indicator_sets = {
            "default": [
                "fwhm", "fwhm_err",
                "bispan", "bispan_err",
                "contrast", "contrast_err",
                "rhk", "rhk_err",
                "berv",
            ],
            "CORALIE": [
                "fwhm", "fwhm_err",
                "bispan", "bispan_err",
                "contrast", "contrast_err",
                "haindex", "haindex_err",
                "berv",
            ],
        } 

        if 'full' in kwargs:
            logger.warning('argument `full` is deprecated, use `indicators` instead')
            indicators = kwargs['full']

        files = []

        for _i, inst in enumerate(self.instruments):
            if instrument is not None:
                if instrument not in inst:
                    continue

            _s = getattr(self, inst)

            if not _s.mask.any():  # all observations are masked, don't save
                continue

            if save_masked:
                arrays = [_s.time, _s.vrad, _s.svrad]
                if join_instruments:
                    arrays += [_s.instrument_array]
            else:
                arrays = [_s.mtime, _s.mvrad, _s.msvrad]
                if join_instruments:
                    arrays += [_s.instrument_array[_s.mask]]
            
            if indicators in (False, None):
                indicator_names = []
            else:
                if indicators is True:
                    indicator_names = indicator_sets["default"]
                elif isinstance(indicators, str):
                    try:
                        indicator_names = indicator_sets[indicators]
                    except KeyError:
                        logger.error(f"unknown indicator set '{indicators}'")
                        logger.error(f"available: {list(indicator_sets.keys())}")
                        return
                elif isinstance(indicators, list) and all(isinstance(i, str) for i in indicators):
                    indicator_names = indicators

            if save_masked:
                arrays += [getattr(_s, ind) for ind in indicator_names]
            else:
                arrays += [getattr(_s, ind)[_s.mask] for ind in indicator_names]

            d = np.stack(arrays, axis=1)
            if not save_nans:
                # raise NotImplementedError
                if np.isnan(d).any():
                    # remove observations where any of the indicators are # NaN
                    nan_mask = np.isnan(d[:, 3:]).any(axis=1)
                    d = d[~nan_mask]
                    if self.verbose:
                        msg = f'{inst}: masking {nan_mask.sum()} observations with NaN in indicators'
                        logger.warning(msg)

            cols = ['rjd', 'vrad', 'svrad']
            cols += ['inst'] if join_instruments else []
            cols += indicator_names

            if format == 'rdb':
                header = '\t'.join(cols)
                header += '\n'
                header += '\t'.join(['-' * len(c) for c in header.strip().split('\t')])
            else:
                header = ','.join(cols)

            if join_instruments:
                file = f'{star_name}.{format}'
                if postfix is not None:
                    file = f'{star_name}_{postfix}.{format}'
            else:
                file = f'{star_name}_{inst}.{format}'
                if postfix is not None:
                    file = f'{star_name}_{inst}_{postfix}.{format}'

            if directory is not None:
                file = os.path.join(directory, file)
            files.append(file)

            N = len(arrays[0])
            with open(file, 'a' if join_instruments and _i != 0 else 'w') as f:
                if join_instruments and _i != 0:
                    pass
                else:
                    f.write(header + '\n')

                for i in range(N):
                    for j, a in enumerate(arrays):
                        f.write(str(a[i]))
                        if j < len(arrays) - 1:
                            f.write('\t' if format == 'rdb' else ',')
                    f.write('\n')

            # np.savetxt(file, d, header=header, delimiter='\t', comments='', fmt='%f')

            if self.verbose and not join_instruments:
                logger.info(f'saving to {file}')

        if self.verbose and join_instruments:
            logger.info(f'saving to {files[0]}')

        if join_instruments:
            files = [files[0]]

        return files

    def checksum(self, write_to=None):
        """ Calculate a hash based on the data """
        from hashlib import md5
        d = np.r_[self.time, self.vrad, self.svrad]
        H = md5(d.data.tobytes()).hexdigest()
        if write_to is not None:
            with open(write_to, 'w') as f:
                f.write(H)
        return H


    #
    def run_lbl(self, instrument=None, data_dir=None,
                skysub=False, tell=False, limit=None, **kwargs):
        from .lbl_wrapper import run_lbl, NIRPS_create_telluric_corrected_S2D

        if instrument is None:
            instruments = self.instruments
        else:
            if instrument not in self.instruments:
                if any([instrument in i for i in self.instruments]):
                    instrument = [i for i in self.instruments if instrument in i]
                else:
                    logger.error(f"No data from instrument '{instrument}'")
                    logger.info(f'available: {self.instruments}')
                    return

            if isinstance(instrument, str):
                instruments = [instrument]
            else:
                instruments = instrument

        for instrument in instruments:
            if self.verbose:
                logger.info(f'gathering files for {instrument}')
            files = getattr(self, instrument).raw_file
            files = map(os.path.basename, files)
            if skysub:
                files = [file.replace('.fits', '_S2D_SKYSUB_A.fits') for file in files]
            else:
                files = [file.replace('.fits', '_S2D_A.fits') for file in files]

            if data_dir is None:
                data_dir = f'{self.star}_downloads'

            files = [os.path.join(data_dir, file) for file in files]
            exist = [os.path.exists(file) for file in files]
            if not all(exist):
                logger.error(f"not all required files exist in {data_dir}")
                logger.error(f"missing {np.logical_not(exist).sum()} / {len(files)}")

                go_on = input('continue? (y/N) ')
                if go_on == '' or not bool(strtobool(go_on)):
                    return

                files = list(np.array(files)[exist])

            # deal with NIRPS telluric correction
            if 'NIRPS' in instrument and tell:
                if self.verbose:
                    logger.info('creating telluric-corrected S2D files')
                files = NIRPS_create_telluric_corrected_S2D(files[:limit])

            run_lbl(self, instrument, files[:limit], **kwargs)

    def load_lbl(self, instrument=None, tell=False, id=None):
        if hasattr(self, '_did_load_lbl') and self._did_load_lbl: # don't do it twice
            return

        from .lbl_wrapper import load_lbl

        if instrument is None:
            instruments = self.instruments
        else:
            if instrument not in self.instruments:
                if any([instrument in i for i in self.instruments]):
                    instrument = [i for i in self.instruments if instrument in i]
                else:
                    logger.error(f"No data from instrument '{instrument}'")
                    logger.info(f'available: {self.instruments}')
                    return

            if isinstance(instrument, str):
                instruments = [instrument]
            else:
                instruments = instrument

        for inst in instruments:
            if self.verbose:
                logger.info(f'loading LBL data for {inst}')

            load_lbl(self, inst, tell=tell, id=id)
            # self.instruments.append(f'{inst}_LBL')

        # self._build_arrays()
        self._did_load_lbl = True


    #
    from .stellar import calc_prot_age

    @property
    def HZ(self):
        if not hasattr(self, 'star_mass'):
            self.star_mass = float(input('stellar mass (Msun): '))
        if not hasattr(self, 'lum'):
            self.lum = float(input('luminosity (Lsun): '))
        if hasattr(self, 'teff'):
            teff = self.teff
        else:
            teff = self.simbad.teff
        return getHZ_period(teff, self.star_mass, 1.0, self.lum)


    @property
    def planets(self):
        """ Query the NASA Exoplanet Archive for any known planets """
        from .nasaexo_wrapper import Planets
        if not hasattr(self, '_planets'):
            self._planets = Planets(self)
        return self._planets


def fit_sine(t, y, yerr=None, period='gls', fix_period=False):
    """ Fit a sine curve of the form y = A * sin(2π * t / P + φ) + c

    Args:
        t (ndarray):
            Time array
        y (ndarray):
            Array of observed values
        yerr (ndarray, optional):
            Array of uncertainties. Defaults to None.
        period (str or float, optional):
            Initial guess for period or 'gls' to get it from Lomb-Scargle
            periodogram. Defaults to 'gls'.
        fix_period (bool, optional):
            Whether to fix the period. Defaults to False.

    Returns:
        p (ndarray):
            Best-fit parameters [A, P, φ, c] or [A, φ, c]
        f (callable):
            Function that returns the best-fit sine curve for input times
    """
    from scipy.optimize import leastsq
    if period == 'gls':
        from astropy.timeseries import LombScargle
        gls = LombScargle(t, y, yerr)
        freq, power = gls.autopower()
        period = 1 / freq[power.argmax()]
    else:
        period = float(period)

    if yerr is None:
        yerr = np.ones_like(y)

    if fix_period:
        def sine(t, p):
            return p[0] * np.sin(2 * np.pi * t / period + p[1]) + p[2]
        p0 = [np.ptp(y), 0.0, 0.0]
    else:
        def sine(t, p):
            return p[0] * np.sin(2 * np.pi * t / p[1] + p[2]) + p[3]
        p0 = [np.ptp(y), period, 0.0, 0.0]

    xbest, _ = leastsq(lambda p, t, y, ye: (sine(t, p) - y) / ye, p0,
                       args=(t, y, yerr))
    return xbest, partial(sine, p=xbest)


def fit_n_sines(t, y, yerr=None, n=1, period='gls', fix_period=False):
    """ Fit N sine curves of the form y = ∑i Ai * sin(2π * t / Pi + φi) + c

    Args:
        t (ndarray):
            Time array
        y (ndarray):
            Array of observed values
        yerr (ndarray, optional):
            Array of uncertainties. Defaults to None.
        n (int, optional):
            Number of sine curves to fit. Defaults to 1.
        period (str or float, optional):
            Initial guess for periods or 'gls' to get them from Lomb-Scargle
            periodogram. Defaults to 'gls'.
        fix_period (bool, optional):
            Whether to fix the periods. Defaults to False.

    Returns:
        p (ndarray):
            Best-fit parameters [A, P, φ, c] or [A, φ, c] for each sine curve
        f (callable):
            Function that returns the best-fit curve for input times
    """
    from scipy.optimize import leastsq
    if period == 'gls':
        from astropy.timeseries import LombScargle
        # first period guess
        gls = LombScargle(t, y, yerr)
        freq, power = gls.autopower()
        period = [1 / freq[power.argmax()]]
        yc = y.copy()
        for i in range(1, n):
            p, f = fit_sine(t, y, yerr, period=period[i-1], fix_period=True)
            yc -= f(t)
            gls = LombScargle(t, yc, yerr)
            freq, power = gls.autopower()
            period.append(1 / freq[power.argmax()])
    else:
        assert len(period) == n, f'wrong number of periods, expected {n} but got {len(period)}'

    if yerr is None:
        yerr = np.ones_like(y)

    if fix_period:
        def sine(t, p):
            return p[-1] + np.sum([p[2*i] * np.sin(2 * np.pi * t / period[i] + p[2*i+1]) for i in range(n)], axis=0)
        f = lambda p, t, y, ye: (sine(t, p) - y) / ye
        p0 = [y.std(), 0.0] * n + [y.mean()]
    else:
        def sine(t, p):
            return p[-1] + np.sum([p[3*i] * np.sin(2 * np.pi * t / p[3*i+1] + p[3*i+2]) for i in range(n)], axis=0)
        f = lambda p, t, y, ye: (sine(t, p) - y) / ye
        p0 = np.r_[np.insert([y.std(), 0.0] * n, np.arange(1, 2*n, n), period), y.mean()]

    xbest, _ = leastsq(f, p0, args=(t, y, yerr))
    return xbest, partial(sine, p=xbest)