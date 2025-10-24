from unittest.mock import call, patch
import unittest.mock as mock
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.utils.data import get_file_contents
from math import isclose

from ligo import raven
from ligo.raven.gracedb_events import _is_gracedb_sdk
from ligo.raven.tests.mock_gracedb_rest import MockGracedb as mock_gracedb_rest
from ligo.raven.tests.mock_gracedb_sdk import MockGracedb as mock_gracedb_sdk


def query_return(event_type, gpstime, tl, th,
                 gracedb=None, group=None, pipelines=None,
                 searches=None, se_searches=None):
    if searches and 'MDC' in searches and event_type=='External':
        return [{"graceid": "E4",
                 "gpstime": 100.,
                 "pipeline": "Fermi",
                 "group": "External",
                 "search": "MDC"}]
    elif searches and 'MDC' in searches and event_type=='Superevent':
        return [{"superevent_id": "S4",
                 "t_0": 100.5,
                 "far": 1e-8,
                 "preferred_event": "G4",
                 "preferred_event_data":
                 {"group": "CBC",
                  "search": "MDC"}}]
    elif tl==-5 and (group==None and pipelines==[]):
        return [{"superevent_id": "S1",
                 "t_0":100.5,
                 "far": 1e-7,
                 "preferred_event": "G1",
                 "preferred_event_data":
                 {"group": "CBC",
                  "search": "AllSky"}},
                {"superevent_id": "S2",
                 "t_0": 96.0,
                 "far": 1e-7,
                 "preferred_event": "G2",
                 "preferred_event_data":
                 {"group": "Burst",
                  "search": "AllSky"}}]
    elif tl==-600 and group=='Burst':
        return [{"superevent_id": "S2",
                 "t_0": 96.0,
                 "far": 1e-7,
                 "preferred_event": "G2",
                 "preferred_event_data":
                 {"group": "Burst",
                  "search": "AllSky"}}]
    elif tl==-5 and group=='CBC':
        return [{"superevent_id": "S1",
                 "t_0": 100.5,
                 "far": 1e-7,
                 "preferred_event": "G1",
                 "preferred_event_data":
                 {"group": "CBC",
                  "search": "AllSky"}}]
    elif (tl==-1 and searches) and ('SubGRB' in searches):
        return [{"graceid": "E4",
                 "gpstime": 99.5,
                 "pipeline": "Fermi",
                 "group": "External",
                 "search": "SubGRB"}]
    elif tl==-1 and pipelines==['Fermi','Swift']:
        return [{"graceid": "E1",
                 "gpstime": 102.0,
                 "pipeline": "Swift",
                 "group": "External",
                 "search": "GRB",
                 "extra_attributes": {
                     "GRB": {
                         "ra": 120.,
                         "dec": 30.}}},
                {"graceid": "E4",
                 "gpstime": 99.5,
                 "pipeline": "Fermi",
                 "group": "External",
                 "search": "SubGRB"}]
    elif tl==-10 and th==10:
        return [{"graceid": "E2",
                 "gpstime": 106.0,
                 "pipeline": "SNEWS",
                 "group": "External",
                 "search": "Supernova"}]
    else:
        return []


@pytest.mark.parametrize(
    'gracedb_id,event_type,gpstime,tl,th,group,pipelines,searches',
    [['E100','Superevent', 100, -5, 1, None, [], []],
     ['E101','Superevent', 100, -600, 60, 'Burst', [], []],
     ['E102','Superevent', 100, -5, 1, 'CBC', [], []],
     ['E102','Superevent', 100, -5, 1, 'CBC', None, None],
     ['S100','External', 100, -1, 5, None, ['Fermi','Swift'], []],
     ['S100','External', 100, -1, 5, None, ['Fermi','Swift'], ['SubGRB']],
     ['S100','External', 100, -1, 5, None, ['Fermi','Swift'], ['SubGRB','SubGRBTargeted']],
     ['S101','External', 100, -10, 10, None, ['SNEWS'], []],
     ['S102','External', 100, -1, 5, None, ['Fermi'], ['MDC']]])
# Repeat all tests with GraceDB SDK
@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_call_query(gracedb_id, event_type, gpstime, tl, th, group, pipelines,
                    searches, mock_gracedb):
 
    results = raven.search.query(
                  event_type, gpstime, tl, th, gracedb=mock_gracedb(),
                  group=group, pipelines=pipelines, searches=searches)
  
    assert results == query_return(event_type, gpstime, tl, th, group=group,
                                   pipelines=pipelines, searches=searches)
 

@pytest.mark.parametrize(
    'gracedb_id,event_type,gpstime,tl,th,group,pipelines,searches,se_searches',
    [['E100','Superevent', 100, -5, 1, None, [], [], []],
     ['E101','Superevent', 100, -600, 60, 'Burst', [], [], []],
     ['E102','Superevent', 100, -5, 1, 'CBC', [], [], []],
     ['S100','External', 100, -1, 5, None, ['Fermi','Swift'], [], []],
     ['S100','External', 100, -1, 5, None, ['Fermi','Swift'], ['SubGRB'], []],
     ['S101','External', 100, -10, 10, None, ['SNEWS'], [], []],
     ['S102','External', 100, -1, 5, 'CBC', ['Fermi'], ['MDC'], ['MDC']],
     ['M103','Superevent', 100, -5, 1, 'CBC', [], ['MDC'], ['MDC']],
     ['S102','External', 100, -113, 56, None, ['AGILE'], ['LVOM'], []],
     ['E102','Superevent', 100, -5, 1, 'CBC', None, None, None]])
# Repeat all tests with GraceDB SDK
@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_search_return(gracedb_id, event_type, gpstime, tl, th, group, pipelines,
                       searches, se_searches, mock_gracedb):

    if gracedb_id.startswith('S'):
        event_dict = {'superevent': gracedb_id,
                      't_0': gpstime,
                      'group': group,
                      'preferred_event': 'G1',
                      'far': 1e-4}
    else:
        event_dict = {'graceid': gracedb_id,
                      'gpstime': gpstime,
                      'group': group,
                      'pipeline': 'Fermi'}

    mockgracedb = mock_gracedb()
    is_gracedb_sdk = _is_gracedb_sdk(mockgracedb)
    results = raven.search.search(gracedb_id, tl, th, gracedb=mockgracedb,
                                  group=group, pipelines=pipelines, searches=searches,
                                  event_dict=event_dict, se_searches=se_searches)
    assert results == query_return(event_type, gpstime, tl, th, group=group,
                                   pipelines=pipelines, searches=searches,
                                   se_searches=se_searches)
    
    message_list = [
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S1'>S1</a> within [-5, +1] seconds, about 0.500 second(s) after External event. Search triggered from E100",
            "RAVEN: External event <a href='https://gracedb-mock.org/events/E100'>E100</a> within [-1, +5] seconds, about 0.500 second(s) before Superevent. Search triggered from E100",
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S2'>S2</a> within [-5, +1] seconds, about 4.000 second(s) before External event. Search triggered from E100",
            "RAVEN: External event <a href='https://gracedb-mock.org/events/E100'>E100</a> within [-1, +5] seconds, about 4.000 second(s) after Superevent. Search triggered from E100",
            "RAVEN: Superevent Burst candidate <a href='https://gracedb-mock.org/superevents/S2'>S2</a> within [-600, +60] seconds, about 4.000 second(s) before External event. Search triggered from E101",
            "RAVEN: External event <a href='https://gracedb-mock.org/events/E101'>E101</a> within [-60, +600] seconds, about 4.000 second(s) after Superevent. Search triggered from E101",
            "RAVEN: Superevent CBC candidate <a href='https://gracedb-mock.org/superevents/S1'>S1</a> within [-5, +1] seconds, about 0.500 second(s) after External event. Search triggered from E102",
            "RAVEN: External event <a href='https://gracedb-mock.org/events/E102'>E102</a> within [-1, +5] seconds, about 0.500 second(s) before Superevent. Search triggered from E102",
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S100'>S100</a> within [-5, +1] seconds, about 2.000 second(s) before External event. Search triggered from S100",
            "RAVEN: External ['Fermi', 'Swift'] event <a href='https://gracedb-mock.org/events/E1'>E1</a> within [-1, +5] seconds, about 2.000 second(s) after Superevent. Search triggered from S100",
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S100'>S100</a> within [-5, +1] seconds, about 0.500 second(s) after External event. Search triggered from S100",
            "RAVEN: External ['Fermi', 'Swift'] event <a href='https://gracedb-mock.org/events/E4'>E4</a> within [-1, +5] seconds, about 0.500 second(s) before Superevent. Search triggered from S100",
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S100'>S100</a> within [-5, +1] seconds, about 0.500 second(s) after External event. Search triggered from S100",
            "RAVEN: External ['Fermi', 'Swift'] ['SubGRB'] event <a href='https://gracedb-mock.org/events/E4'>E4</a> within [-1, +5] seconds, about 0.500 second(s) before Superevent. Search triggered from S100",
            "RAVEN: Superevent candidate <a href='https://gracedb-mock.org/superevents/S101'>S101</a> within [-10, +10] seconds, about 6.000 second(s) before External event. Search triggered from S101",
            "RAVEN: External ['SNEWS'] event <a href='https://gracedb-mock.org/events/E2'>E2</a> within [-10, +10] seconds, about 6.000 second(s) after Superevent. Search triggered from S101",
            "RAVEN: Superevent CBC ['MDC'] candidate <a href='https://gracedb-mock.org/superevents/S102'>S102</a> within [-5, +1] seconds, about 0.000 second(s) after External event. Search triggered from S102",
            "RAVEN: External ['Fermi'] ['MDC'] event <a href='https://gracedb-mock.org/events/E4'>E4</a> within [-1, +5] seconds, about 0.000 second(s) before Superevent. Search triggered from S102",
            "RAVEN: Superevent CBC ['MDC'] candidate <a href='https://gracedb-mock.org/superevents/S4'>S4</a> within [-5, +1] seconds, about 0.500 second(s) after External event. Search triggered from M103",
            "RAVEN: External ['MDC'] event <a href='https://gracedb-mock.org/events/M103'>M103</a> within [-1, +5] seconds, about 0.500 second(s) before Superevent. Search triggered from M103",
            "RAVEN: No External ['AGILE'] ['LVOM'] candidates in window [-113, +56] seconds. Search triggered from S102"
        ]
 
    if gracedb_id=='E100':
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E100'].logs.create.call_args_list
            assert calls_list[0][1]['comment'] == message_list[0]
            assert calls_list[1][1]['comment'] == message_list[2]

            calls_list = mockgracedb.superevents['S1'].logs.create.call_args_list
            assert calls_list[0][1]['comment'] == message_list[1]

            calls_list = mockgracedb.superevents['S2'].logs.create.call_args_list
            assert calls_list[1][1]['comment'] == message_list[3]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[0][1]['message'] == message_list[0]
            assert calls_list[1][1]['message'] == message_list[1]
            assert calls_list[2][1]['message'] == message_list[2]
            assert calls_list[3][1]['message'] == message_list[3]

    elif gracedb_id=='E101':
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E101'].logs.create.call_args_list
            assert calls_list[2][1]['comment'] == message_list[4]

            calls_list = mockgracedb.superevents['S2'].logs.create.call_args_list
            assert calls_list[2][1]['comment'] == message_list[5]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[4][1]['message'] == message_list[4]
            assert calls_list[5][1]['message'] == message_list[5]

    elif gracedb_id=='E102':
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E102'].logs.create.call_args_list
            assert calls_list[3][1]['comment'] == message_list[6]

            calls_list = mockgracedb.superevents['S1'].logs.create.call_args_list
            assert calls_list[3][1]['comment'] == message_list[7]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[6][1]['message'] == message_list[6]
            assert calls_list[7][1]['message'] == message_list[7]

    elif gracedb_id=='S100' and not searches:
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E1'].logs.create.call_args_list
            assert calls_list[4][1]['comment'] == message_list[8]

            calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list
            assert calls_list[4][1]['comment'] == message_list[9]
            assert calls_list[5][1]['comment'] == message_list[11]

            calls_list = mockgracedb.events['E4'].logs.create.call_args_list
            assert calls_list[5][1]['comment'] == message_list[10]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[8][1]['message'] == message_list[8]
            assert calls_list[9][1]['message'] == message_list[9]
            assert calls_list[10][1]['message'] == message_list[10]
            assert calls_list[11][1]['message'] == message_list[11]

    elif gracedb_id=='S100' and searches:
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E1'].logs.create.call_args_list
            assert calls_list[6][1]['comment'] == message_list[12]

            calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list
            assert calls_list[6][1]['comment'] == message_list[13]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[12][1]['message'] == message_list[12]
            assert calls_list[13][1]['message'] == message_list[13]

    elif gracedb_id=='S101':
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E2'].logs.create.call_args_list
            assert calls_list[7][1]['comment'] == message_list[14]

            calls_list = mockgracedb.superevents['S101'].logs.create.call_args_list
            assert calls_list[7][1]['comment'] == message_list[15]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[14][1]['message'] == message_list[14]
            assert calls_list[15][1]['message'] == message_list[15]

    elif gracedb_id=='S102' and group:
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E4'].logs.create.call_args_list
            assert calls_list[8][1]['comment'] == message_list[16]

            calls_list = mockgracedb.superevents['S102'].logs.create.call_args_list
            assert calls_list[8][1]['comment'] == message_list[17]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[16][1]['message'] == message_list[16]
            assert calls_list[17][1]['message'] == message_list[17]

    elif gracedb_id=='M103':
        if is_gracedb_sdk:
            calls_list = mockgracedb.events['E4'].logs.create.call_args_list
            assert calls_list[9][1]['comment'] == message_list[18]

            calls_list = mockgracedb.superevents['S102'].logs.create.call_args_list
            assert calls_list[9][1]['comment'] == message_list[19]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[18][1]['message'] == message_list[18]
            assert calls_list[19][1]['message'] == message_list[19]

    elif gracedb_id=='S102':
        if is_gracedb_sdk:
            calls_list = mockgracedb.superevents['S102'].logs.create.call_args_list
            assert calls_list[10][1]['comment'] == message_list[20]
        else:
            calls_list = mockgracedb.writeLog.call_args_list
            assert calls_list[20][1]['message'] == message_list[20]


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_grb(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S100', 'E1', -1, 5, gracedb=mock_gracedb())
    assert isclose(result['temporal_coinc_far'], 5.8980e-10, abs_tol=1e-13)
    assert result['preferred_event'] == 'G1' 


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_snews(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S101', 'E2', -10, 10, gracedb=mock_gracedb(),
                                    grb_search='Supernova')
    assert result == "RAVEN: WARNING: Invalid search. RAVEN only considers 'GRB', 'SubGRB', and 'SubGRBTargeted'."


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_subgrb(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S102', 'E3', -5, 1, gracedb=mock_gracedb(),
                                    grb_search='SubGRB')
    assert isclose(result['temporal_coinc_far'], 7.1347e-14, abs_tol=1e-17)
    assert result['preferred_event'] == 'G3'


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_swift_subgrb(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S101', 'E4', -30, 30, gracedb=mock_gracedb(),
                                    far_grb=1e-4, grb_search='SubGRBTargeted')
    assert isclose(result['temporal_coinc_far'], 5.2482e-9, abs_tol=1e-13)
    assert result['preferred_event'] == 'G2'


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_mdc(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S100', 'M5', -1, 5, gracedb=mock_gracedb(),
                                    grb_search='MDC')
    assert isclose(result['temporal_coinc_far'], 5.8980e-10, abs_tol=1e-13)
    assert result['preferred_event'] == 'G1'


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
@patch('ligo.raven.gracedb_events.SE')
@patch('ligo.raven.gracedb_events.ExtTrig')
def test_coinc_far_emrate(mock_ExtTrig, mock_SE, mock_gracedb):

    result = raven.search.coinc_far('S100', 'E1', -1, 5, gracedb=mock_gracedb(), em_rate=1e-7)
    assert isclose(result['temporal_coinc_far'], 6e-12, abs_tol=1e-13)
    assert result['preferred_event'] == 'G1'


class S100Skymap(object):
    def read(self):
        return get_file_contents('ligo/tests/data/GW170817/bayestar.fits.gz',
                                 encoding='binary', cache=False)


class E1Skymap(object):
    def read(self):
        return get_file_contents('ligo/tests/data/GW170817/glg_healpix_all_bn_v00.fit',
                                 encoding='binary', cache=False)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_coinc_far_skymap(mock_gracedb):

    result = raven.search.coinc_far('S100', 'E3', -5, 1, gracedb=mock_gracedb(),
                                    grb_search='GRB', incl_sky=True, se_fitsfile='bayestar.fits.gz',
                                    ext_fitsfile='glg_healpix_all_bn_v00.fit',
                                    se_nested=False, ext_nested=False)

    assert isclose(result['spatiotemporal_coinc_far'], 5.6755e-11, abs_tol=1e-14)
    assert result['preferred_event'] == 'G1'


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signif_gracedb_flat_flat(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E3', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.fits.gz',
                                              ext_fitsfile='glg_healpix_all_bn_v00.fit',
                                              se_nested=False, ext_nested=False)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E3'>E3</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/32.286, rel_tol=.001)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signif_gracedb_moc_flat(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E3', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.multiorder.fits',
                                              ext_fitsfile='glg_healpix_all_bn_v00.fit',
                                              se_moc=True, ext_moc=False,
                                              se_nested=True ,ext_nested=False)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message  == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E3'>E3</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/32.286, rel_tol=.001)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signif_gracedb_moc_flat_using_preferred_event(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E3', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.multiorder.fits',
                                              ext_fitsfile='glg_healpix_all_bn_v00.fit',
                                              se_moc=True, ext_moc=False,
                                              se_nested=True ,ext_nested=False,
                                              use_preferred_event_skymap=True)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message  == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E3'>E3</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/32.286, rel_tol=.001)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signif_gracedb_moc_moc(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E3', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.multiorder.fits',
                                              ext_fitsfile='glg_healpix_all_bn_v00.multiorder.fits',
                                              se_moc=True, ext_moc=True, se_nested=True, ext_nested=True)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message  == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E3'>E3</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/32.286, rel_tol=.001)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signic_gracedb_flat_radec(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E1', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.fits.gz',
                                              use_radec=True, se_nested=False, ext_nested=False)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E1'>E1</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/1430, rel_tol=.001)


@pytest.mark.parametrize('mock_gracedb', [mock_gracedb_rest, mock_gracedb_sdk])
def test_calc_signic_gracedb_moc_radec(mock_gracedb):
    mockgracedb = mock_gracedb()
    result = raven.search.calc_signif_gracedb('S100', 'E1', -5, 1, gracedb=mockgracedb,
                                              grb_search='GRB', incl_sky=True, se_fitsfile='GW170817.multiorder.fits',
                                              use_radec=True, se_nested=True, ext_nested=False, se_moc=True)

    if _is_gracedb_sdk(mockgracedb):
        calls_list = mockgracedb.superevents['S100'].logs.create.call_args_list[-1][1]
        message = calls_list['comment']
        tags = calls_list['tags']
    else:
        calls_list = mockgracedb.writeLog.call_args_list[-2][1]
        message = calls_list['message']
        tags = calls_list['tag_name']

    assert message == "RAVEN: Computed coincident FAR(s) in Hz with external trigger <a href='https://gracedb-mock.org/events/E1'>E1</a>"
    assert calls_list['filename'] == 'coincidence_far.json'
    assert tags == ['ext_coinc']
    assert isclose(float(result['temporal_coinc_far']), 5.8980e-10, abs_tol=1e-14)
    assert isclose(float(result['spatiotemporal_coinc_far']), float(result['temporal_coinc_far'])/1430, rel_tol=.001)
