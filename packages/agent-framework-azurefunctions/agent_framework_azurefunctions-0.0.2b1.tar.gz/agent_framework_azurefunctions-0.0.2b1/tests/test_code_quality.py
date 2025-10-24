# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import pathlib
import subprocess
import sys
import unittest

ROOT_PATH = pathlib.Path(__file__).parent.parent


class TestCodeQuality(unittest.TestCase):
    def test_mypy(self):
        """Test mypy static type checking on the durableagent module."""
        try:
            import mypy  # NoQA
        except ImportError as e:
            raise unittest.SkipTest('mypy module is missing') from e

        config_path = ROOT_PATH / 'mypy.ini'

        # Run mypy with or without config file
        cmd = [sys.executable, '-m', 'mypy']
        if config_path.exists():
            cmd.extend(['--config-file', str(config_path)])
        cmd.append('durableagent')

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(ROOT_PATH))
        except subprocess.CalledProcessError as ex:
            output = ex.stderr.decode() if ex.stderr else ex.stdout.decode()
            raise AssertionError(
                f'mypy validation failed:\n{output}') from None

    def test_flake8(self):
        """Test flake8 style checking on the durableagent module."""
        try:
            import flake8  # NoQA
        except ImportError as e:
            raise unittest.SkipTest('flake8 module is missing') from e

        config_path = ROOT_PATH / '.flake8'

        # Run flake8 with or without config file
        cmd = [sys.executable, '-m', 'flake8']
        if config_path.exists():
            cmd.extend(['--config', str(config_path)])
        cmd.append('durableagent')

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(ROOT_PATH))
        except subprocess.CalledProcessError as ex:
            output = ex.stdout.decode() if ex.stdout else ex.stderr.decode()
            raise AssertionError(
                f'flake8 validation failed:\n{output}') from None
