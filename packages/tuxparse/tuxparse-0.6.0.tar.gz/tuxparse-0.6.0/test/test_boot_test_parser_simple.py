#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from io import StringIO
from unittest.mock import patch, MagicMock

from tuxparse.boot_test_parser import BootTestParser, tstamp
from tuxparse.__main__ import _is_lava_yaml_format
from test.test_utils import (
    get_parser_results,
    assert_tests_created,
    assert_content_found,
    assert_multiple_patterns_detected,
    assert_no_failures_in_results,
)


def read_sample_file(name):
    """Read sample log files from test data directory"""
    if not name.startswith("/"):
        name = os.path.join(os.path.dirname(__file__), "data", name)
    try:
        return open(name).read()
    except FileNotFoundError:
        # Return a sample log if file doesn't exist
        if "oops" in name:
            return "[   14.461360] Internal error: Oops - BUG: 0 [#1] PREEMPT SMP"
        elif "panic" in name:
            return "[    0.123] Kernel panic - not syncing: Attempted to kill init! exitcode=0x00000009"
        elif "kasan" in name:
            return "==================================================================\nBUG: KASAN: slab-out-of-bounds in kmalloc_oob_right+0x190/0x3b8"
        elif "kcsan" in name:
            return "==================================================================\nBUG: KCSAN: data-race in do_page_fault spectre_v4_enable_task_mitigation"
        elif "kfence" in name:
            return "==================================================================\nBUG: KFENCE: memory corruption in kfree+0x8c/0x174"
        elif "rcu" in name:
            return "WARNING: suspicious RCU usage"
        elif "exception" in name:
            return "WARNING: CPU: 0 PID: 1 at kernel/smp.c:912 smp_call_function_many_cond+0x3c4/0x3c8"
        elif "multiple" in name:
            return """[    0.123] Kernel panic - not syncing: stack protector: Kernel stack is corrupted in
[   14.461360] WARNING: CPU: 0 PID: 1 at drivers/gpu/drm/radeon/radeon_object.c:89 radeon_ttm_bo_destroy+0xe8/0x208
[   15.123456] Internal error: Oops - BUG: 0 [#1] PREEMPT SMP
[   16.789012] Unhandled fault: external abort on non-linefetch at 0x12345678"""
        else:
            return ""


class TestBootTestParser:
    """Tests for boot_test_parser (linux_log_parser equivalent)"""

    def setup_method(self):
        self.parser = BootTestParser()

    def test_detects_oops(self):
        """Test detection of kernel oops"""
        log = read_sample_file("oops.log")
        data = self.parser.parse_log(log, unique=False)

        # Test data structure directly instead of JSON dumps
        assert data, "Should detect issues in oops log"
        boot_tests = get_parser_results(data, "boot")

        # Verify oops-related tests were created and contain expected content
        assert_tests_created(boot_tests, "oops", "Should detect oops patterns")
        assert_content_found(
            boot_tests,
            "oops",
            ["Internal error: Oops", "Oops - BUG:"],
            "Should capture oops error messages",
        )

    def test_detects_kernel_panic(self):
        """Test detection of kernel panic"""
        log = read_sample_file("kernelpanic-single-and-multiline.log")
        data = self.parser.parse_log(log, unique=False)

        # Test data structure directly instead of JSON dumps
        assert data, "Should detect issues in panic log"
        boot_tests = get_parser_results(data, "boot")

        # Verify panic-related tests were created and contain expected content
        assert_tests_created(boot_tests, "panic", "Should detect panic patterns")
        assert_content_found(
            boot_tests,
            "panic",
            ["Kernel panic - not syncing"],
            "Should capture panic messages",
        )

    def test_detects_kernel_exception(self):
        """Test detection of kernel exceptions/warnings"""
        log = read_sample_file("kernelexceptiontrace.log")
        data = self.parser.parse_log(log, unique=False)

        assert data, "Should detect issues in exception log"
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        # Check that warning/exception-related tests were created
        warning_tests = [
            name
            for name in boot_tests.keys()
            if "warning" in name.lower() or "exception" in name.lower()
        ]
        assert len(warning_tests) > 0, "Should detect warning/exception patterns"

        # Verify the log content contains expected warning indicators
        found_warning_content = False
        for test_name, test_data in boot_tests.items():
            if "warning" in test_name.lower() or "exception" in test_name.lower():
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "WARNING: CPU:" in line or "smp_call_function_many_cond" in line:
                        found_warning_content = True
                        break
        assert found_warning_content, "Should capture warning/exception messages"

    def test_detects_kernel_kasan(self):
        """Test detection of KASAN issues"""
        log = read_sample_file("kasan.log")
        data = self.parser.parse_log(log, unique=False)

        assert data, "Should detect issues in KASAN log"
        boot_tests = get_parser_results(data, "boot")

        # Verify KASAN-related tests were created and contain expected content
        assert_tests_created(boot_tests, "kasan", "Should detect KASAN patterns")
        assert_content_found(
            boot_tests, "kasan", ["BUG: KASAN:"], "Should capture KASAN bug messages"
        )

    def test_detects_kernel_kcsan(self):
        """Test detection of KCSAN issues"""
        log = read_sample_file("kcsan_simple.log")
        data = self.parser.parse_log(log, unique=False)

        assert data, "Should detect issues in KCSAN log"
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        # Check that KCSAN-related tests were created
        kcsan_tests = [name for name in boot_tests.keys() if "kcsan" in name.lower()]
        assert len(kcsan_tests) > 0, "Should detect KCSAN patterns"

        # Verify the log content contains expected KCSAN indicators
        found_kcsan_content = False
        for test_name, test_data in boot_tests.items():
            if "kcsan" in test_name.lower():
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "BUG: KCSAN:" in line or "data-race" in line:
                        found_kcsan_content = True
                        break
        assert found_kcsan_content, "Should capture KCSAN bug or data-race messages"

    def test_detects_kernel_kfence(self):
        """Test detection of KFENCE issues"""
        log = read_sample_file("kfence.log")
        data = self.parser.parse_log(log, unique=False)

        # Test data structure directly instead of JSON dumps
        assert data, "Should detect issues in KFENCE log"

        # KFENCE might be categorized under different parser types
        if "log-parser-boot" in data:
            boot_tests = data["log-parser-boot"]
        elif "log-parser-test" in data:
            boot_tests = data["log-parser-test"]
        else:
            assert (
                False
            ), f"Should have parser results under log-parser-boot or log-parser-test, got keys: {list(data.keys())}"

        # Verify KFENCE-related tests were created
        kfence_tests = [name for name in boot_tests.keys() if "kfence" in name.lower()]
        assert len(kfence_tests) > 0, "Should detect KFENCE patterns"

        # Verify log excerpts contain expected KFENCE indicators
        found_kfence_content = False
        for test_name, test_data in boot_tests.items():
            if "kfence" in test_name.lower():
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "BUG: KFENCE:" in line or "memory corruption" in line:
                        found_kfence_content = True
                        break
        assert (
            found_kfence_content
        ), "Should capture KFENCE bug or memory corruption messages"

    def test_detects_kernel_ubsan_warning(self):
        ubsan_log = """[    0.000000] Booting Linux on physical CPU 0x0
[    5.123457] UBSAN: array-index-out-of-bounds in fs/ext4/super.c:1234:56
[    5.123458] index 10 is out of range for type int[5]
[    5.123459] CPU: 0 PID: 1234 Comm: mount Not tainted 6.16.0-rc3 #1
[    5.123460] Hardware name: Test Board
[    5.123461] Call Trace:
[    5.123462] ext4_fill_super+0x12c/0x890
[    5.123463] ---[ end trace 0000000000000000 ]---
[    6.000000] Normal boot continues"""

        data = self.parser.parse_log(ubsan_log, unique=False)

        assert data
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        ubsan_tests = [name for name in boot_tests.keys() if "ubsan" in name.lower()]
        assert len(ubsan_tests) > 0

        assert_content_found(
            boot_tests,
            "ubsan",
            ["UBSAN: array-index-out-of-bounds"],
            "Should capture UBSAN array bounds violation",
        )

    def test_detects_kernel_ubsan_panic(self):
        ubsan_panic_log = """[    0.000000] Booting Linux on physical CPU 0x0
[    7.234568] UBSAN: integer subtraction overflow in drivers/example.c:456:78
[    7.234569] signed integer overflow: 5 - 10 cannot be represented in type 'int'
[    7.234570] CPU: 0 PID: 1234 Comm: test Not tainted 6.16.0-rc3 #1
[    7.234571] Call Trace:
[    7.234572] some_function+0x120/0x890
[    7.234573] ---[ end trace 0000000000000000 ]---
[    7.234574] Kernel panic - not syncing: UBSAN: integer subtraction overflow: Fatal exception
[    8.000000] System halted"""

        data = self.parser.parse_log(ubsan_panic_log, unique=False)

        assert data
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        ubsan_tests = [name for name in boot_tests.keys() if "ubsan" in name.lower()]
        assert len(ubsan_tests) > 0

        assert_content_found(
            boot_tests,
            "ubsan",
            ["UBSAN: integer subtraction overflow", "Fatal exception"],
            "Should capture UBSAN panic with fatal exception",
        )

    def test_detects_rcu_warning(self):
        """Test detection of RCU warnings"""
        log = read_sample_file("rcu_warning.log")
        data = self.parser.parse_log(log, unique=False)

        assert data, "Should detect issues in RCU warning log"
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        # Check that RCU or warning-related tests were created
        rcu_tests = [
            name
            for name in boot_tests.keys()
            if "rcu" in name.lower() or "warning" in name.lower()
        ]
        assert len(rcu_tests) > 0, "Should detect RCU/warning patterns"

        # Verify the log content contains expected RCU indicators
        found_rcu_content = False
        for test_name, test_data in boot_tests.items():
            if "rcu" in test_name.lower() or "warning" in test_name.lower():
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "WARNING: suspicious RCU usage" in line or "RCU" in line:
                        found_rcu_content = True
                        break
        assert found_rcu_content, "Should capture RCU warning messages"

    def test_detects_multiple_issues(self):
        """Test detection of multiple issues in one log"""
        log = read_sample_file("multiple_issues_dmesg.log")
        data = self.parser.parse_log(log, unique=False)

        # Test data structure directly instead of JSON dumps
        assert data, "Should detect issues in multi-issue log"
        boot_tests = get_parser_results(data, "boot")

        # Should detect multiple types of issues
        issue_types = ["panic", "warning", "oops", "fault"]
        assert_multiple_patterns_detected(
            boot_tests, issue_types, min_patterns=2, context="multiple issues log"
        )

    def test_no_false_positives_empty_log(self):
        """Test that empty logs don't generate false positives"""
        data = self.parser.parse_log("", unique=False)

        # Test data structure directly - empty logs should not create test results
        assert not data or not data.get(
            "log-parser-boot"
        ), "Empty log should not generate any boot tests"

    def test_no_false_positives_normal_log(self):
        """Test that normal boot logs don't generate false positives"""
        normal_log = """[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd034]
[    0.000000] Linux version 4.4.89-01529-gb29bace (buildslave@x15-build-21)
[    0.000000] Boot CPU: AArch64 Processor [410fd034]
[    0.000000] efi: Getting EFI parameters from /chosen:
[    1.234567] systemd[1]: Started Update UTMP about System Runlevel Changes.
Ubuntu 20.04 LTS device login: """

        data = self.parser.parse_log(normal_log, unique=False)

        # Test data structure directly - normal boot messages should not create failed tests
        # It's acceptable for normal logs to create no tests (no false positives)
        if data and "log-parser-boot" in data:
            boot_tests = data["log-parser-boot"]
            assert_no_failures_in_results(boot_tests, "normal boot log")
        # If no tests created, that's also acceptable for normal boot logs

    def test_unique_flag_functionality(self):
        """Test that unique flag works"""
        # Test with duplicate entries
        duplicate_log = """[    0.123] Kernel panic - not syncing: test
[    0.456] Kernel panic - not syncing: test"""

        data_unique = self.parser.parse_log(duplicate_log, unique=True)
        data_not_unique = self.parser.parse_log(duplicate_log, unique=False)

        # Test data structures directly instead of JSON dumps
        assert (
            data_unique and "log-parser-boot" in data_unique
        ), "Unique parsing should produce results"
        assert (
            data_not_unique and "log-parser-boot" in data_not_unique
        ), "Non-unique parsing should produce results"

        unique_tests = data_unique["log-parser-boot"]
        not_unique_tests = data_not_unique["log-parser-boot"]

        # Both should have detected the panic
        assert len(unique_tests) > 0, "Unique parsing should detect tests"
        assert len(not_unique_tests) > 0, "Non-unique parsing should detect tests"

    def test_is_lava_yaml_format_with_valid_lava_yaml(self):
        """Test _is_lava_yaml_format with valid LAVA YAML format"""
        lava_content = StringIO(
            '- {dt: 2023-01-01T00:00:00.000000, lvl: target, msg: "test"}'
        )
        result = _is_lava_yaml_format(lava_content)
        assert result is True

    def test_is_lava_yaml_format_with_plain_text(self):
        """Test _is_lava_yaml_format with plain text format"""
        plain_content = StringIO("[    0.000000] Kernel panic - not syncing: test")
        result = _is_lava_yaml_format(plain_content)
        assert result is False

    def test_is_lava_yaml_format_with_empty_input(self):
        """Test _is_lava_yaml_format with empty input"""
        empty_content = StringIO("")
        result = _is_lava_yaml_format(empty_content)
        assert result is False

    def test_is_lava_yaml_format_with_non_seekable_stream(self):
        """Test _is_lava_yaml_format with non-seekable stream"""
        mock_stream = MagicMock()
        mock_stream.readline.return_value = (
            '- {dt: 2023-01-01T00:00:00.000000, lvl: target, msg: "test"}'
        )
        mock_stream.seek.side_effect = OSError("Stream is not seekable")

        result = _is_lava_yaml_format(mock_stream)
        assert result is False  # Should return False for safety

    def test_parse_lava_log_entry_with_valid_yaml(self):
        """Test _parse_lava_log_entry with valid YAML"""
        valid_entry = (
            '- {dt: 2023-01-01T00:00:00.000000, lvl: target, msg: "test message"}'
        )
        result = self.parser._parse_lava_log_entry(valid_entry)

        assert result is not None
        assert result["lvl"] == "target"
        assert result["msg"] == "test message"

    def test_parse_lava_log_entry_with_invalid_yaml(self):
        """Test _parse_lava_log_entry with invalid YAML"""
        invalid_entry = "invalid yaml format"
        result = self.parser._parse_lava_log_entry(invalid_entry)
        assert result is None

    def test_parse_lava_log_entry_with_missing_fields(self):
        """Test _parse_lava_log_entry with missing required fields"""
        missing_fields = (
            '- {timestamp: 2023-01-01T00:00:00.000000, level: target, message: "test"}'
        )
        result = self.parser._parse_lava_log_entry(missing_fields)
        assert result is None

    def test_logs_txt_with_dict_msg(self):
        """Test logs_txt method handles dict messages properly"""
        dict_msg_yaml = "- {dt: 2023-01-01T00:00:00.000000, lvl: target, msg: {result: pass, test: example}}"
        result = self.parser.logs_txt(dict_msg_yaml)

        assert result is not None
        assert "result" in result

    def test_logs_txt_with_namespace_feedback(self):
        """Test logs_txt method handles namespace feedback properly"""
        feedback_yaml = '- {dt: 2023-01-01T00:00:00.000000, lvl: feedback, ns: "test-ns", msg: "feedback message"}'
        result = self.parser.logs_txt(feedback_yaml)

        assert "<test-ns> feedback message" in result

    def test_parse_log_with_empty_file_object(self):
        """Test parse_log with empty file object"""
        empty_file = StringIO("")
        result = self.parser.parse_log(empty_file, False)
        assert not result

    def test_parse_log_with_file_object_input(self):
        """Test parse_log with file object input"""
        log_content = StringIO("[    0.000000] Kernel panic - not syncing: test panic")
        result = self.parser.parse_log(log_content, False)

        assert result
        assert "log-parser-boot" in result

    def test_parse_log_error_handling(self):
        """Test parse_log error handling with invalid input"""
        mock_file = MagicMock()
        mock_file.read.side_effect = Exception("Read error")

        with patch("tuxparse.boot_test_parser.logger") as mock_logger:
            result = self.parser.parse_log(mock_file, False)
            assert not result
            mock_logger.error.assert_called()

    # Tests for syslog priority format support
    def test_timestamp_pattern_traditional_format(self):
        """Test timestamp pattern matching with traditional kernel timestamps"""

        # Traditional timestamp formats
        traditional_lines = [
            "[    0.000000] Linux version 6.16.0-rc6",
            "[   12.345678] Memory: 222472K/262144K available",
            "[  123.456789] Kernel panic - not syncing: test panic",
            "[    0.123456] WARNING: CPU: 0 PID: 1 at kernel/test.c:123",
        ]

        for line in traditional_lines:
            match = re.search(tstamp, line)
            assert match is not None, f"Should match traditional timestamp in: {line}"
            assert match.group().startswith(
                "["
            ), f"Should capture timestamp bracket in: {line}"

    def test_timestamp_pattern_syslog_format(self):
        """Test timestamp pattern matching with syslog priority format"""

        # Syslog priority formats
        syslog_excerpt = [
            "<0>Internal error: Oops: 805 [#1] ARM",
            "<4>WARNING: kernel/irq/manage.c:1829 at free_irq+0xe8/0x324",
            "<6>printk: log buffer data + meta data: 524288 bytes",
            '<5>Unknown kernel command line parameters "verbose"',
        ]

        for line in syslog_excerpt:
            match = re.search(tstamp, line)
            assert match is not None, f"Should match syslog priority in: {line}"
            assert match.group().startswith("<") and match.group().endswith(
                ">"
            ), f"Should capture priority in: {line}"

    def test_timestamp_pattern_mixed_formats(self):
        """Test that timestamp pattern handles both formats in same log"""

        mixed_lines = [
            "[    0.000000] Linux version 6.16.0-rc6",
            "<4>WARNING: kernel/irq/manage.c:1829 at free_irq+0xe8/0x324",
            "[   12.345678] Memory: 222472K/262144K available",
            "<6>printk: log buffer data + meta data: 524288 bytes",
            "Regular line without timestamp",
        ]

        matched_count = 0
        for line in mixed_lines:
            match = re.search(tstamp, line)
            if match:
                matched_count += 1

        assert matched_count == 4, "Should match 4 timestamped lines out of 5"

    def test_kernel_msgs_only_traditional_format(self):
        """Test __kernel_msgs_only extraction with traditional timestamps"""
        log_content = """Some regular output
[    0.000000] Linux version 6.16.0-rc6
[   12.345678] Memory: 222472K/262144K available
[  123.456789] Kernel panic - not syncing: test panic
Regular user output
[    0.123456] WARNING: CPU: 0 PID: 1 at kernel/test.c:123
More regular output"""

        kernel_msgs = self.parser._BootTestParser__kernel_msgs_only(log_content)
        lines = [line for line in kernel_msgs.split("\n") if line.strip()]

        assert len(lines) == 4, f"Should extract 4 kernel messages, got {len(lines)}"
        assert "Linux version 6.16.0-rc6" in kernel_msgs
        assert "Kernel panic - not syncing" in kernel_msgs
        assert "WARNING: CPU: 0 PID: 1" in kernel_msgs
        assert "Regular user output" not in kernel_msgs

    def test_kernel_msgs_only_syslog_format(self):
        """Test __kernel_msgs_only extraction with syslog priority format"""
        log_content = """ALSA lib confmisc.c:855:(parse_card) cannot find card '0'
<0>Internal error: Oops: 805 [#1] ARM
<4>WARNING: kernel/irq/manage.c:1829 at free_irq+0xe8/0x324, CPU#0: kunit_try_catch/80
<6>printk: log buffer data + meta data: 524288 + 1638400 = 2162688 bytes
<5>Unknown kernel command line parameters "verbose", will be passed to user space.
alsa: Could not initialize DAC"""

        kernel_msgs = self.parser._BootTestParser__kernel_msgs_only(log_content)
        lines = [line for line in kernel_msgs.split("\n") if line.strip()]

        assert len(lines) == 4, f"Should extract 4 kernel messages, got {len(lines)}"
        assert "Internal error: Oops: 805" in kernel_msgs
        assert "WARNING: kernel/irq/manage.c:1829" in kernel_msgs
        assert "printk: log buffer data" in kernel_msgs
        assert "Unknown kernel command line parameters" in kernel_msgs
        assert "ALSA lib confmisc.c" not in kernel_msgs
        assert "alsa: Could not initialize DAC" not in kernel_msgs

    def test_kernel_msgs_only_mixed_formats(self):
        """Test __kernel_msgs_only extraction with mixed timestamp formats"""
        log_content = """Regular output
[    0.000000] Linux version 6.16.0-rc6
<4>WARNING: kernel/irq/manage.c:1829 at free_irq+0xe8/0x324
[   12.345678] Memory: 222472K/262144K available
<6>printk: log buffer data + meta data: 524288 bytes
More regular output"""

        kernel_msgs = self.parser._BootTestParser__kernel_msgs_only(log_content)
        lines = [line for line in kernel_msgs.split("\n") if line.strip()]

        assert len(lines) == 4, f"Should extract 4 kernel messages, got {len(lines)}"
        assert "Linux version 6.16.0-rc6" in kernel_msgs
        assert "WARNING: kernel/irq/manage.c:1829" in kernel_msgs
        assert "Memory: 222472K/262144K available" in kernel_msgs
        assert "printk: log buffer data" in kernel_msgs
        assert "Regular output" not in kernel_msgs

    def test_parse_log_syslog_warning_detection(self):
        """Test that parse_log detects WARNING with syslog priority format"""
        syslog_warning_log = """<4>WARNING: kernel/irq/manage.c:1829 at free_irq+0xe8/0x324, CPU#0: kunit_try_catch/80
<6>printk: log buffer data + meta data: 524288 + 1638400 = 2162688 bytes
<4>WARNING: lib/math/int_log.c:63 at intlog2+0x80/0x94, CPU#0: kunit_try_catch/413"""

        result = self.parser.parse_log(syslog_warning_log, unique=False)

        assert result is not None
        assert "log-parser-boot" in result
        boot_tests = result["log-parser-boot"]

        # Should detect WARNING patterns
        warning_tests = [name for name in boot_tests.keys() if "warning" in name]
        assert len(warning_tests) > 0, "Should detect WARNING patterns in syslog format"

        # Check that the warning content is captured
        found_irq_warning = False
        found_intlog_warning = False
        for test_name, test_data in boot_tests.items():
            if "warning" in test_name:
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "kernel/irq/manage.c:1829" in line:
                        found_irq_warning = True
                    if "lib/math/int_log.c:63" in line:
                        found_intlog_warning = True

        assert found_irq_warning, "Should capture IRQ management warning"
        assert found_intlog_warning, "Should capture intlog warning"

    def test_parse_log_syslog_oops_detection(self):
        """Test that parse_log detects Oops with syslog priority format"""
        syslog_oops_log = """<6>printk: log buffer data + meta data: 524288 + 1638400 = 2162688 bytes
<0>Internal error: Oops: 805 [#1] ARM
<4>Tainted: [W]=WARN, [N]=TEST"""

        result = self.parser.parse_log(syslog_oops_log, unique=False)

        assert result is not None
        assert "log-parser-boot" in result
        boot_tests = result["log-parser-boot"]

        # Should detect Oops patterns
        oops_tests = [name for name in boot_tests.keys() if "oops" in name]
        assert len(oops_tests) > 0, "Should detect Oops patterns in syslog format"

        # Check that the oops content is captured
        found_oops = False
        for test_name, test_data in boot_tests.items():
            if "oops" in test_name:
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "Internal error: Oops: 805" in line:
                        found_oops = True

        assert found_oops, "Should capture Oops error message"

    def test_parse_log_traditional_vs_syslog_equivalence(self):
        """Test that both timestamp formats detect the same patterns"""
        # Traditional timestamp format
        traditional_log = """[    0.000000] Linux version 6.16.0-rc6
[   12.345678] WARNING: kernel/test.c:123 at test_function+0x20/0x30
[  123.456789] Internal error: Oops: 805 [#1] ARM"""

        # Syslog priority format
        syslog_log = """<6>Linux version 6.16.0-rc6
<4>WARNING: kernel/test.c:123 at test_function+0x20/0x30
<0>Internal error: Oops: 805 [#1] ARM"""

        traditional_result = self.parser.parse_log(traditional_log, unique=False)
        syslog_result = self.parser.parse_log(syslog_log, unique=False)

        # Both should detect the same number of boot tests
        traditional_count = len(traditional_result.get("log-parser-boot", {}))
        syslog_count = len(syslog_result.get("log-parser-boot", {}))

        assert (
            traditional_count == syslog_count
        ), f"Should detect same number of tests: traditional={traditional_count}, syslog={syslog_count}"
        assert traditional_count > 0, "Should detect some tests"

        # Both should detect WARNING and Oops
        traditional_tests = set(traditional_result.get("log-parser-boot", {}).keys())
        syslog_tests = set(syslog_result.get("log-parser-boot", {}).keys())

        traditional_types = set(name.split("-")[0] for name in traditional_tests)
        syslog_types = set(name.split("-")[0] for name in syslog_tests)

        assert traditional_types == syslog_types, "Should detect same test types"
        assert "warning" in traditional_types, "Should detect WARNING in both formats"
        assert "oops" in traditional_types, "Should detect Oops in both formats"

    def test_backward_compatibility_traditional_format(self):
        """Test that traditional timestamp format still works after syslog support"""
        # This test ensures we didn't break existing functionality
        traditional_kernel_log = """[    0.000000] Linux version 6.16.0-rc6-next-20250715
[    0.123456] Memory: 222472K/262144K available
[   12.345678] Kernel panic - not syncing: stack protector
[   14.461360] WARNING: CPU: 0 PID: 1 at drivers/gpu/drm/radeon/radeon_object.c:89
[   15.123456] Internal error: Oops - BUG: 0 [#1] PREEMPT SMP
[   16.789012] Unhandled fault: external abort on non-linefetch"""

        result = self.parser.parse_log(traditional_kernel_log, unique=False)

        assert result is not None
        assert "log-parser-boot" in result
        boot_tests = result["log-parser-boot"]

        # Should detect multiple issue types
        test_types = set(name.split("-")[0] for name in boot_tests.keys())
        assert "panic" in test_types, "Should detect panic"
        assert "warning" in test_types, "Should detect warning"
        assert "oops" in test_types, "Should detect oops"
        assert "fault" in test_types, "Should detect fault"

        # Verify content is captured correctly
        for test_name, test_data in boot_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])
            assert len(log_excerpt) > 0, f"Test {test_name} should have log lines"
            # Check that we have meaningful content (not just empty lines)
            meaningful_lines = [line for line in log_excerpt if line.strip()]
            assert (
                len(meaningful_lines) > 0
            ), f"Test {test_name} should have meaningful content"

    def test_detects_oom(self):
        """Test detection of OOM (Out of Memory) killer patterns"""
        oom_log = """[  230.984697] oom01 invoked oom-killer: gfp_mask=0x140dca(GFP_HIGHUSER_MOVABLE|__GFP_ZERO|__GFP_COMP), order=0, oom_score_adj=0
[  230.984717] CPU: 87 UID: 0 PID: 296892 Comm: oom01 Not tainted 6.16.0-rc6-next-20250717 #1 PREEMPT
[  230.984721] Hardware name: Inspur NF5280R7/Mitchell MB, BIOS 04.04.00004001 2025-02-04 22:23:30 02/04/2025
[  230.984724] Call trace:
[  230.984726]  show_stack+0x20/0x38 (C)
[  230.984734]  dump_stack_lvl+0xbc/0xd0
[  230.984738]  dump_stack+0x18/0x28
[  230.984739]  dump_header+0x44/0x1a8
[  230.984745]  oom_kill_process+0x138/0x360
[  230.984749]  out_of_memory+0xec/0x590
[  230.984823] Mem-Info:
[  230.984849] active_anon:21 inactive_anon:130365016 isolated_anon:0
[  230.984849]  active_file:0 inactive_file:1675 isolated_file:0
[  230.984849]  unevictable:0 dirty:0 writeback:1
[  230.987905] Out of memory: Killed process 296779 (oom01) total-vm:602413548kB, anon-rss:521275392kB, file-rss:1536kB, shmem-rss:0kB, UID:0 pgtables:1021952kB oom_score_adj:0"""

        data = self.parser.parse_log(oom_log, unique=False)

        assert data, "Should detect issues in OOM log"
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        # Check that OOM-related tests were created
        oom_tests = [name for name in boot_tests.keys() if "oom" in name.lower()]
        assert len(oom_tests) > 0, "Should detect OOM patterns"

        # Verify that the key OOM information is captured
        found_oom_killer = False
        found_killed_process = False
        for test_name, test_data in boot_tests.items():
            if "oom" in test_name.lower():
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "oom-killer" in line:
                        found_oom_killer = True
                    if "Out of memory: Killed process" in line:
                        found_killed_process = True

        assert found_oom_killer, "Should capture oom-killer invocation"
        assert found_killed_process, "Should capture killed process message"

    def test_detects_oom_syslog_format(self):
        """Test detection of OOM with syslog priority format"""
        oom_syslog_log = """<0>oom01 invoked oom-killer: gfp_mask=0x140dca(GFP_HIGHUSER_MOVABLE|__GFP_ZERO|__GFP_COMP), order=0, oom_score_adj=0
<4>CPU: 87 UID: 0 PID: 296892 Comm: oom01 Not tainted 6.16.0-rc6-next-20250717 #1 PREEMPT
<6>Hardware name: Inspur NF5280R7/Mitchell MB, BIOS 04.04.00004001 2025-02-04 22:23:30 02/04/2025
<4>Call trace:
<4> show_stack+0x20/0x38 (C)
<4> dump_stack_lvl+0xbc/0xd0
<4> dump_stack+0x18/0x28
<4> dump_header+0x44/0x1a8
<4> oom_kill_process+0x138/0x360
<4> out_of_memory+0xec/0x590
<6>Mem-Info:
<6>active_anon:21 inactive_anon:130365016 isolated_anon:0
<6> active_file:0 inactive_file:1675 isolated_file:0
<6> unevictable:0 dirty:0 writeback:1
<0>Out of memory: Killed process 296779 (oom01) total-vm:602413548kB, anon-rss:521275392kB, file-rss:1536kB, shmem-rss:0kB, UID:0 pgtables:1021952kB oom_score_adj:0"""

        result = self.parser.parse_log(oom_syslog_log, unique=False)

        assert result is not None
        assert "log-parser-boot" in result
        boot_tests = result["log-parser-boot"]

        # Should detect OOM patterns
        oom_tests = [name for name in boot_tests.keys() if "oom" in name]
        assert len(oom_tests) > 0, "Should detect OOM patterns in syslog format"

        # Check that the key OOM content is captured
        found_oom_killer = False
        found_killed_process = False
        for test_name, test_data in boot_tests.items():
            if "oom" in test_name:
                log_excerpt = test_data.get("log_excerpt", [])
                for line in log_excerpt:
                    if "oom-killer" in line:
                        found_oom_killer = True
                    if "Out of memory: Killed process" in line:
                        found_killed_process = True

        assert found_oom_killer, "Should capture OOM killer invocation"
        assert found_killed_process, "Should capture killed process message"

    def test_boot_log_no_patterns_matched_feature(self):
        """Test the unknown-boot-failure feature for boot issues with no detectable patterns"""
        boot_issue_log = """[    0.000000] Booting Linux on physical CPU 0x0
[    0.000000] Linux version 5.15.0-test
[    0.000000] CPU: ARMv8 Processor
[    0.000000] Machine model: Test Board
[    0.000000] Memory: 1024MB available
[    0.000000] Kernel command line: console=ttyS0,115200
[    0.000000] PID hash table entries: 512
[    0.000000] Dentry cache hash table entries: 8192
[    0.000000] Inode-cache hash table entries: 4096
[    0.000000] Mount-cache hash table entries: 1024
[    0.000000] CPU0: thread -1, cpu 0, socket 0, mpidr 80000000
[    0.000000] Setting up static identity map
[    0.000000] Brought up 1 CPUs
[    0.000000] Normal boot process continuing"""

        data = self.parser.parse_log(boot_issue_log, unique=False)

        assert data, "Should create data for boot issue without detectable patterns"
        assert "log-parser-boot" in data, "Should create boot parser results"
        boot_tests = data["log-parser-boot"]

        no_pattern_tests = [
            name
            for name in boot_tests.keys()
            if name.startswith("unknown-boot-failure-")
        ]
        assert (
            len(no_pattern_tests) > 0
        ), "Should create unknown-boot-failure test with SHA"

        no_pattern_test = boot_tests[no_pattern_tests[0]]
        log_excerpt = no_pattern_test["log_excerpt"]

        expected_line_count = min(20, len(boot_issue_log.strip().split("\n")))
        assert (
            len(log_excerpt) == expected_line_count
        ), f"Should capture {expected_line_count} lines"

        assert (
            "Normal boot process continuing" in log_excerpt[-1]
        ), "Should capture the last line"

        assert no_pattern_test["result"] == "fail", "Should mark as failed test"

    def test_boot_log_no_patterns_matched_not_triggered_with_login(self):
        """Test that unknown-boot-failure is NOT created when login prompt is present"""
        successful_boot_log = """[    0.000000] Booting Linux on physical CPU 0x0
[    0.000000] Linux version 5.15.0-test
[    0.000000] CPU: ARMv8 Processor
[    0.000000] Machine model: Test Board
[    0.000000] Memory: 1024MB available
[    0.000000] Kernel command line: console=ttyS0,115200
[    0.000000] PID hash table entries: 512
[    0.000000] Dentry cache hash table entries: 8192
[    0.000000] Inode-cache hash table entries: 4096
[    0.000000] Mount-cache hash table entries: 1024
[    0.000000] CPU0: thread -1, cpu 0, socket 0, mpidr 80000000
[    0.000000] Setting up static identity map
[    0.000000] Brought up 1 CPUs
[    0.000000] Normal boot process continuing
Ubuntu 20.04 LTS device login: """

        data = self.parser.parse_log(successful_boot_log, unique=False)

        if data and "log-parser-boot" in data:
            boot_tests = data["log-parser-boot"]
            no_pattern_tests = [
                name
                for name in boot_tests.keys()
                if name.startswith("unknown-boot-failure-")
            ]
            assert (
                len(no_pattern_tests) == 0
            ), "Should not create no-patterns-matched test when login prompt is present"

    def test_boot_log_no_patterns_matched_not_triggered_with_detected_patterns(self):
        """Test that unknown-boot-failure is NOT created when error patterns are detected"""
        boot_issue_with_panic = """[    0.000000] Booting Linux on physical CPU 0x0
[    0.000000] Linux version 5.15.0-test
[    0.000000] CPU: ARMv8 Processor
[    0.000000] Memory: 1024MB available
[    0.123000] Kernel panic - not syncing: Attempted to kill init!
[    0.124000] CPU: 0 PID: 1 Comm: swapper/0"""

        data = self.parser.parse_log(boot_issue_with_panic, unique=False)

        assert data, "Should create data for boot with detected patterns"
        assert "log-parser-boot" in data, "Should create boot parser results"
        boot_tests = data["log-parser-boot"]

        panic_tests = [name for name in boot_tests.keys() if "panic" in name.lower()]
        assert len(panic_tests) > 0, "Should detect panic pattern"

        no_pattern_tests = [
            name
            for name in boot_tests.keys()
            if name.startswith("unknown-boot-failure-")
        ]
        assert (
            len(no_pattern_tests) == 0
        ), "Should not create no-patterns-matched test when error patterns are detected"

    def test_no_false_positive_vbmeta_debug_message(self):
        """Test that vbmeta DEBUG messages don't trigger false BUG patterns"""
        vbmeta_log = """[   3.492479] [I] [decon0] sel(0x0) OFIFO.0 - dsimavb_slot_verify.c:948: DEBUG: vbmeta_a: VERIFICATION_DISABLED bit is set.
[   3.500000] Normal boot continues
[   4.000000] BUG: actual kernel bug here
[   4.100000] More normal output"""

        data = self.parser.parse_log(vbmeta_log, unique=False)

        assert data, "Should process the log"
        assert "log-parser-boot" in data
        boot_tests = data["log-parser-boot"]

        assert_tests_created(boot_tests, "bug", "Should detect bug patterns")
        assert_content_found(
            boot_tests,
            "bug",
            ["BUG: actual kernel bug here"],
            "Should capture real kernel bug",
        )

        debug_found = any(
            "DEBUG: vbmeta_a: VERIFICATION_DISABLED" in line
            for test_data in boot_tests.values()
            for line in test_data.get("log_excerpt", [])
        )
        assert not debug_found, "Should NOT detect vbmeta DEBUG as a bug"

    def test_cutoff_boot_log_method_directly(self):
        """Test the __cutoff_boot_log method directly for coverage."""
        log_with_login = """[0.000] Boot message 1
[1.000] Boot message 2
testhost login: user
[2.000] Test message 1"""

        boot_log, test_log = self.parser._BootTestParser__cutoff_boot_log(
            log_with_login
        )
        assert "Boot message 1" in boot_log
        assert "Boot message 2" in boot_log
        assert "login:" in test_log
        assert "Test message 1" in test_log

        log_with_console = """[0.000] Boot message 1
[1.000] Boot message 2
console:/
[2.000] Test message 1"""

        boot_log, test_log = self.parser._BootTestParser__cutoff_boot_log(
            log_with_console
        )
        assert "Boot message 1" in boot_log
        assert "Boot message 2" in boot_log
        assert "console:/" in test_log
        assert "Test message 1" in test_log

        log_with_root = """[0.000] Boot message 1
[1.000] Boot message 2
root@device:~#
[2.000] Test message 1"""

        boot_log, test_log = self.parser._BootTestParser__cutoff_boot_log(log_with_root)
        assert "Boot message 1" in boot_log
        assert "Boot message 2" in boot_log
        assert "root@device:~#" in test_log
        assert "Test message 1" in test_log

        log_without_login = """[0.000] Boot message 1
[1.000] Boot message 2
[2.000] Boot message 3"""

        boot_log, test_log = self.parser._BootTestParser__cutoff_boot_log(
            log_without_login
        )
        assert boot_log == log_without_login
        assert test_log == ""

    def test_login_pattern_variations(self):
        """Test various login pattern formats."""
        login_patterns = [
            "device login:",
            "hostname login:",
            "ubuntu login:",
            "debian login:",
            "login:",
            "console:/",
            "root@host:/#",
            "root@device:~#",
            "user@system:/home/user#",
        ]

        for pattern in login_patterns:
            log = f"""[0.000] Boot messages
[1.000] More boot messages
{pattern}
[2.000] Test messages after login"""

            data = self.parser.parse_log(log, unique=False)
            assert isinstance(data, dict), f"Should return dict for pattern: {pattern}"

    def test_chunked_processing_direct_method_calls(self):
        """Test chunked processing method variants for coverage."""
        large_log = """[0.000] Boot message 1
[1.000] WARNING: test warning
testhost login: user
[2.000] Test message 1
[3.000] Test message 2"""

        results1 = self.parser._process_log_in_chunks(large_log, False, chunk_size=2)
        results2 = self.parser._process_log_in_chunks(large_log, False, chunk_size=10)
        results3 = self.parser._process_log_in_chunks(large_log, True, chunk_size=5)

        assert isinstance(results1, dict)
        assert isinstance(results2, dict)
        assert isinstance(results3, dict)

        log_stream = StringIO(large_log)
        results4 = self.parser._process_log_in_chunks(log_stream, False, chunk_size=3)
        assert isinstance(results4, dict)

    def test_edge_cases_for_coverage(self):
        """Test various edge cases to improve coverage."""
        empty_result = self.parser.parse_log("", unique=False)
        assert isinstance(empty_result, dict)

        whitespace_result = self.parser.parse_log("   \n\n   ", unique=False)
        assert isinstance(whitespace_result, dict)

        login_only = self.parser.parse_log("login:", unique=False)
        assert isinstance(login_only, dict)

        login_at_end = self.parser.parse_log(
            """[0.000] Boot message
[1.000] More messages
login:""",
            unique=False,
        )
        assert isinstance(login_at_end, dict)

    def test_kernel_msgs_only_edge_cases(self):
        """Test __kernel_msgs_only method edge cases."""
        mixed_log = """Regular line without timestamp
[0.000] Kernel message with timestamp
<4>Syslog priority message
Another regular line
[1.000] Another kernel message
<6>Another syslog message"""

        kernel_only = self.parser._BootTestParser__kernel_msgs_only(mixed_log)
        lines = [line.strip() for line in kernel_only.split("\n") if line.strip()]

        assert len(lines) == 4
        assert "Regular line without timestamp" not in kernel_only
        assert "Another regular line" not in kernel_only
        assert "Kernel message with timestamp" in kernel_only
        assert "Syslog priority message" in kernel_only

    def test_detects_rcu_stall(self):
        """Test detection of RCU stall issues"""
        log = """[  344.856743] rcu: INFO: rcu_preempt detected stalls on CPUs/tasks:
[  344.863123] rcu: \\t0-...!: (2 GPs behind) idle=9810/0/0x0 softirq=1405/1405 fqs=1
[  344.867117] rcu: \\tUnless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
[  344.876265] rcu: RCU grace-period kthread stack dump:
[  344.881323] task:rcu_preempt     state:I stack:0     pid:16    ppid:2      flags:0x00000008
[  344.889698] Call trace:
[  344.892145]  __switch_to+0x154/0x1f8
[  344.895733]  __schedule+0x494/0x8a0
[  344.899234]  schedule+0x84/0xe8
[  344.902386]  schedule_timeout+0xac/0x19c
[  344.906320]  rcu_gp_fqs_loop+0x1f4/0x808
[  344.910257]  rcu_gp_kthread+0x70/0x238
[  344.914017]  kthread+0xe8/0x1cc
[  344.917167]  ret_from_fork+0x10/0x20
[  344.920755] rcu: Stack dump where RCU GP kthread last ran:
[  344.926247] Task dump for CPU 0:
[  344.929477] task:swapper/0       state:R  running task     stack:0     pid:0     ppid:0      flags:0x00000008
[  344.939421] Call trace:
[  344.941868]  __switch_to+0x154/0x1f8
[  344.945457]  ct_idle_enter+0x10/0x1c
[  344.949043]  0xffff00097ed15640"""

        data = self.parser.parse_log(log, unique=True)

        assert data, "Should detect RCU stall in log"
        boot_tests = get_parser_results(data, "boot")

        # Verify RCU stall-related tests were created
        assert_tests_created(
            boot_tests, "rcu-stall", "Should detect RCU stall patterns"
        )
        assert_content_found(
            boot_tests,
            "rcu-stall",
            ["detected stalls on CPUs/tasks:", "rcu_preempt kthread"],
            "Should capture RCU stall messages",
        )
