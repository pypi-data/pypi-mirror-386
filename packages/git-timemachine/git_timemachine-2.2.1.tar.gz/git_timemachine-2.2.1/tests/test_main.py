from git_timemachine.__about__ import __version__
from git_timemachine.__main__ import app


def test_version(runner):
    assert __version__ in runner.invoke(app, ['--version']).output
