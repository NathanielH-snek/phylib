# -*- coding: utf-8 -*-

"""Tests of misc utility functions."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import os.path as op
import subprocess

import numpy as np
from numpy.testing import assert_array_equal as ae
from pytest import raises, mark
from six import string_types

from .._misc import (_git_version,
                     _load_json, _save_json,
                     _load_pickle, _save_pickle,
                     _read_python,
                     _read_text,
                     _write_text,
                     _read_tsv,
                     _write_tsv,
                     _encode_qbytearray, _decode_qbytearray,
                     _fullname,
                     _load_from_fullname,
                     )


#------------------------------------------------------------------------------
# Misc tests
#------------------------------------------------------------------------------

def test_qbytearray(tempdir):
    try:
        from PyQt5.QtCore import QByteArray
    except ImportError:  # pragma: no cover
        return
    arr = QByteArray()
    arr.append('1')
    arr.append('2')
    arr.append('3')

    encoded = _encode_qbytearray(arr)
    assert isinstance(encoded, string_types)
    decoded = _decode_qbytearray(encoded)
    assert arr == decoded

    # Test JSON serialization of QByteArray.
    d = {'arr': arr}
    path = op.join(tempdir, 'test')
    _save_json(path, d)
    d_bis = _load_json(path)
    assert d == d_bis


def test_json_simple(tempdir):
    d = {'a': 1, 'b': 'bb', 3: '33', 'mock': {'mock': True}}

    path = op.join(tempdir, 'test')
    _save_json(path, d)
    d_bis = _load_json(path)
    assert d == d_bis

    with open(path, 'w') as f:
        f.write('')
    assert _load_json(path) == {}
    with raises(IOError):
        _load_json(path + '_bis')


@mark.parametrize('kind', ['json', 'pickle'])
def test_json_numpy(tempdir, kind):
    arr = np.arange(20).reshape((2, -1)).astype(np.float32)
    d = {'a': arr, 'b': arr.ravel()[:10], 'c': arr[0, 0]}

    path = op.join(tempdir, 'test')
    f = _save_json if kind == 'json' else _save_pickle
    f(path, d)

    f = _load_json if kind == 'json' else _load_pickle
    d_bis = f(path)
    arr_bis = d_bis['a']

    assert arr_bis.dtype == arr.dtype
    assert arr_bis.shape == arr.shape
    ae(arr_bis, arr)

    ae(d['b'], d_bis['b'])
    ae(d['c'], d_bis['c'])


def test_read_python(tempdir):
    path = op.join(tempdir, 'mock.py')
    with open(path, 'w') as f:
        f.write("""a = {'b': 1}""")

    assert _read_python(path) == {'a': {'b': 1}}


def test_write_text(tempdir):
    for path in (op.join(tempdir, 'test_1'),
                 op.join(tempdir, 'test_dir/test_2.txt'),
                 ):
        _write_text(path, 'hello world')
        assert _read_text(path) == 'hello world'


def test_write_tsv(tempdir):
    path = op.join(tempdir, 'test.tsv')
    assert _read_tsv(path) == {}

    data = {2: '20', 3: '30', 5: '50'}
    _write_tsv(path, 'myfield', data)

    assert _read_tsv(path) == ('myfield', data)


def test_git_version():
    v = _git_version()

    # If this test file is tracked by git, then _git_version() should succeed
    filedir, _ = op.split(__file__)
    try:
        with open(os.devnull, 'w') as fnull:
            subprocess.check_output(['git', '-C', filedir, 'status'],
                                    stderr=fnull)
            assert v != "", "git_version failed to return"
            assert v[:5] == "-git-", "Git version does not begin in -git-"
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        assert v == ""


def _myfunction(x):
    return


def test_fullname():
    assert _fullname(_myfunction) == 'phylib.utils.tests.test_misc._myfunction'

    assert _load_from_fullname(_myfunction) == _myfunction
    assert _load_from_fullname(_fullname(_myfunction)) == _myfunction
