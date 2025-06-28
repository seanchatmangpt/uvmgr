'''Basic tests for test_substrate_project.'''

import pytest

from test_substrate_project import __version__


def test_version():
    '''Test version is defined.'''
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_import():
    '''Test package can be imported.'''
    import test_substrate_project
    assert test_substrate_project is not None