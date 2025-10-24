# Project Librarian: Brandon Piotrzkowski
#              Staff Scientist
#              UW-Milwaukee Department of Physics
#              Center for Gravitation & Cosmology
#              <brandon.piotrzkowski@ligo.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Module containing time- and sky- coincidence search functions.
"""
__author__ = "Alex Urban <alexander.urban@ligo.org>"


# Imports.
import json
import re
import sys

from astropy import units as u
from astropy.coordinates import SkyCoord
import astropy_healpix as ah
import healpy as hp
import numpy as np

from .gracedb_events import SE, ExtTrig, _is_gracedb_sdk, _get_gracedb_url
from ligo.gracedb.rest import GraceDb


#########################################################
# Functions implementing the actual coincidence search. #
#########################################################

def query(event_type, gpstime, tl, th, gracedb=None, group=None,
          pipelines=[], searches=[], se_searches=[]):
    """ Query for coincident events of type event_type occurring within a
        window of [tl, th] seconds around gpstime.

    Parameters
    ----------
    event_type: str
        "Superevent" or "External"
    gpstime: float
        Event's gps time
    tl: float
        Start of coincident time window
    th: float
        End of coincident time window
    gracedb: class
        SDK or REST API client for HTTP connection
    group: str
        "CBC", "Burst", or "Test",
    pipelines: list
        List of external trigger pipeline names
    searches: array
        List of external trigger searches
    se_searches: array
        List of superevent searches
    """

    # Perform a sanity check on the time window.
    if tl >= th:
        sys.stderr.write("ERROR: The time window [tl, th] must have tl < th.")
        sys.exit(1)

    # Catch potential error if pipelines or searches are None
    if not pipelines:
        pipelines = []
    # FIXME: Rename searches to ext_searches and depreciate searches field
    if not searches:
        searches = []
    if not se_searches:
        se_searches = []

    # Initiate instance of GraceDb if not given.
    if gracedb is None:
        gracedb = GraceDb()
    is_gracedb_sdk = _is_gracedb_sdk(gracedb)

    # Perform the GraceDB query.
    start, end = gpstime + tl, gpstime + th

    if event_type == 'External':  # Searching for external events
        arg = (f"{event_type} {start} .. {end}"
               f"{' MDC' if 'MDC' in searches else ''}")
        # Return list of graceids of coincident events.
        if is_gracedb_sdk:
            results = list(gracedb.events.search(query=arg))
        else:
            results = list(gracedb.events(arg))

        if pipelines:
            results = [event for event in results if event['pipeline']
                       in pipelines]
        if searches:
            results = [event for event in results if
                       event['search'] in searches]
        return results

    elif event_type == 'Superevent':  # Searching for superevents
        arg = f"{start} .. {end}{' MDC' if 'MDC' in se_searches else ''}"
        # Return list of coincident superevent_ids.
        if is_gracedb_sdk:
            results = list(gracedb.superevents.search(query=arg))
        else:
            results = list(gracedb.superevents(arg))
        if group:
            results = [superevent for superevent in results if
                       superevent['preferred_event_data']['group'] == group]
        if se_searches:
            results = [superevent for superevent in results if
                       superevent['preferred_event_data']['search'] in
                       se_searches]
        return results


def search(gracedb_id, tl, th, gracedb=None, group=None, pipelines=None,
           searches=[], se_searches=[], event_dict=None):
    """ Perform a search for neighbors coincident in time within
        a window [tl, th] seconds around an event. Uploads the
        results to the selected gracedb server.

    Parameters
    ----------
    gracedb_id: str
        ID of the trigger used by GraceDB
    tl: float
        Start of coincident time window
    th: float
        End of coincident time window
    gracedb: class
        SDK or REST API client for HTTP connection
    group: string
        "CBC", "Burst", or "Test",
    pipelines: list
        List of external trigger pipeline names
    searches: array
        List of external trigger searches
    se_searches: array
        List of superevent searches
    event_dict: dict
        Dictionary of the gracedb event
    """
    # Identify neighbor types with their graceid strings.
    types = {'G': 'GW', 'E': 'External', 'S': 'Superevent',
             'T': 'Test'}
    groups = {'G': 'CBC Burst', 'E': 'External', 'S': 'Superevent'}

    # Catch potential error if pipelines or searches are None
    if not pipelines:
        pipelines = []
    if not searches:
        searches = []

    # Initiate correct instance of GraceDb.
    if gracedb is None:
        gracedb = GraceDb()

    # Load in event
    if 'S' in gracedb_id:
        event = SE(gracedb_id, gracedb=gracedb, event_dict=event_dict)
    else:
        event = ExtTrig(gracedb_id, gracedb=gracedb, event_dict=event_dict)

    # Grab any and all neighboring events.
    # Filter results depending on the group if specified.
    neighbors = query(groups[event.neighbor_type], event.gpstime, tl, th,
                      gracedb=gracedb, group=group, pipelines=pipelines,
                      searches=searches, se_searches=se_searches)

    # If no neighbors, report a null result.
    if not neighbors:
        if 'S' in gracedb_id:
            message = (f"RAVEN: No {types[event.neighbor_type]} "
                       f"{str(pipelines) + ' ' if pipelines else ''}"
                       f"{str(searches) + ' ' if searches else ''}"
                       f"candidates in window [{tl}, +{th}] seconds. ")
        else:
            message = (f"RAVEN: No {types[event.neighbor_type]} "
                       f"{str(group) + ' ' if group else ''}"
                       f"{str(se_searches) + ' ' if se_searches else ''}"
                       f"candidates in window [{tl}, +{th}] seconds. ")
        message += f"Search triggered from {gracedb_id}"
        event.submit_gracedb_log(message, tags=["ext_coinc"])

    # If neighbors are found, report each of them.
    else:
        for neighbor in neighbors:
            if event.neighbor_type == 'S':
                # search called on a external event
                deltat = event.gpstime - neighbor['t_0']
                superid = neighbor['superevent_id']
                extid = event.graceid
                tl_m, th_m = tl, th
                relat_word = ['before', 'after']
                ext = event
                se = SE(superid, gracedb=gracedb, event_dict=neighbor)
            else:
                # search called on a superevent
                deltat = event.gpstime - neighbor['gpstime']
                superid = event.graceid
                extid = neighbor['graceid']
                tl_m, th_m = -th, -tl
                relat_word = ['after', 'before']
                se = event
                ext = ExtTrig(extid, gracedb=gracedb, event_dict=neighbor)
            if deltat < 0:
                relat_word.reverse()
                deltat = abs(deltat)
            selink = 'superevents/'
            extlink = 'events/'
            gracedb_url = re.findall('(.*)api/', _get_gracedb_url(gracedb))[0]

            # Send message to external event
            message_ext = \
                (f"RAVEN: {types['S']} {str(group) + ' ' if group else ''}"
                 f"{str(se_searches) + ' ' if se_searches else ''}candidate "
                 f"<a href='{gracedb_url}{selink}{superid}'>{superid}</a> "
                 f"within [{tl_m}, +{th_m}] seconds, about {float(deltat):.3f}"
                 f" second(s) {relat_word[0]} {types['E']} event. "
                 f"Search triggered from {gracedb_id}")
            ext.submit_gracedb_log(message_ext, tags=["ext_coinc"])

            # Send message to superevent
            message_gw = \
                (f"RAVEN: {types['E']} "
                 f"{str(pipelines) + ' ' if pipelines else ''}"
                 f"{str(searches) + ' ' if searches else ''}event "
                 f"<a href='{gracedb_url}{extlink}{extid}'>{extid}</a> "
                 f"within [{-th_m}, +{-tl_m}] seconds, about "
                 f"{float(deltat):.3f} second(s) {relat_word[1]} "
                 f"{types['S']}. Search triggered from {gracedb_id}")
            se.submit_gracedb_log(message_gw, tags=["ext_coinc"])

    # Return search results.
    return neighbors


def skymap_overlap_integral(se_skymap, exttrig_skymap=[],
                            se_skymap_uniq=[], ext_skymap_uniq=[],
                            ra=None, dec=None,
                            se_nested=True, ext_nested=True):
    """Sky map overlap integral between two sky maps.

    This method was originally developed in:
        doi.org/10.3847/1538-4357/aabfd2
    while the flattened sky map version was mentioned in:
        https://git.ligo.org/brandon.piotrzkowski/raven-paper

    Either a multi-ordered (MOC) GW sky map with UNIQ ordering,
    or a flattened sky map with Nested or Ring ordering can be used.
    Either a mutli-ordered (MOC) external sky map with UNIQ ordering,
    flattened sky map with Nested or Ring ordering,
    or a position indicated by RA/DEC can be used.

    Parameters
    ----------
    se_skymap: array
        Array containing either GW sky localization probabilities
        if using nested or ring ordering,
        or probability density if using UNIQ ordering
    exttrig_skymap: array
        Array containing either external sky localization probabilities
        if using nested or ring ordering,
        or probability density if using UNIQ ordering
    se_skymap_uniq: array
        Array containing GW UNIQ indexing, if non-empty then assumes
        GW sky map is multi-ordered
    ext_skymap_uniq: array
        Array containing external UNIQ indexing, if non-empty then assume
        external sky map is multi-ordered
    ra: float
        Right ascension of external localization in degrees
    dec: float
        Declination of external localization in degrees
    se_nested: bool
        If True, assumes GW sky map uses nested ordering, otherwise
        assumes ring ordering
    ext_nested: bool
        If True, assumes external sky map uses nested ordering, otherwise
        assumes ring ordering

    """
    se_order = 'nested' if se_nested or any(se_skymap_uniq) else 'ring'
    ext_order = 'nested' if ext_nested or any(ext_skymap_uniq) else 'ring'

    # Enforce the sky maps to be non-negative
    se_skymap = np.abs(se_skymap)
    exttrig_skymap = np.abs(exttrig_skymap)

    if not any(exttrig_skymap) and not (ra is not None and dec is not None):
        # Raise error if external info not given
        raise ValueError("Please provide external sky map or ra/dec")

    # Use multi-ordered GW sky map
    if any(se_skymap_uniq):
        # gw_skymap is the probability density instead of probability
        # convert GW sky map uniq to ra and dec
        level, ipix = ah.uniq_to_level_ipix(se_skymap_uniq)
        nsides = ah.level_to_nside(level)
        areas = ah.nside_to_pixel_area(nsides)
        ra_gw, dec_gw = \
            ah.healpix_to_lonlat(ipix, nsides,
                                 order='nested')
        sky_prior = 1 / (4 * np.pi * u.sr)
        se_norm = np.sum(se_skymap * areas)

        if any(ext_skymap_uniq):
            # Use two multi-ordered sky maps
            # Find ra/dec of external skymap
            level, ipix = ah.uniq_to_level_ipix(ext_skymap_uniq)
            nsides = ah.level_to_nside(level)
            ra_ext, dec_ext = \
                ah.healpix_to_lonlat(ipix, nsides,
                                     order=ext_order)
            # Find closest external pixels to gw pixels
            c = SkyCoord(ra=ra_gw, dec=dec_gw)
            catalog = SkyCoord(ra=ra_ext, dec=dec_ext)
            ext_ind, d2d, d3d = c.match_to_catalog_sky(catalog)
            ext_norm = np.sum(exttrig_skymap * ah.nside_to_pixel_area(nsides))

            return np.sum(se_skymap * areas * exttrig_skymap[ext_ind] /
                          sky_prior / se_norm / ext_norm).to(1).value

        elif ra is not None and dec is not None:
            # Use multi-ordered gw sky map and one external point
            # Relevant for very well localized experiments
            # such as Swift
            c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
            catalog = SkyCoord(ra=ra_gw, dec=dec_gw)
            ind, d2d, d3d = c.match_to_catalog_sky(catalog)

            return (se_skymap[ind] / u.sr / sky_prior / se_norm).to(1).value

        elif any(exttrig_skymap):
            # Use multi-ordered gw sky map and flat external sky map
            # Find matching external sky map indices using GW ra/dec
            ext_nside = ah.npix_to_nside(len(exttrig_skymap))
            ext_ind = \
                ah.lonlat_to_healpix(ra_gw, dec_gw, ext_nside,
                                     order=ext_order)

            ext_norm = np.sum(exttrig_skymap)

            return np.sum(se_skymap * areas * exttrig_skymap[ext_ind] /
                          ah.nside_to_pixel_area(ext_nside) /
                          sky_prior / se_norm / ext_norm).to(1).value

    # Use flat GW sky map
    else:
        if ra is not None and dec is not None:
            # Use flat gw sky and one external point
            se_nside = ah.npix_to_nside(len(se_skymap))
            ind = ah.lonlat_to_healpix(ra * u.deg, dec * u.deg, se_nside,
                                       order=se_order)
            se_norm = sum(se_skymap)
            return se_skymap[ind] * len(se_skymap) / se_norm

        elif any(exttrig_skymap):
            if se_nested != ext_nested:
                raise ValueError("Sky maps must both use nested or ring"
                                 "ordering")
            # Use two flat sky maps
            nside_s = hp.npix2nside(len(se_skymap))
            nside_e = hp.npix2nside(len(exttrig_skymap))
            if nside_s > nside_e:
                exttrig_skymap = hp.ud_grade(exttrig_skymap,
                                             nside_out=nside_s,
                                             order_in=('NESTED' if ext_nested
                                                       else 'RING'))
            else:
                se_skymap = hp.ud_grade(se_skymap,
                                        nside_out=nside_e,
                                        order_in=('NESTED' if se_nested
                                                  else 'RING'))
            se_norm = se_skymap.sum()
            exttrig_norm = exttrig_skymap.sum()
            if se_norm > 0 and exttrig_norm > 0:
                return (np.dot(se_skymap, exttrig_skymap) / se_norm /
                        exttrig_norm * len(se_skymap))
            else:
                return ("RAVEN: ERROR: At least one sky map has a "
                        "probability density that sums to zero or less.")

    raise ValueError("Please provide both GW and external sky map info")


def coinc_far(se_id, ext_id, tl, th, grb_search='GRB', se_fitsfile=None,
              ext_fitsfile=None, incl_sky=False,
              gracedb=None, far_grb=None, em_rate=None,
              far_gw_thresh=None, far_grb_thresh=None,
              se_dict=None, ext_dict=None,
              se_moc=False, ext_moc=False,
              use_radec=False, se_nested=False, ext_nested=False,
              use_preferred_event_skymap=False):
    """ Calculate the significance of a gravitational wave candidate with the
        addition of an external astrophyical counterpart in terms of a
        coincidence false alarm rate. This includes a temporal and a
        space-time type.

    Parameters
    ----------
    se_id: str
        GraceDB ID of superevent
    ext_id: str
        GraceDB ID of external event
    tl: float
        Start of coincident time window
    th: float
        End of coincident time window
    grb_search: str
        Determines joint FAR method.
        "GRB", "SubGRB", or "SubGRBTargeted"
    se_fitsfile: str
        GW's skymap file name
    ext_fitsfile: str
        External event's skymap file name
    incl_sky: bool
        If True, uses skymaps in the joint FAR calculation
    gracedb: class
        SDK or REST API client for HTTP connection
    far_grb: float
        GRB false alarm rate
    em_rate: float
        Detection rate of external events
    far_gw_thresh: float
        Maximum cutoff for GW FAR considered in the search
    far_grb_thresh: float
        Maximum cutoff for GRB FAR considered in the search
    se_dict: float
        Dictionary of superevent
    ext_dict: float
        Dictionary of external event
    se_moc: bool
        If True, assumes multi-order coverage (MOC) GW skymap
    ext_moc: bool
        If True, assumes multi-order coverage (MOC) external event skymap
    use_radec: bool
        If True, use ra and dec for single pixel external skymap
    se_nested: bool
        If True, assumes GW skymap uses nested ordering, otherwise
        assumes ring ordering
    ext_nested: bool
        If True, assumes external skymap uses nested ordering, otherwise
        assumes ring ordering
    use_preferred_event_skymap: bool
        If True, uses the GW sky map in the preferred event rather than the
        superevent
    """

    # Create the SE and ExtTrig objects based on string inputs.
    se = SE(se_id, fitsfile=se_fitsfile, gracedb=gracedb, event_dict=se_dict,
            is_moc=se_moc, nested=se_nested,
            use_preferred_event_skymap=use_preferred_event_skymap)
    ext = ExtTrig(ext_id, fitsfile=ext_fitsfile, gracedb=gracedb,
                  event_dict=ext_dict, use_radec=use_radec, is_moc=ext_moc,
                  nested=ext_nested)

    # Is the GW superevent candidate's FAR sensible?
    if not se.far:
        message = ("RAVEN: WARNING: This GW superevent candidate's FAR is a "
                   " NoneType object.")
        return message

    # The combined rate of independent GRB discovery by Swift, Fermi,
    # INTEGRAL, and AGILE MCAL
    # Fermi: 236/yr
    # Swift: 65/yr
    # INTEGRAL: ~5/yr
    # AGILE MCAL: ~5/yr
    gcn_rate = 310. / (365. * 24. * 60. * 60.)

    if grb_search in {'GRB', 'MDC'}:
        # Check if given an em rate first, intended for offline use
        # Otherwise calculate FAR using vetted rate based on search
        em_rate = em_rate if em_rate else gcn_rate
        temporal_far = (th - tl) * em_rate * se.far

    elif grb_search == 'SubGRB':
        # Rate of subthreshold GRBs (rate of threshold plus rate of
        # subthreshold). Introduced based on an analysis done by
        # Peter Shawhan: https://dcc.ligo.org/cgi-bin/private/
        #                DocDB/ShowDocument?docid=T1900297&version=
        gcn_rate += 65. / (365. * 24. * 60. * 60.)
        em_rate = em_rate if em_rate else gcn_rate
        temporal_far = (th - tl) * em_rate * se.far

    elif grb_search == 'SubGRBTargeted':
        # Max FARs considered in analysis
        if ext.inst == 'Fermi':
            far_gw_thresh = far_gw_thresh if far_gw_thresh else 1 / (3600 * 24)
            far_grb_thresh = far_grb_thresh if far_grb_thresh else 1 / 10000
        elif ext.inst == 'Swift':
            far_gw_thresh = far_gw_thresh if far_gw_thresh else 2 / (3600 * 24)
            far_grb_thresh = far_grb_thresh if far_grb_thresh else 1 / 1000
        else:
            raise AssertionError(("Only Fermi or Swift are valid "
                                  "pipelines for joint sub-threshold "
                                  "search"))
        # Map the product of uniformly drawn distributions to CDF
        # See https://en.wikipedia.org/wiki/Product_distribution
        z = (th - tl) * far_grb * se.far
        z_max = (th - tl) * far_grb_thresh * far_gw_thresh
        temporal_far = z * (1 - np.log(z/z_max))

    else:
        message = ("RAVEN: WARNING: Invalid search. RAVEN only considers "
                   "'GRB', 'SubGRB', and 'SubGRBTargeted'.")
        return message

    # Include sky coincidence if desired.
    if incl_sky:
        skymap_overlap = skymap_overlap_integral(
                             se.skymap, ext.skymap,
                             se.uniq, ext.uniq, ext.ra, ext.dec,
                             se.nested, ext.nested)
        if isinstance(skymap_overlap, str):
            return skymap_overlap
        try:
            spatiotemporal_far = temporal_far / skymap_overlap
        except ZeroDivisionError:
            message = ("RAVEN: WARNING: Sky maps minimally overlap. "
                       "Sky map overlap integral is {0:.2e}. "
                       "There is strong evidence against these events being "
                       "coincident.").format(skymap_overlap)
            return message
    else:
        spatiotemporal_far = None
        skymap_overlap = None

    return {"temporal_coinc_far": temporal_far,
            "spatiotemporal_coinc_far": spatiotemporal_far,
            "skymap_overlap": skymap_overlap,
            "preferred_event": se.preferred_event,
            "external_event": ext.graceid}


def calc_signif_gracedb(se_id, ext_id, tl, th, grb_search='GRB',
                        se_fitsfile=None, ext_fitsfile=None,
                        incl_sky=False, gracedb=None,
                        far_grb=None, em_rate=None,
                        far_gw_thresh=None, far_grb_thresh=None,
                        se_dict=None, ext_dict=None,
                        se_moc=False, ext_moc=False,
                        use_radec=False, se_nested=False, ext_nested=False,
                        use_preferred_event_skymap=False):
    """ Calculates and uploads the coincidence false alarm rate
        of the given superevent to the selected gracedb server.

    Parameters
    ----------
    se_id: str
        GraceDB ID of superevent
    ext_id: str
        GraceDB ID of external event
    tl: float
        Start of coincident time window
    th: float
        End of coincident time window
    grb_search: str
        Determines joint FAR method.
        "GRB", "SubGRB", or "SubGRBTargeted"
    se_fitsfile: str
        GW's skymap file name
    ext_fitsfile: str
        External event's skymap file name
    incl_sky: bool
        If True, uses skymaps in the joint FAR calculation
    gracedb: class
        SDK or REST API client for HTTP connection
    far_grb: float
        GRB false alarm rate
    em_rate: float
        Detection rate of external events
    far_gw_thresh: float
        Maximum cutoff for GW FAR considered in the search
    far_grb_thresh: float
        Maximum cutoff for GRB FAR considered in the search
    se_dict: float
        Dictionary of superevent
    ext_dict: float
        Dictionary of external event
    se_moc: bool
        If True, assumes multi-order coverage (MOC) GW skymap
    ext_moc: bool
        If True, assumes multi-order coverage (MOC) external event skymap
    use_radec: bool
        If True, use ra and dec for single pixel external skymap
    se_nested: bool
        If True, assumes GW skymap uses nested ordering, otherwise
        assumes ring ordering
    ext_nested: bool
        If True, assumes external skymap uses nested ordering, otherwise
        assumes ring ordering
    use_preferred_event_skymap: bool
        If True, uses the GW sky map in the preferred event rather than the
        superevent
    """

    # Create the SE and ExtTrig objects based on string inputs.
    se = SE(se_id, fitsfile=se_fitsfile, gracedb=gracedb, event_dict=se_dict,
            is_moc=se_moc, nested=se_nested,
            use_preferred_event_skymap=use_preferred_event_skymap)
    ext = ExtTrig(ext_id, fitsfile=ext_fitsfile, gracedb=gracedb,
                  event_dict=ext_dict, use_radec=use_radec, is_moc=ext_moc,
                  nested=ext_nested)

    # Create coincidence_far.json
    coinc_far_output = \
        coinc_far(
            se_id, ext_id, tl, th,
            grb_search=grb_search,
            se_fitsfile=se_fitsfile,
            ext_fitsfile=ext_fitsfile,
            incl_sky=incl_sky, gracedb=gracedb,
            far_grb=far_grb, em_rate=em_rate,
            far_gw_thresh=far_gw_thresh,
            far_grb_thresh=far_grb_thresh,
            se_dict=se_dict, ext_dict=ext_dict,
            se_moc=se_moc, ext_moc=ext_moc,
            use_radec=use_radec,
            se_nested=se_nested, ext_nested=ext_nested,
            use_preferred_event_skymap=use_preferred_event_skymap)
    if isinstance(coinc_far_output, str):
        se.submit_gracedb_log(coinc_far_output, tags=["ext_coinc"])
        ext.submit_gracedb_log(coinc_far_output, tags=["ext_coinc"])
        raise ZeroDivisionError(coinc_far_output)
    coincidence_far = json.dumps(coinc_far_output)

    gracedb_events_url = re.findall('(.*)api/', _get_gracedb_url(gracedb))[0]
    link1 = 'events/'
    link2 = 'superevents/'

    message = (f"RAVEN: Computed coincident FAR(s) in Hz with external "
               f"trigger <a href='{gracedb_events_url + link1}"
               f"{ext.graceid}'>{ext.graceid}</a>")
    se.submit_gracedb_log(message, filename='coincidence_far.json',
                          filecontents=coincidence_far,
                          tags=["ext_coinc"])

    message = (f"RAVEN: Computed coincident FAR(s) in Hz with superevent "
               f"<a href='{gracedb_events_url + link2}"
               f"{se.graceid}'>{se.graceid}</a>")
    ext.submit_gracedb_log(message, filename='coincidence_far.json',
                           filecontents=coincidence_far,
                           tags=["ext_coinc"])

    return coinc_far_output
