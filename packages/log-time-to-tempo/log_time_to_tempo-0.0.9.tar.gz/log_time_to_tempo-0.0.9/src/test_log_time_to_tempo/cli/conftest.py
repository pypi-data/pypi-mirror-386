import os
import pathlib
import sys
from typing import Callable

import pytest
from typer.testing import CliRunner, Result

from log_time_to_tempo.cli.main import app

CallableCli = Callable[[list[str]], Result]


@pytest.fixture()
def cli(caplog, tmp_path, monkeypatch):
    # click testing and logging output might produce issues with broken streams
    # (e.g. ValueError: I/O operation on closed file.)
    # see https://github.com/pallets/click/issues/824
    # Therefore, we disable any logging output
    # caplog.set_level(100000)

    # isolate cli invocations to not modify current system
    monkeypatch.setattr('log_time_to_tempo.cli.app_dir', tmp_path / 'lt')
    monkeypatch.setattr('log_time_to_tempo.caching.cache_dir', tmp_path / 'lt' / 'cache')
    monkeypatch.setattr('log_time_to_tempo.cli.config.fp_config_default', tmp_path / '.lt')

    def invoke(*args, **kwargs) -> Result:
        runner: CliRunner = CliRunner()
        result = runner.invoke(app, *args, **kwargs)

        print('----- CLI on stdout')
        print(result.stdout, end='')
        print('-----')
        if result.stderr:
            print('----- CLI on stderr', file=sys.stderr)
            print(result.stderr, end='', file=sys.stderr)
            print('-----', file=sys.stderr)

        return result

    previous_directory = pathlib.Path.cwd()
    os.chdir(tmp_path)
    yield invoke
    os.chdir(previous_directory)
