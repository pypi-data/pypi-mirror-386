"""Test outcar."""

import os

import numpy as np
import pytest

from parsevasp.outcar import Outcar


@pytest.fixture
def outcar_parser(request):
    """A fixture that loads OUTCAR."""
    try:
        name = request.param
    except AttributeError:
        # Test not parametrized
        name = 'OUTCAR'
    testdir = os.path.dirname(__file__)
    outcarfile = testdir + '/' + name
    outcar = Outcar(file_path=outcarfile)

    return outcar


@pytest.fixture
def outcar_parser_file_objects(request):
    """A fixture that loads OUTCAR using file object."""
    try:
        name = request.param
    except AttributeError:
        # Test not parametrized
        name = 'OUTCAR'
    testdir = os.path.dirname(__file__)
    outcarfile = testdir + '/' + name
    outcar = None
    with open(outcarfile) as file_handler:
        outcar = Outcar(file_handler=file_handler)

    return outcar


def test_outcar_symmetry(outcar_parser):
    """Check if parser returns correct symmetry entries."""

    symmetry = outcar_parser.get_symmetry()

    test = [48, 16, 16, 16, 16, 16, 16, 4, 4, 4, 4, 4, 4, 8, 8, 48]
    assert symmetry['num_space_group_operations']['static'] == test
    assert symmetry['num_space_group_operations']['dynamic'] == test
    test = [
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
        'primitive cell',
    ]
    assert symmetry['original_cell_type']['static'] == test
    assert symmetry['original_cell_type']['dynamic'] == test
    test = [
        'face centered cubic supercell.',
        'body centered tetragonal supercell.',
        'body centered tetragonal supercell.',
        'body centered tetragonal supercell.',
        'body centered tetragonal supercell.',
        'body centered tetragonal supercell.',
        'body centered tetragonal supercell.',
        'base centered monoclinic supercell.',
        'base centered monoclinic supercell.',
        'base centered monoclinic supercell.',
        'base centered monoclinic supercell.',
        'base centered monoclinic supercell.',
        'base centered monoclinic supercell.',
        'face centered cubic supercell.',
        'face centered cubic supercell.',
        'face centered cubic supercell.',
    ]
    assert symmetry['symmetrized_cell_type']['static'] == test
    assert symmetry['symmetrized_cell_type']['dynamic'] == test


def test_outcar_elastic(outcar_parser):
    """Check if parser returns correct elastic moduli entries."""

    elastic = outcar_parser.get_elastic_moduli()
    test = np.array(
        [
            [1.6740702e03, 7.0419980e02, 7.0419980e02, -0.0000000e00, 0.0000000e00, 0.0000000e00],
            [7.0502380e02, 1.6748491e03, 7.0502380e02, -0.0000000e00, -0.0000000e00, 0.0000000e00],
            [7.0499350e02, 7.0499350e02, 1.6748165e03, 0.0000000e00, -0.0000000e00, 0.0000000e00],
            [8.2260000e-01, 8.7980000e-01, 1.2896000e00, 1.1225901e03, -0.0000000e00, 0.0000000e00],
            [-7.8000000e-03, -4.9500000e-02, 1.4700000e-02, 0.0000000e00, 1.1230829e03, -0.0000000e00],
            [-2.9200000e-02, -5.3200000e-02, -2.1970000e-01, -0.0000000e00, 0.0000000e00, 1.1223147e03],
        ]
    )
    np.testing.assert_allclose(elastic['non_symmetrized'], test)
    test = np.array(
        [
            [1674.5786, 704.739, 704.739, -0.0, 0.0, 0.0],
            [704.739, 1674.5786, 704.739, -0.0, 0.0, 0.0],
            [704.739, 704.739, 1674.5786, -0.0, -0.0, 0.0],
            [-0.0, -0.0, -0.0, 1122.6622, 0.0, -0.0],
            [0.0, 0.0, -0.0, 0.0, 1122.6622, -0.0],
            [0.0, 0.0, 0.0, -0.0, -0.0, 1122.6622],
        ]
    )
    np.testing.assert_allclose(elastic['symmetrized'], test)
    test = np.array(
        [
            [1674.5786, 704.739, 704.739, -0.0, 0.0, 0.0],
            [704.739, 1674.5786, 704.739, -0.0, 0.0, 0.0],
            [704.739, 704.739, 1674.5786, -0.0, -0.0, 0.0],
            [-0.0, -0.0, -0.0, 775.8054, 0.0, -0.0],
            [0.0, 0.0, -0.0, 0.0, 775.8054, -0.0],
            [0.0, 0.0, 0.0, -0.0, -0.0, 775.8054],
        ]
    )
    np.testing.assert_allclose(elastic['total'], test)


def test_outcar_elastic_file_object(outcar_parser_file_objects):
    """Check if parser returns correct elastic moduli entries using the file object."""

    elastic = outcar_parser_file_objects.get_elastic_moduli()
    test = np.array(
        [
            [1.6740702e03, 7.0419980e02, 7.0419980e02, -0.0000000e00, 0.0000000e00, 0.0000000e00],
            [7.0502380e02, 1.6748491e03, 7.0502380e02, -0.0000000e00, -0.0000000e00, 0.0000000e00],
            [7.0499350e02, 7.0499350e02, 1.6748165e03, 0.0000000e00, -0.0000000e00, 0.0000000e00],
            [8.2260000e-01, 8.7980000e-01, 1.2896000e00, 1.1225901e03, -0.0000000e00, 0.0000000e00],
            [-7.8000000e-03, -4.9500000e-02, 1.4700000e-02, 0.0000000e00, 1.1230829e03, -0.0000000e00],
            [-2.9200000e-02, -5.3200000e-02, -2.1970000e-01, -0.0000000e00, 0.0000000e00, 1.1223147e03],
        ]
    )
    np.testing.assert_allclose(elastic['non_symmetrized'], test)
    test = np.array(
        [
            [1674.5786, 704.739, 704.739, -0.0, 0.0, 0.0],
            [704.739, 1674.5786, 704.739, -0.0, 0.0, 0.0],
            [704.739, 704.739, 1674.5786, -0.0, -0.0, 0.0],
            [-0.0, -0.0, -0.0, 1122.6622, 0.0, -0.0],
            [0.0, 0.0, -0.0, 0.0, 1122.6622, -0.0],
            [0.0, 0.0, 0.0, -0.0, -0.0, 1122.6622],
        ]
    )
    np.testing.assert_allclose(elastic['symmetrized'], test)
    test = np.array(
        [
            [1674.5786, 704.739, 704.739, -0.0, 0.0, 0.0],
            [704.739, 1674.5786, 704.739, -0.0, 0.0, 0.0],
            [704.739, 704.739, 1674.5786, -0.0, -0.0, 0.0],
            [-0.0, -0.0, -0.0, 775.8054, 0.0, -0.0],
            [0.0, 0.0, -0.0, 0.0, 775.8054, -0.0],
            [0.0, 0.0, 0.0, -0.0, -0.0, 775.8054],
        ]
    )
    np.testing.assert_allclose(elastic['total'], test)


@pytest.mark.parametrize('outcar_parser', (['OUTCAR_MAG']), indirect=['outcar_parser'])
def test_outcar_magnetization(outcar_parser):
    """Check if the magnetization parser returns the correct magnetization."""

    magnetization = outcar_parser.get_magnetization()
    test = {
        'sphere': {
            'x': {
                'site_moment': {
                    1: {'s': -0.014, 'p': -0.051, 'd': 1.687, 'tot': 1.621},
                    2: {'s': -0.015, 'p': -0.052, 'd': 1.686, 'tot': 1.619},
                    3: {'s': -0.014, 'p': -0.053, 'd': 1.708, 'tot': 1.64},
                    4: {'s': -0.014, 'p': -0.053, 'd': 1.708, 'tot': 1.64},
                },
                'total_magnetization': {'s': -0.057, 'p': -0.21, 'd': 6.788, 'tot': 6.521},
            },
            'y': {'site_moment': {}, 'total_magnetization': {}},
            'z': {'site_moment': {}, 'total_magnetization': {}},
        },
        'full_cell': np.asarray([6.4424922]),
    }

    for _proj in ['x', 'y', 'z']:
        for _key, _val in test['sphere'][_proj]['site_moment'].items():
            _test = np.asarray(list(_val.values()))
            _mag = np.asarray(list(magnetization['sphere'][_proj]['site_moment'][_key].values()))
            np.testing.assert_allclose(_mag, _test)

        _test = np.asarray(list(test['sphere'][_proj]['total_magnetization'].values()))
        _mag = np.asarray(list(magnetization['sphere'][_proj]['total_magnetization'].values()))
        np.testing.assert_allclose(_mag, _test)
    _mag = np.asarray(list(magnetization['full_cell']))
    _test = np.asarray(list(test['full_cell']))
    np.testing.assert_allclose(_mag, _test)


@pytest.mark.parametrize('outcar_parser', ['OUTCAR_MAG_SINGLE'], indirect=['outcar_parser'])
def test_outcar_magnetization_single(outcar_parser):
    """Check if the magnetization parser returns the correct magnetization
    for a single atom in the unit cell.

    """

    magnetization = outcar_parser.get_magnetization()

    test = {
        'sphere': {
            'x': {
                'site_moment': {
                    1: {'s': -0.012, 'p': -0.043, 'd': 2.49, 'tot': 2.434},
                },
                'total_magnetization': {'s': -0.012, 'p': -0.043, 'd': 2.49, 'tot': 2.434},
            },
            'y': {'site_moment': {}, 'total_magnetization': {}},
            'z': {'site_moment': {}, 'total_magnetization': {}},
        },
        'full_cell': np.asarray([2.4077611]),
    }

    for _proj in ['x', 'y', 'z']:
        for _key, _val in test['sphere'][_proj]['site_moment'].items():
            _test = np.asarray(list(_val.values()))
            _mag = np.asarray(list(magnetization['sphere'][_proj]['site_moment'][_key].values()))
            np.testing.assert_allclose(_mag, _test)

        _test = np.asarray(list(test['sphere'][_proj]['total_magnetization'].values()))
        _mag = np.asarray(list(magnetization['sphere'][_proj]['total_magnetization'].values()))
        np.testing.assert_allclose(_mag, _test)
    _mag = np.asarray(list(magnetization['full_cell']))
    _test = np.asarray(list(test['full_cell']))
    np.testing.assert_allclose(_mag, _test)


def test_outcar_timing_information(outcar_parser_file_objects):
    """Check if outcar_parser returns correct timing information."""

    timings = outcar_parser_file_objects.get_run_stats()
    assert timings['total_cpu_time_used'] == 89.795
    assert timings['user_time'] == 60.247
    assert timings['elapsed_time'] == 90.990
    assert timings['system_time'] == 29.549
    assert timings['maximum_memory_used'] == 81612.0
    assert timings['average_memory_used'] == 0.0

    assert timings['mem_usage_base'] == 30000.0
    assert timings['mem_usage_nonl-proj'] == 2198.0
    assert timings['mem_usage_fftplans'] == 304.0
    assert timings['mem_usage_grid'] == 903.0
    assert timings['mem_usage_one-center'] == 6.0
    assert timings['mem_usage_wavefun'] == 559.0


def test_run_stats(outcar_parser):
    """Test that the output stats is correct."""

    run_stats = outcar_parser.get_run_stats()
    compare_dict = {
        'mem_usage_base': 30000.0,
        'mem_usage_nonl-proj': 2198.0,
        'mem_usage_fftplans': 304.0,
        'mem_usage_grid': 903.0,
        'mem_usage_one-center': 6.0,
        'mem_usage_wavefun': 559.0,
        'total_cpu_time_used': 89.795,
        'user_time': 60.247,
        'system_time': 29.549,
        'elapsed_time': 90.99,
        'maximum_memory_used': 81612.0,
        'average_memory_used': 0.0,
    }
    assert run_stats == compare_dict


_TEST_DATA = [
    ('OUTCAR.converged', [True, True, True, False, False]),
    ('OUTCAR.nelm-breach-consistent', [True, False, False, True, True]),
    ('OUTCAR.nelm-breach-partial', [True, False, True, False, True]),
    ('OUTCAR.unfinished', [False, False, False, False, False]),
    ('OUTCAR.not-converged', [True, False, True, False, False]),
]


@pytest.mark.parametrize('outcar_parser,expected', _TEST_DATA, indirect=['outcar_parser'])
def test_run_status(outcar_parser, expected):
    """Test that the status of the run is correct."""

    run_status = outcar_parser.get_run_status()
    assert run_status['finished'] is expected[0]
    assert run_status['ionic_converged'] is expected[1]
    assert run_status['electronic_converged'] is expected[2]
    assert run_status['consistent_nelm_breach'] is expected[3]
    assert run_status['contains_nelm_breach'] is expected[4]


def test_crashed_outcar(outcar_parser):
    """Test incomplete OUTCAR"""
    testdir = os.path.dirname(__file__)
    outcarfile = os.path.join(testdir, 'OUTCAR.crashed')
    with pytest.raises(SystemExit):
        _ = Outcar(file_path=outcarfile)
