'''Basic tests for container_demo.'''

import pytest

from container_demo import __version__


def test_version():
    '''Test version is defined.'''
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_import():
    '''Test package can be imported.'''
    import container_demo
    assert container_demo is not None