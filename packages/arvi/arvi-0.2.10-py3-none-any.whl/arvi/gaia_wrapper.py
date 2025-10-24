import os
from io import StringIO
from csv import DictReader
import requests

DATA_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(DATA_PATH, 'data')

QUERY = """
SELECT TOP 20 gaia_source.designation, gaia_source.source_id,
              gaia_source.ra, gaia_source.dec, 
              gaia_source.parallax, gaia_source.pmra, gaia_source.pmdec,
              gaia_source.ruwe, gaia_source.phot_g_mean_mag, gaia_source.bp_rp, 
              gaia_source.radial_velocity, gaia_source.radial_velocity_error
FROM gaiadr3.gaia_source 
WHERE 
CONTAINS(
	POINT('ICRS',gaiadr3.gaia_source.ra,gaiadr3.gaia_source.dec),
	CIRCLE(
		'ICRS',
		COORD1(EPOCH_PROP_POS({ra},{dec},{plx},{pmra},{pmdec},{rv},2000,2016.0)),
		COORD2(EPOCH_PROP_POS({ra},{dec},{plx},{pmra},{pmdec},{rv},2000,2016.0)),
		0.001388888888888889)
)=1
"""

QUERY_ID = """
SELECT TOP 20 gaia_source.designation, gaia_source.source_id,
              gaia_source.ra, gaia_source.dec, 
              gaia_source.parallax, gaia_source.pmra, gaia_source.pmdec,
              gaia_source.ruwe, gaia_source.phot_g_mean_mag, gaia_source.bp_rp, 
              gaia_source.radial_velocity, gaia_source.radial_velocity_error
FROM gaiadr3.gaia_source 
WHERE 
gaia_source.source_id = {id}
"""

translate = {
    'Proxima': '5853498713190525696',
    'GJ699': '4472832130942575872',
    'LS II +14 13': '4318465066420528000',
}


def run_query(query):
    url = 'https://gea.esac.esa.int/tap-server/tap/sync'
    data = dict(query=query, request='doQuery', lang='ADQL', format='csv')
    try:
        response = requests.post(url, data=data, timeout=2)
    except requests.ReadTimeout as err:
        raise IndexError(err)
    except requests.ConnectionError as err:
        raise IndexError(err)
    return response.content.decode()

def parse_csv(csv):
    reader = DictReader(StringIO(csv))
    return list(reader)


class gaia:
    """
    A very simple wrapper around a TAP query to gaia for a given target. This
    class simply runs a few TAP queries and stores the result as attributes.

    Attributes:
        ra (float): right ascension
        dec (float): declination
        coords (SkyCoord): coordinates as a SkyCoord object
        dr3_id (int): Gaia DR3 identifier
        plx (float): parallax
        radial_velocity (float): radial velocity
    """
    def __init__(self, star:str, simbad=None, _debug=False):
        """
        Args:
            star (str): The name of the star to query simbad
        """
        from astropy.coordinates import SkyCoord

        self.star = star

        if simbad is None:
            from .simbad_wrapper import simbad as Simbad
            simbad = Simbad(star)
            if _debug:
                print(simbad)

        ra = simbad.ra
        dec = simbad.dec
        plx = simbad.plx
        pmra = simbad.pmra
        pmdec = simbad.pmdec
        rv = simbad.rvz_radvel
        args = dict(ra=ra, dec=dec, plx=plx, pmra=pmra, pmdec=pmdec, rv=rv) 

        try:
            if star in translate:
                table = run_query(query=QUERY_ID.format(id=translate[star]))
            elif hasattr(simbad, 'gaia_id') and simbad.gaia_id is not None:
                table = run_query(query=QUERY_ID.format(id=simbad.gaia_id))
            else:
                table = run_query(query=QUERY.format(**args))
            
            if _debug:
                print('table:', table)

            results = parse_csv(table)[0]
        except IndexError:
            raise ValueError(f'Gaia query for {star} failed')
        
        try:
            self.dr3_id = int(results['source_id'])
        except KeyError:
            raise ValueError(f'Gaia query for {star} failed')

        self.ra = float(results['ra'])
        self.dec = float(results['dec'])
        self.pmra = float(results['pmra'])
        self.pmdec = float(results['pmdec'])
        self.coords = SkyCoord(self.ra, self.dec, unit='deg')
        self.plx = float(results['parallax'])
        try:
            self.radial_velocity = float(results['radial_velocity'])
        except ValueError:
            self.radial_velocity = None
        try:
            self.radial_velocity_error = float(results['radial_velocity_error'])
        except ValueError:
            self.radial_velocity_error = None

        return

    def __repr__(self):
        return f'{self.star} (DR3 id={self.dr3_id})'
