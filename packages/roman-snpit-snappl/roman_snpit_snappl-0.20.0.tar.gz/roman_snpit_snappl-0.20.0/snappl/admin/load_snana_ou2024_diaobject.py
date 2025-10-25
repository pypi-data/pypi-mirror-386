import re
import uuid
import simplejson
import pathlib
import functools
import argparse
import multiprocessing

import pandas

from snappl.logger import SNLogger
from snappl.utils import SNPITJsonEncoder
import snappl.db.db


def load_snana_ou2024_diaobject( provid, pqf, logevery=10000, dbcon=None ):
    match = re.search( r'^snana_([0-9]+)\.parquet$', pqf.name )
    if match is None:
        raise ValueError( f"Failed to parse filename {match}" )
    healpix = int( match.group(1) )
    df = pandas.read_parquet( pqf )

    thingstoinsert = []
    for n, row in enumerate( df.itertuples() ):
        if n % logevery == 0:
            SNLogger.info( f"File {pqf.name}, {n} of {len(df)} done" )

        params = { k: v for k, v in zip( row.model_param_names, row.model_param_values ) }

        subdict = { 'id':  uuid.uuid4(),
                    'provenance_id': provid,
                    'name': str(row.id),
                    'iauname': None,
                    'ra': float(row.ra),
                    'dec': float(row.dec),
                    'mjd_discovery': float(row.start_mjd),
                    'mjd_peak': float(row.peak_mjd),
                    'mjd_start': float(row.start_mjd),
                    'mjd_end': float(row.end_mjd),
                    'ndetected': 2,
                    'properties': simplejson.dumps(
                        { 'healpix': healpix,
                          'host_id': int(row.host_id),
                          'gentype': int(row.gentype),
                          'model_name': row.model_name,
                          'z_cmb': float(row.z_CMB),
                          'mw_ebv': float(row.mw_EBV),
                          'mw_extinction_applied': float(row.mw_extinction_applied),
                          'av': float(row.AV),
                          'rv': float(row.RV),
                          'v_pec': float(row.v_pec),
                          'host_ra': float(row.host_ra),
                          'host_dec': float(row.host_dec),
                          'host_mag_g': float(row.host_mag_g),
                          'host_mag_i': float(row.host_mag_i),
                          'host_mag_f': float(row.host_mag_F),
                          'host_sn_sep': float(row.host_sn_sep),
                          'peak_mjd': float(row.peak_mjd),
                          'peak_mag_g': float(row.peak_mag_g),
                          'peak_mag_i': float(row.peak_mag_i),
                          'peak_mag_f': float(row.peak_mag_F),
                          'lens_dmu': float(row.lens_dmu),
                          'lens_dmu_applied': bool(row.lens_dmu_applied),
                          'model_params': params },
                        sort_keys=True,
                        cls=SNPITJsonEncoder )
                   }
        thingstoinsert.append( subdict )

    snappl.db.db.DiaObject.bulk_insert_or_upsert( thingstoinsert, dbcon=dbcon )

    return len( thingstoinsert )


def main():
    parser = argparse.ArgumentParser( 'load_snana_ou2024_diaobject',
                                      description='Load all parquet files below a directory.' )
    parser.add_argument( '-p', '--provid', required=True, help="Provenance id" )
    parser.add_argument( '-n', '--nprocs', type=int, default=12,
                         help="Number of processes to run at once [default: 12]" )
    parser.add_argument( 'basedir', help='Base directory.' )
    args = parser.parse_args()

    with snappl.db.db.DBCon( dictcursor=True ) as dbcon:
        rows = dbcon.execute( "SELECT * FROM provenance WHERE id=%(id)s", { 'id': args.provid } )
        if len(rows) == 0:
            raise ValueError( "Invalid provenance {args.provid}" )
        SNLogger.info( f"Loading provenance for process {rows[0]['process']} {rows[0]['major']}.{rows[0]['minor']}" )

    # First, collect all the parquet files

    def find_pqfiles( direc ):
        pqfiles = []
        subdirs = []
        for f in direc.iterdir():
            f = f.resolve()
            if ( f.name[:5] == 'snana') and ( f.name[-8:] == '.parquet' ):
                pqfiles.append( f )
            elif f.is_dir():
                subdirs.append( f )

        for subdir in subdirs:
            pqfiles.extend( find_pqfiles( subdir ) )

        return pqfiles

    basedir = pathlib.Path( args.basedir )
    pqfiles = find_pqfiles( basedir )
    SNLogger.info( f"{len(pqfiles)} parquet files to load" )
    SNLogger.debug( f"All pqfiles we're going to do: {pqfiles}" )

    # Launch parallel processes to load these files

    did = []
    tot = 0

    def add_to_did( n ):
        nonlocal tot, did
        tot += n
        did.append( n )
        SNLogger.info( f"Completed {len(did)} of {len(pqfiles)} parquet files ({tot} objects)" )

    errors = []

    def omg( e ):
        nonlocal errors
        SNLogger.error( f"Subprocess returned error: {e}" )
        errors.append( e )

    do_load = functools.partial( load_snana_ou2024_diaobject, [ args.provid ] )

    with multiprocessing.Pool( args.nprocs ) as pool:
        for pqf in pqfiles:
            pool.apply_async( do_load, [ pqf ], callback=add_to_did, error_callback=omg )
        pool.close()
        pool.join()

    if len(errors) > 0:
        nl = '\n'
        SNLogger.error( f"There were errors:\n{nl.join(str(e) for e in errors)}" )
        raise RuntimeError( "There were errors!" )

    SNLogger.info( f"Loaded {tot} objects in {len(did)} parquet files." )


# ======================================================================
if __name__ == "__main__":
    main()
