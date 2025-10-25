__all__ = [ 'ImageCollection', 'ImageCollectionOU2024', 'ImageCollectionManualFITS', 'ImageCollectionDB' ]

import pathlib

import simplejson

from snappl.config import Config
from snappl.http import retry_post
from snappl.image import OpenUniverse2024FITSImage, FITSImage, FITSImageStdHeaders
from snappl.provenance import Provenance
from snappl.dbclient import SNPITDBClient
from snappl.utils import asUUID, SNPITJsonEncoder


class ImageCollection:
    """A class that keeps track of groups of images.

    Never instantiate an object of this class of its subclasses
    directly.  Call the get_collection() class method go get your image
    collection.

    Available properties include:

    base_path : pathlib.Path ; image paths are relative to this absolute path.

    """

    @classmethod
    def get_collection( cls, collection='snpitdb', subset=None,
                        provenance_tag=None, process=None, provenance=None,
                        dbclient=None, **kwargs ):
        """Get an ImageCollection object.

        Parameters
        ----------
          collection : str
            Name of the collection.  Currently defined collections:
            * ou2024 - Open Universe 2024 FITS images
            * manual_fits - FITS images that aren't really part of a collection
            * snpitdb - Images from Roman SNPIT internal DB.

          subset : str or None
            Name of the subset, if relevant for that collection.
              * manual_fits
                 * (None) - a single FITS file on disk
                 * "threefile" - follows the convention of snappl.image.FITSImageStdHeaders
                                 and std_imagenames=True passed to the constructor

          provenance_tag : str, defanot None
            The Roman SNPIT internal database provenance tag for the
            provenance of the images.  Either provenance_tag or
            provenance is required when collection is 'snpitdb'.
            Invalid if collection is not 'snpitdb'.

          process : str, default None
            The process to go with provenance_tag; required when
            provenance_tag is not None.

          provenance : Provenance or UUID or str, default None
            The Roman SNPIT internal database Provenance or provenance
            id for the images.  Either provenance_tag or provenance is
            required when collection is 'snpitdb'.  Invalid if
            collection is not 'snpitdb'.

          dbclient : SNPITDBClient, default None
            Only needed if collection is 'snpit'.  If None, a new one
            will be made when needed.

          **kwargs : Some collections types require additional arguments.

        """
        if collection == 'snpitdb':
            dbclient = SNPITDBClient() if dbclient is None else dbclient
            if ( provenance is None ) and ( provenance_tag is None ):
                raise ValueError( 'Collection snpitdb requires either provenance_tag or provenance' )
            if ( provenance_tag is None ) != ( process is None ):
                raise ValueError( 'Must specify either both or neither or provenance_tag and process' )

            if provenance is None:
                provenance = Provenance.get_provs_for_tag( provenance_tag, process=process, dbclient=dbclient )
            if not isinstance( provenance, Provenance ):
                provenance = Provenance.get_by_id( provenance, dbclient=dbclient )

            return ImageCollectionDB( provenance=provenance, **kwargs )

        # If we get here, we know collection isn't 'snpitdb'

        if any( i is not None for i in [ provenance_tag, process, provenance ] ):
            raise ValueError( "provenance_tag, process, and provenance are only valid for collection snpitdb" )

        if collection == 'ou2024':
            return ImageCollectionOU2024( **kwargs )

        elif collection == 'manual_fits':
            if subset is None:
                return ImageCollectionManualFITS( **kwargs )
            elif subset == "threefile":
                return ImageCollectionManualFITS( threefile=True, **kwargs )
            else:
                raise ValueError( f"Unknown subset {subset} of manual_fits" )

        else:
            raise ValueError( f"Unknown image collection {collection} (subset {subset})" )

    def get_image( self, image_id=None, path=None, pointing=None, band=None, sca=None, dbclient=None ):
        """Return an object of a subclass of Image based on input parameters.

        You can specify an image by:
          * image_id  (for collections that point to the internal Roman SNPIT database)
          * path
          * pointing, band, and sca

        Parameters
        ----------
          image_id : UUID or str, default None
            The id of the image you want to get.  This is only relevant
            for image collections that refer to images in the internal
            Roman SNPIT database, otherwise it is invalid.  If image_id
            is given, then path, pointing, band, and sca are all ignored.

          path: Path or str, default None
            The path to the relative to base_path.  For some subclasses,
            this must be consistent wiht pointing, band, and sca if passed.

          pointing: str, default None
            Pointing.  If not given, just use the Path to find the image.

          band: str, default None
            Band.

          sca: int, default None
            SCA.

          base_path: str or pathlib.Path, default None
            The base path for the image collection.  If not given, use
            the default for the collection from when the collection
            object was instantiated.

          dbclient : SNPITDBClient, default None
            Only relevant for image collections that refer to the
            internal SNPIT database.  If None, a new connection will be
            made if needed.

        Returns
        -------
          image: Image

        """
        raise NotImplementedError( f"get_image not implemented for f{self.__class__.__name__}" )


    def get_image_path( self, pointing, band, sca, base_path=None ):
        """Return the absolute path to the desired image, if that makes sense.

        This will only make sense for image collections where an image
        is uniquely defined by a pointing, band, and sca.  Other image
        collections will just not implement this method.

        Parameters
        ----------
          pointing: str
            The pointing number

          band : str
            The band

          sca: int
            The SCA

          base_path : str or Path, default None
            If None, use the default value for this collection

        Returns
        -------
          pathlib.Path

        """
        raise NotImplementedError( f"{self.__class__.__name__} doesn't implement get_image_path" )


    def find_images( self, **kwargs ):
        """Find images.

        Parameters
        ----------
          path: pathlib.Path or str, default None
            Relative path of the image to search for.  Usually if you
            feed it this, you don't want to feed it nay other
            parameters.

          mjd_min : float, default None
            Only return images at this mjd or later

          mjd_max : float, default None
            Only return images at this mjd or earlier.

          ra: float, default None
            Only return images that contain this ra

          dec: float, default None
            Only return images that containe this dec

          band: str, default None
            Only include images from this band

          exptime_min: float, default None
            Only include images with at least this exptime in seconds.

          exptime_max: float, default None
            Only include images with at most this exptime in seconds.

          sca: int
            Only include images from this sca.

          order_by: str or list, default None
            By default, the returned images are not sorted in any
            particular way.  Put a keyword here to sort by that value
            (or by those values).  Options include 'id',
            'provenance_id', 'pointing', 'sca', 'ra', 'dec', 'filepath',
            'width', 'height', 'mjd', 'exptime'.  Not all of these are
            necessarily useful, and some of them may be null for many
            objects in the database.

          limit : int, default None
            Only return this many objects at most.

          offset : int, default None
            Useful with limit and order_by ; offset the returned value
            by this many entries.  You can make repeated calls to
            find_objects to get subsets of objects by passing the same
            order_by and limit, but different offsets each time, to
            slowly build up a list.

        Returns
        -------
          imagelist: list of snappl.image.Image
            Really it will be list of objects of a subclass of
            snappl.image.Image, but you shouldn't need to know that.

        """
        raise NotImplementedError( f"{self.__class__.__name__} needs to implement find_images" )


class ImageCollectionOU2024:
    """Collection of OpenUnivers 2024 FITS images."""

    def __init__( self, base_path=None ):
        self._base_path = None if base_path is None else pathlib.Path( base_path )

    @property
    def base_path( self ):
        if self._base_path is None:
            self._base_path = pathlib.Path( Config.get().value( 'system.ou24.images' ) )
        return self._base_path

    def get_image( self, image_id=None, path=None, pointing=None, band=None, sca=None, base_path=None, dbclient=None ):
        """Return a OpenUniverse2024FITSImage based on specifications.

        If you specify all of path, pointing, band, and sca, they must
        be consistent.

        If you just give path, then pointing, band, and sca will be read
        from the header.

        If you give pointinb, band, and sca, but not path, it will use
        get_image_path to find the image.

        """

        if image_id is not None:
            raise ValueError( "image_id is invalid for ImageCollectionOU2024" )

        base_path = self.base_path if base_path is None else pathlib.Path( base_path )
        if path is not None:
            img = OpenUniverse2024FITSImage( base_path / path )
            if ( pointing is not None ) and ( int(pointing) != int(img.pointing) ):
                raise ValueError( "Pointing {pointing} inconsistent with what's in {path}" )
            if ( sca is not None ) and ( int(sca) != int(img.sca) ):
                raise ValueError( "SCA {sca} inconsistent with what's in {path}" )
            if ( band is not None ) and ( str(band) != str(img.band) ):
                raise ValueError( "Band {band} inconsistent with what's in {path}" )
            return img

        if any( i is None for i in [ pointing, band, sca ] ):
            raise ValueError( "Must specify either path or all of (pointing, band, sca)" )

        path = self.get_image_path( pointing, band, sca, base_path=base_path )
        img = OpenUniverse2024FITSImage( path, pointing=pointing, sca=sca )
        return img


    def get_image_path( self, pointing, band, sca, base_path=None ):
        """Return the absolute path to the desired OU2024 FITS image.

        See ImageCollection.get_image_path for documentation.

        """
        base_path = self.base_path if base_path is None else pathlib.Path( base_path )
        path = ( base_path / band / str(pointing) /
                 f'Roman_TDS_simple_model_{band}_{str(pointing)}_{str(sca)}.fits.gz' )
        return path

    def find_images( self,
                      subset=None,
                      path=None,
                      mjd_min=None,
                      mjd_max=None,
                      ra=None,
                      dec=None,
                      band=None,
                      exptime_min=None,
                      exptime_max=None,
                      sca=None ):
        params = {}

        if ( ra is None ) != ( dec is None ):
            raise ValueError( "Specify either both or neither of ra and dec" )

        if ra is not None:
            params['containing'] = ( float(ra), float(dec) )

        if mjd_min is not None:
            params['mjd_min'] = float(mjd_min)
        if mjd_max is not None:
            params['mjd_max'] = float(mjd_max)
        if band is not None:
            params['filter'] = str(band)
        if exptime_min is not None:
            params['exptime_min'] = float(exptime_min)
        if exptime_max is not None:
            params['exptime_max'] = float(exptime_max)

        simdex = Config.get().value( 'system.ou24.simdex_server' )
        res = retry_post( f"{simdex}/findromanimages", json=params ).json()

        images = []
        for i in range( len(res['pointing']) ):
            path = self.get_image_path( res['pointing'][i], res['filter'][i], res['sca'][i] )
            image = OpenUniverse2024FITSImage(path, None, res["sca"][i])
            image.mjd = res['mjd'][i]
            images.append( image )


        return images



class ImageCollectionManualFITS:
    """Manually specified custom images.

    One version of this (constructed with threefile=True) assumes that
    there are three files associated with an image whose path is given
    as {path}::

       {path}_image.fits
       {path}_noise.fits
       {path}_flags.fits

    In addition, the threefile version assumes that the following header
    keywords all exist in the header of the _image.fits file::

      BAND
      EXPTIME
      MJD
      POINTING
      SCA
      ZPT

    (in addition to a WCS in the _image.fits header).

    """

    def __init__( self, base_path=None, threefile=False ):
        if base_path is None:
            raise RuntimeError( "manual_fits collection needs a base path" )
        self.base_path = pathlib.Path( base_path )
        self.threefile = threefile

    def get_image_path( self, pointing, band, sca, base_path=None ):
        raise NotImplementedError( "get_image_path is not defined for ImageCollectionManualFITS" )

    def find_images( self, **kwargs ):
        raise NotImplementedError( "find_images is not defined for ImageCollectionManualFITS" )

    def get_image( self, image_id=None, path=None, pointing=None, band=None, sca=None, base_path=None, dbclient=None ):
        if image_id is not None:
            raise ValueError( "image_id is invalid for ImageCollectionManualFITS" )

        if path is None:
            raise ValueError( "ImageCollectionManualFITS.get_image requires a path, it can't "
                              "handle pointing/band/sca." )

        base_path = pathlib.Path(base_path) if base_path is not None else self.base_path
        if self.threefile:
            return FITSImageStdHeaders( path=base_path / path, std_imagenames=True )

        else:
            return FITSImage( path=path )


# ======================================================================
# Images that are in the Roman SNPIT Database

class ImageCollectionDB:
    image_class_dict = { 'ou2024': OpenUniverse2024FITSImage }
    base_path_dict = { 'ou2024': 'system.ou24.images' }

    def __init__( self, provenance=None, base_path=None ):
        if provenance is None:
            raise ValueError( "provenance is required" )
        self.provenance = provenance

        prov_imclass = self.provenance.params['image_class']
        if prov_imclass not in self.image_class_dict:
            raise RuntimeError( "Unknown image_class {image_class}" )
        self.image_class = self.image_class_dict[ prov_imclass ]

        if base_path is None:
            base_path = Config.get().value( self.base_path_dict[ prov_imclass ] )
        self.base_path = pathlib.Path( base_path )


    def get_image( self, image_id=None, path=None, pointing=None, band=None, sca=None, dbclient=None ):
        dbclient = SNPITDBClient() if dbclient is None else dbclient

        if image_id is not None:
            row = dbclient.send( f"/getl2image/{image_id}" )
            if asUUID(row['provenance_id']) != self.provenance.id:
                raise ValueError( f"Asked for image {image_id} in provenance {self.provenance.id}, but that image "
                                  f"actually has provenance {row['provenance_id']}" )

        else:
            if not ( ( path is not None ) or
                     ( all( i is not None for i in [ pointing, band, sca ] ) ) ):
                raise ValueError( "Must specify one of image_id, path, or (pointing, band, and sca)." )

            data = { k: v for k, v in zip( ['filepath', 'pointing', 'band', 'sca' ],
                                           [path, pointing, band, sca ] )
                     if v is not None }
            rows = dbclient.send( f"/findl2images/{self.provenance.id}",
                                  data=simplejson.dumps( data, cls=SNPITJsonEncoder ),
                                  headers={'Content-Type': 'application/json'} )
            if len(rows) == 0:
                raise RuntimeError( f"Image not found for provenance {self.provenance.id} and {data}" )
            elif len(rows) > 1:
                raise RuntimeError( f"Multiple images found for provenance {self.provenance.id} and {data}" )

            row = rows[0]

        row['path'] = self.base_path / row['filepath']
        return self.image_class( **row )


    def get_image_path( self, pointing, band, sca, base_path=None, image_id=None ):
        raise NotImplementedError( "Not implemented yet, may not be..." )


    def find_images( self, dbclient=None, **kwargs ):
        dbclient = SNPITDBClient() if dbclient is None else dbclient
        rows = dbclient.send( f'findl2images/{self.provenance.id}',
                              data=simplejson.dumps( kwargs, cls=SNPITJsonEncoder ),
                              headers={'Content-Type': 'application/json'} )

        images = []
        for row in rows:
            row['path'] = self.base_path / row['filepath']
            row['band'] = row['band']
            images.append( self.image_class( **row ) )

        return images
