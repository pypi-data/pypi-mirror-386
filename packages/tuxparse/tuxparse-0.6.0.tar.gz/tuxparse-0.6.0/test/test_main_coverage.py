#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for uncovered code in tuxparse.__main__
"""

import io
import json
import os
import pytest
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch
from tuxparse.__main__ import _is_lava_yaml_format, main, parse_args
from tuxparse.__main__ import start


class TestMainCoverage:
    """Test coverage for uncovered code in __main__.py"""

    def test_parse_args_no_stdin_input_error(self):
        """Test line 73: Error when no input provided via stdin"""
        # Mock sys.stdin.isatty() to return True (interactive terminal)
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            mock_stdin.configure_mock(**{"isatty.return_value": True})

            with patch("sys.argv", ["tuxparse", "--log-parser", "build"]):
                with pytest.raises(SystemExit):
                    parse_args()

    def test_is_lava_yaml_format_exception_handling_oserror(self):
        """Test lines 84-86: OSError exception handling in _is_lava_yaml_format"""
        mock_file = MagicMock()
        mock_file.readline.side_effect = OSError("Test OS error")

        result = _is_lava_yaml_format(mock_file)
        assert result is False

    def test_is_lava_yaml_format_exception_handling_unsupported_operation(self):
        """Test lines 84-86: UnsupportedOperation in _is_lava_yaml_format"""
        mock_file = MagicMock()
        mock_file.readline.side_effect = io.UnsupportedOperation(
            "Test unsupported operation"
        )

        result = _is_lava_yaml_format(mock_file)
        assert result is False

    def test_is_lava_yaml_format_exception_handling_general(self):
        """Test lines 87-89: General exception handling in _is_lava_yaml_format"""
        mock_file = MagicMock()
        mock_file.readline.side_effect = Exception("Test general exception")

        result = _is_lava_yaml_format(mock_file)
        assert result is False

    def test_main_debug_logging(self):
        """Test line 96: Debug logging setup"""
        test_log = "--toolchain=gcc\nmake: test"

        with patch("sys.argv", ["tuxparse", "--log-parser", "build", "--debug"]):
            with patch("sys.stdin", io.StringIO(test_log)):
                with patch("tuxparse.__main__.logger") as mock_logger:
                    try:
                        main()
                    except SystemExit:
                        pass
                    mock_logger.setLevel.assert_called_once()

    def test_debug_output_to_stderr(self):
        """Test that --debug flag outputs debug messages to stderr"""
        test_log = """[   10.000000] ==================================================================
[   10.000001] BUG: KASAN: slab-out-of-bounds in test_func+0x123/0x456
[   10.000002] Write of size 1 at addr ffff000082192373
[   10.000003] ==================================================================
[   20.000000] Normal log message
"""

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot", "--debug"]):
            with patch("sys.stdin", io.StringIO(test_log)):
                captured_stderr = StringIO()
                captured_stdout = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with patch("sys.stdout", captured_stdout):
                        try:
                            result = main()
                            assert result == 0
                        except SystemExit as e:
                            assert e.code == 0

                        stderr_content = captured_stderr.getvalue()
                        stdout_content = captured_stdout.getvalue()

                        assert "DEBUG:" in stderr_content
                        output = json.loads(stdout_content)
                        assert isinstance(output, dict)

    def test_no_debug_output_without_flag(self):
        """Test that debug messages don't appear without --debug flag"""
        test_log = """[   10.000000] Normal log message
[   20.000000] Another message
"""

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot"]):
            with patch("sys.stdin", io.StringIO(test_log)):
                captured_stderr = StringIO()
                captured_stdout = StringIO()
                with patch("sys.stderr", captured_stderr):
                    with patch("sys.stdout", captured_stdout):
                        try:
                            result = main()
                            assert result == 0
                        except SystemExit as e:
                            assert e.code == 0

                        stderr_content = captured_stderr.getvalue()
                        assert "DEBUG:" not in stderr_content

    def test_main_lava_yaml_processing(self):
        """Test lines 102-115: LAVA YAML processing"""
        lava_yaml_content = """- {"dt": "2025-01-01T00:00:00.000000", "lvl": "target", "msg": "[    0.000000] Linux version 6.16.0"}"""

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", io.StringIO(lava_yaml_content)):
                # Mock _is_lava_yaml_format to return True
                with patch("tuxparse.__main__._is_lava_yaml_format", return_value=True):
                    # Mock the logs_txt method
                    with patch(
                        "tuxparse.boot_test_parser.BootTestParser.logs_txt",
                        return_value="processed content",
                    ) as mock_logs_txt:
                        # Mock file writing
                        with patch("builtins.open", create=True) as mock_open:
                            try:
                                result = main()
                                assert result == 0
                                mock_logs_txt.assert_called_once()
                                mock_open.assert_called()
                            except SystemExit as e:
                                assert e.code == 0

    def test_main_lava_yaml_processing_exception(self):
        """Test lines 113-115: LAVA YAML processing exception handling"""
        lava_yaml_content = (
            """- {"dt": "2025-01-01T00:00:00.000000", "lvl": "target", "msg": "test"}"""
        )

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", io.StringIO(lava_yaml_content)):
                with patch("tuxparse.__main__._is_lava_yaml_format", return_value=True):
                    # Make logs_txt raise an exception
                    with patch(
                        "tuxparse.boot_test_parser.BootTestParser.logs_txt",
                        side_effect=Exception("Test error"),
                    ):
                        with patch("tuxparse.__main__.logger") as mock_logger:
                            result = main()
                            assert result == 1
                            mock_logger.error.assert_called()

    def test_main_result_file_creation(self):
        """Test lines 123-130: Result file creation and merging"""
        test_log = "--toolchain=gcc\n/builds/linux/test.c:1:1: error: test error"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            result_file = temp_file.name
            # Write existing JSON content
            temp_file.write('{"existing": "data"}')

        try:
            with patch(
                "sys.argv",
                ["tuxparse", "--log-parser", "build", "--result-file", result_file],
            ):
                with patch("sys.stdin", io.StringIO(test_log)):
                    try:
                        result = main()
                        assert result == 0
                    except SystemExit as e:
                        assert e.code == 0

                    # Check that file was updated
                    with open(result_file, "r") as f:
                        data = json.load(f)
                        assert "existing" in data
        finally:
            os.unlink(result_file)

    def test_main_result_file_new_file(self):
        """Test result file creation when file doesn't exist"""
        test_log = "--toolchain=gcc\n/builds/linux/test.c:1:1: error: test error"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=True) as temp_file:
            result_file = temp_file.name
        # File is now deleted

        try:
            with patch(
                "sys.argv",
                ["tuxparse", "--log-parser", "build", "--result-file", result_file],
            ):
                with patch("sys.stdin", io.StringIO(test_log)):
                    try:
                        result = main()
                        assert result == 0
                    except SystemExit as e:
                        assert e.code == 0

                    # Check that file was created
                    assert os.path.exists(result_file)
                    with open(result_file, "r") as f:
                        data = json.load(f)
                        assert isinstance(data, dict)
        finally:
            if os.path.exists(result_file):
                os.unlink(result_file)

    def test_main_system_exit_handling(self):
        """Test lines 132-134: SystemExit handling"""
        with patch("sys.argv", ["tuxparse", "--log-parser", "build"]):
            with patch("sys.stdin", io.StringIO("test")):
                with patch("tuxparse.__main__.parse_args", side_effect=SystemExit(2)):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 2

    def test_start_function(self):
        """Test line 139: start() function when __name__ == '__main__'"""
        # This tests the start() function path
        with patch("tuxparse.__main__.__name__", "__main__"):
            with patch("tuxparse.__main__.main", return_value=0) as mock_main:
                with patch("sys.exit") as mock_exit:
                    start()
                    mock_main.assert_called_once()
                    mock_exit.assert_called_once_with(0)

    def test_result_file_empty_content(self):
        """Test result file handling when existing file is empty"""
        test_log = "--toolchain=gcc\n/builds/linux/test.c:1:1: error: test error"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            result_file = temp_file.name
            # Write empty content
            temp_file.write("")

        try:
            with patch(
                "sys.argv",
                ["tuxparse", "--log-parser", "build", "--result-file", result_file],
            ):
                with patch("sys.stdin", io.StringIO(test_log)):
                    try:
                        result = main()
                        assert result == 0
                    except SystemExit as e:
                        assert e.code == 0

                    # Check that file was updated with new data only
                    with open(result_file, "r") as f:
                        data = json.load(f)
                        assert isinstance(data, dict)
        finally:
            os.unlink(result_file)

    def test_stdin_yaml_vs_txt_consistency(self):
        """Test that LAVA YAML via stdin produces same output as extracted console logs"""
        lava_yaml_content = """- {"dt": "2025-01-01T00:00:00.000000", "lvl": "target", "msg": "[    0.000000] Linux version 6.16.0"}
- {"dt": "2025-01-01T00:00:00.100000", "lvl": "target", "msg": "[    0.100000] Booting on CPU 0"}
- {"dt": "2025-01-01T00:00:01.000000", "lvl": "target", "msg": "debian login: root"}"""

        console_content = """[    0.000000] Linux version 6.16.0
[    0.100000] Booting on CPU 0
debian login: root"""

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", io.StringIO(lava_yaml_content)):
                with patch("builtins.open", create=True):
                    captured_yaml = StringIO()
                    with patch("sys.stdout", captured_yaml):
                        try:
                            main()
                        except SystemExit:
                            pass

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", io.StringIO(console_content)):
                captured_txt = StringIO()
                with patch("sys.stdout", captured_txt):
                    try:
                        main()
                    except SystemExit:
                        pass

        output_yaml = json.loads(captured_yaml.getvalue())
        output_txt = json.loads(captured_txt.getvalue())

        assert output_yaml == output_txt

    def test_stdin_non_seekable_lava_yaml(self):
        """Test non-seekable stdin with LAVA YAML content"""
        lava_yaml_content = """- {"dt": "2025-01-01T00:00:00.000000", "lvl": "target", "msg": "[    0.000000] Linux version 6.16.0"}
- {"dt": "2025-01-01T00:00:00.100000", "lvl": "target", "msg": "debian login: root"}"""

        mock_stdin = MagicMock()
        mock_stdin.seekable.return_value = False
        mock_stdin.read.return_value = lava_yaml_content
        mock_stdin.isatty.return_value = False

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", mock_stdin):
                with patch("builtins.open", create=True):
                    try:
                        result = main()
                        assert result == 0
                    except SystemExit as e:
                        assert e.code == 0

    def test_stdin_non_seekable_non_lava(self):
        """Test non-seekable stdin with non-LAVA content"""
        console_content = """[    0.000000] Linux version 6.16.0
debian login: root"""

        mock_stdin = MagicMock()
        mock_stdin.seekable.return_value = False
        mock_stdin.read.return_value = console_content
        mock_stdin.isatty.return_value = False

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", mock_stdin):
                try:
                    result = main()
                    assert result == 0
                except SystemExit as e:
                    assert e.code == 0

    def test_boot_parser_filters_boot_only(self):
        """Test that --log-parser boot filters to only boot results"""
        boot_and_test_content = """[    0.000000] Linux version 6.16.0
[    0.000000] Kernel panic - not syncing: VFS: Unable to mount root fs
debian login: root
[   10.000000] WARNING: CPU: 0 PID: 1 at some_file.c:123 some_function+0x123/0x456"""

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot_test"]):
            with patch("sys.stdin", io.StringIO(boot_and_test_content)):
                captured = StringIO()
                with patch("sys.stdout", captured):
                    try:
                        main()
                    except SystemExit:
                        pass

                    output = json.loads(captured.getvalue())
                    assert (
                        "log-parser-test" in output
                    ), "boot_test should create log-parser-test suite"
                    assert (
                        "log-parser-boot" in output
                    ), "boot_test should create log-parser-boot suite"

        with patch("sys.argv", ["tuxparse", "--log-parser", "boot"]):
            with patch("sys.stdin", io.StringIO(boot_and_test_content)):
                captured = StringIO()
                with patch("sys.stdout", captured):
                    try:
                        result = main()
                        assert result == 0
                    except SystemExit as e:
                        assert e.code == 0

                    output = json.loads(captured.getvalue())
                    assert (
                        "log-parser-test" not in output
                    ), "boot parser should filter out log-parser-test"
                    for key in output.keys():
                        assert "boot" in key
                    assert len(output) > 0
