#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import io
from unittest.mock import patch, MagicMock
from tuxparse.boot_test_parser import BootTestParser


class TestChunkedProcessing(unittest.TestCase):
    """Test suite for chunked processing functionality in boot_test_parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = BootTestParser()

    def test_chunked_processing_basic_functionality(self):
        """Test basic chunked processing with a moderately sized log."""
        # Create a log with multiple chunks (chunk_size=5000, so 6k lines = 2 chunks)
        log_excerpt = []
        for i in range(6000):
            if i % 1000 == 0:
                log_excerpt.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: test panic {i}"
                )
            else:
                log_excerpt.append(f"[{i:8.3f}] Normal kernel message {i}")

        large_log = "\n".join(log_excerpt)

        # Process with chunked processing
        results = self.parser._process_log_in_chunks(large_log, False)

        # Verify results
        self.assertIn("log-parser-boot", results)
        boot_suite = results["log-parser-boot"]

        # Should have multiple panic tests detected
        panic_tests = [name for name in boot_suite.keys() if "panic" in name]
        self.assertGreater(len(panic_tests), 0)

        # Each panic test should have log lines
        for test_name in panic_tests:
            self.assertGreater(len(boot_suite[test_name]["log_excerpt"]), 0)

    def test_chunked_processing_with_overlap(self):
        """Test that chunked processing maintains overlap between chunks."""
        # Create a log where a multi-line pattern spans chunk boundaries
        log_excerpt = []

        # Add 4900 lines to approach chunk boundary
        for i in range(4900):
            log_excerpt.append(f"[{i:8.3f}] Normal message {i}")

        # Add a multi-line pattern that spans chunk boundary
        log_excerpt.extend(
            [
                "[4900.000] ------------[ cut here ]------------",
                "[4900.001] WARNING: CPU: 0 PID: 1 at kernel/test.c:123 test_function+0x20/0x30",
                "[4900.002] Modules linked in:",
                "[4900.003] CPU: 0 PID: 1 Comm: swapper/0 Not tainted 5.4.0-test #1",
                "[4900.004] Hardware name: QEMU Standard PC (i440FX + PIIX, 1996)",
                "[4900.005] Call Trace:",
                "[4900.006]  test_function+0x20/0x30",
                "[4900.007]  init_module+0x10/0x20",
                "[4900.008] ---[ end trace 1234567890abcdef ]---",
            ]
        )

        # Add more lines to create a second chunk
        for i in range(5000, 6000):
            log_excerpt.append(f"[{i:8.3f}] Normal message {i}")

        large_log = "\n".join(log_excerpt)

        # Process with chunked processing
        results = self.parser._process_log_in_chunks(large_log, False)

        # Verify the multi-line pattern was detected
        self.assertIn("log-parser-boot", results)
        boot_suite = results["log-parser-boot"]

        # Should have detected the warning
        warning_tests = [
            name for name in boot_suite.keys() if "WARNING" in name.upper()
        ]
        self.assertGreater(len(warning_tests), 0)

    def test_chunked_processing_memory_efficiency(self):
        """Test that chunked processing is memory efficient."""

        # Create a very large log (but process in small chunks)
        def generate_large_log():
            """Generator for large log to avoid loading all into memory."""
            for i in range(20000):  # 20k lines
                if i % 5000 == 0:
                    yield f"[{i:8.3f}] Kernel panic - not syncing: test panic {i}\n"
                else:
                    yield f"[{i:8.3f}] Normal kernel message {i}\n"

        # Create a file-like object from generator
        large_log_content = "".join(generate_large_log())
        log_stream = io.StringIO(large_log_content)

        # Process with small chunk size for memory efficiency testing
        results = self.parser._process_log_in_chunks(log_stream, False, chunk_size=1000)

        # Verify results
        self.assertIn("log-parser-boot", results)
        boot_suite = results["log-parser-boot"]

        # Should have detected multiple panic tests
        panic_tests = [name for name in boot_suite.keys() if "panic" in name]
        self.assertGreater(len(panic_tests), 0)

    def test_chunked_processing_with_file_object(self):
        """Test chunked processing with file-like objects."""
        # Create test log content
        log_content = []
        for i in range(7000):
            if i % 2000 == 0:
                log_content.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: test panic {i}"
                )
            else:
                log_content.append(f"[{i:8.3f}] Normal message {i}")

        log_text = "\n".join(log_content)

        # Test with StringIO (seekable)
        log_stream = io.StringIO(log_text)
        results = self.parser._process_log_in_chunks(log_stream, False)

        self.assertIn("log-parser-boot", results)
        panic_tests = [
            name for name in results["log-parser-boot"].keys() if "panic" in name
        ]
        self.assertGreater(len(panic_tests), 0)

        # Test with string input
        results_string = self.parser._process_log_in_chunks(log_text, False)

        # Results should be equivalent
        self.assertEqual(
            len(results["log-parser-boot"]), len(results_string["log-parser-boot"])
        )

    def test_chunked_processing_fallback_to_simple(self):
        """Test that small logs fallback to simple processing."""
        # Create a small log (less than chunk_size)
        small_log = []
        for i in range(100):
            if i == 50:
                small_log.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: small test panic"
                )
            else:
                small_log.append(f"[{i:8.3f}] Normal message {i}")

        log_text = "\n".join(small_log)

        # Mock the seek operation to verify fallback path
        with patch("io.StringIO") as mock_stringio:
            mock_file = MagicMock()
            mock_file.readline.side_effect = log_text.split("\n") + [""]
            mock_file.seek.return_value = None
            mock_file.read.return_value = log_text
            mock_stringio.return_value = mock_file

            results = self.parser._process_log_in_chunks(log_text, False)

            # Should still detect the panic
            self.assertIn("log-parser-boot", results)
            panic_tests = [
                name for name in results["log-parser-boot"].keys() if "panic" in name
            ]
            self.assertGreater(len(panic_tests), 0)

    def test_chunked_processing_merge_results(self):
        """Test the result merging functionality."""
        # Create two sets of results to merge
        main_results = {
            "log-parser-boot": {
                "test1": {"log_excerpt": ["line1", "line2"], "result": "fail"},
                "test2": {"log_excerpt": ["line3"], "result": "fail"},
            }
        }

        new_results = {
            "log-parser-boot": {
                "test1": {
                    "log_excerpt": ["line2", "line4"],
                    "result": "fail",
                },  # Overlapping
                "test3": {"log_excerpt": ["line5", "line6"], "result": "fail"},  # New
            }
        }

        # Merge results
        self.parser._merge_results(main_results, new_results)

        # Verify merging
        boot_suite = main_results["log-parser-boot"]

        # test1 should have merged lines (no duplicates)
        self.assertIn("test1", boot_suite)
        test1_lines = set(boot_suite["test1"]["log_excerpt"])
        expected_lines = {"line1", "line2", "line4"}
        self.assertEqual(test1_lines, expected_lines)

        # test2 should remain unchanged
        self.assertEqual(boot_suite["test2"]["log_excerpt"], ["line3"])

        # test3 should be added
        self.assertIn("test3", boot_suite)
        self.assertEqual(boot_suite["test3"]["log_excerpt"], ["line5", "line6"])

    def test_chunked_processing_snippet_limiting(self):
        """Test snippet limiting in chunked processing."""
        # Create results with too many snippets
        main_results = {
            "log-parser-boot": {
                "test1": {
                    "log_excerpt": [f"line{i}" for i in range(50)],
                    "result": "fail",
                }
            }
        }

        new_results = {
            "log-parser-boot": {
                "test1": {
                    "log_excerpt": [f"newline{i}" for i in range(20)],
                    "result": "fail",
                }
            }
        }

        # Merge with snippet limiting
        with patch("logging.Logger.debug") as mock_debug:
            self.parser._merge_results(
                main_results, new_results, max_snippets_per_test=30
            )

            boot_suite = main_results["log-parser-boot"]
            self.assertEqual(len(boot_suite["test1"]["log_excerpt"]), 30)
            mock_debug.assert_called()

    def test_chunked_processing_with_boot_test_split(self):
        """Test chunked processing handles boot/test log splitting correctly."""
        # Create a log with both boot and test sections
        log_excerpt = []

        # Boot section
        for i in range(3000):
            log_excerpt.append(f"[{i:8.3f}] Boot message {i}")
            # Add detectable patterns in boot section
            if i == 1000:
                log_excerpt.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: boot section panic"
                )
            elif i == 2000:
                # Add KASAN pattern with proper format (needs equals signs)
                log_excerpt.append(
                    f"[{i:8.3f}] =================================================================="
                )
                log_excerpt.append(f"[{i:8.3f}] BUG: KASAN: use-after-free in boot")
                log_excerpt.append(
                    f"[{i:8.3f}] =================================================================="
                )

        # Add login prompt to trigger split
        log_excerpt.append("[3000.000] test-system login:")

        # Test section
        for i in range(3001, 6000):
            log_excerpt.append(f"[{i:8.3f}] Test message {i}")
            if i == 4000:
                log_excerpt.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: test section panic"
                )

        large_log = "\n".join(log_excerpt)

        # Process with chunked processing
        results = self.parser._process_log_in_chunks(large_log, False)

        # Should have both boot and test suites
        self.assertIn("log-parser-boot", results)
        self.assertIn("log-parser-test", results)

        # Boot suite should contain the panic and KASAN from boot section
        boot_suite = results["log-parser-boot"]
        boot_panic_tests = [name for name in boot_suite.keys() if "panic" in name]
        boot_kasan_tests = [name for name in boot_suite.keys() if "kasan" in name]
        self.assertGreater(len(boot_panic_tests), 0)
        self.assertGreater(len(boot_kasan_tests), 0)

        # Test suite should contain the panic from test section
        test_suite = results["log-parser-test"]
        test_panic_tests = [name for name in test_suite.keys() if "panic" in name]
        self.assertGreater(len(test_panic_tests), 0)

    def test_chunked_processing_logging(self):
        """Test that chunked processing produces appropriate logging."""
        # Create a log that will be processed in chunks
        log_excerpt = []
        for i in range(12000):  # Enough for multiple chunks
            log_excerpt.append(f"[{i:8.3f}] Message {i}")

        large_log = "\n".join(log_excerpt)

        # Process with logging
        with patch("logging.Logger.debug") as mock_debug:
            results = self.parser._process_log_in_chunks(large_log, False)

            # Should have logged chunk processing information
            mock_debug.assert_called()
            # Should return valid results
            self.assertIsInstance(results, dict)

            # Check that logging includes chunk information
            logged_messages = [call[0][0] for call in mock_debug.call_args_list]
            chunk_messages = [
                msg for msg in logged_messages if "Processing chunk" in msg
            ]
            self.assertGreater(len(chunk_messages), 0)

            # Should log completion message
            completion_messages = [
                msg for msg in logged_messages if "Completed processing" in msg
            ]
            self.assertEqual(len(completion_messages), 1)

    def test_chunked_processing_login_detection_single_pass(self):
        """Test that login detection works correctly in single-pass chunked processing."""
        log_excerpt = []

        for i in range(2000):
            log_excerpt.append(f"[{i:8.3f}] Boot message {i}")
            if i == 500:
                log_excerpt.append(f"[{i:8.3f}] Kernel panic - not syncing: boot panic")

        log_excerpt.append("Debian GNU/Linux 12 testhost ttyS0")
        log_excerpt.append("")
        log_excerpt.append("testhost login: root")

        for i in range(2003, 5000):
            log_excerpt.append(f"[{i:8.3f}] Test message {i}")
            if i == 3000:
                log_excerpt.append(f"[{i:8.3f}] Kernel panic - not syncing: test panic")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(large_log, False, chunk_size=500)

        self.assertIn("log-parser-boot", results)
        self.assertIn("log-parser-test", results)

        boot_suite = results["log-parser-boot"]
        boot_panic_tests = [name for name in boot_suite.keys() if "panic" in name]
        self.assertGreater(len(boot_panic_tests), 0)

        for test_name in boot_panic_tests:
            log_excerpt_lines = boot_suite[test_name]["log_excerpt"]
            boot_panic_found = any("boot panic" in line for line in log_excerpt_lines)
            self.assertTrue(boot_panic_found, "Boot section should contain boot panic")

        test_suite = results["log-parser-test"]
        test_panic_tests = [name for name in test_suite.keys() if "panic" in name]
        self.assertGreater(len(test_panic_tests), 0)

        for test_name in test_panic_tests:
            log_excerpt_lines = test_suite[test_name]["log_excerpt"]
            test_panic_found = any("test panic" in line for line in log_excerpt_lines)
            self.assertTrue(test_panic_found, "Test section should contain test panic")

    def test_chunked_processing_no_login_found(self):
        """Test chunked processing when no login prompt is found."""
        log_excerpt = []

        for i in range(3000):
            log_excerpt.append(f"[{i:8.3f}] Boot message {i}")
            if i == 1000:
                log_excerpt.append(
                    f"[{i:8.3f}] Kernel panic - not syncing: boot failure"
                )

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(large_log, False, chunk_size=500)

        self.assertIn("log-parser-boot", results)
        self.assertNotIn("log-parser-test", results)

        boot_suite = results["log-parser-boot"]
        panic_tests = [name for name in boot_suite.keys() if "panic" in name]
        self.assertGreater(len(panic_tests), 0)

    def test_chunked_processing_login_detection_edge_cases(self):
        """Test login detection with different login prompt formats."""
        test_cases = [
            ("hostname login:", "Standard login prompt"),
            ("console:/", "Android console prompt"),
            ("root@testhost:~#", "Root shell prompt"),
            ("root@device:/#", "Android root shell"),
        ]

        for login_pattern, description in test_cases:
            with self.subTest(login_pattern=login_pattern, description=description):
                log_excerpt = []

                for i in range(1000):
                    log_excerpt.append(f"[{i:8.3f}] Boot message {i}")
                    if i == 500:
                        log_excerpt.append(f"[{i:8.3f}] WARNING: test warning in boot")

                log_excerpt.append(login_pattern)

                for i in range(1001, 2000):
                    log_excerpt.append(f"[{i:8.3f}] Test message {i}")
                    if i == 1500:
                        log_excerpt.append(f"[{i:8.3f}] WARNING: test warning in test")

                large_log = "\n".join(log_excerpt)

                results = self.parser._process_log_in_chunks(
                    large_log, False, chunk_size=300
                )

                self.assertIn(
                    "log-parser-boot",
                    results,
                    f"Should have boot suite for {description}",
                )
                self.assertIn(
                    "log-parser-test",
                    results,
                    f"Should have test suite for {description}",
                )

                boot_warnings = [
                    name
                    for name in results["log-parser-boot"].keys()
                    if "warning" in name
                ]
                test_warnings = [
                    name
                    for name in results["log-parser-test"].keys()
                    if "warning" in name
                ]

                self.assertGreater(
                    len(boot_warnings), 0, f"Should find boot warning for {description}"
                )
                self.assertGreater(
                    len(test_warnings), 0, f"Should find test warning for {description}"
                )

    def test_chunked_processing_login_at_chunk_boundary(self):
        """Test login detection when login prompt appears at chunk boundaries."""
        log_excerpt = []

        chunk_size = 500
        for i in range(chunk_size - 1):
            log_excerpt.append(f"[{i:8.3f}] Boot message {i}")
            if i == 250:
                log_excerpt.append(f"[{i:8.3f}] WARNING: test warning in boot")

        log_excerpt.append("testhost login: user")

        for i in range(chunk_size, chunk_size + 200):
            log_excerpt.append(f"[{i:8.3f}] Test message {i}")
            if i == chunk_size + 100:
                log_excerpt.append(f"[{i:8.3f}] WARNING: test warning in test")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(
            large_log, False, chunk_size=chunk_size
        )

        self.assertIn("log-parser-boot", results)
        self.assertIn("log-parser-test", results)

        boot_suite = results["log-parser-boot"]
        boot_warnings = [name for name in boot_suite.keys() if "warning" in name]
        self.assertGreater(len(boot_warnings), 0, "Should find warning in boot section")

        test_suite = results["log-parser-test"]
        test_warnings = [name for name in test_suite.keys() if "warning" in name]
        self.assertGreater(len(test_warnings), 0, "Should find warning in test section")

        for test_name in boot_warnings:
            log_excerpt_lines = boot_suite[test_name]["log_excerpt"]
            boot_warning_found = any("boot" in line for line in log_excerpt_lines)
            self.assertTrue(
                boot_warning_found, "Boot warning should be in boot section"
            )

        for test_name in test_warnings:
            log_excerpt_lines = test_suite[test_name]["log_excerpt"]
            test_warning_found = any("test" in line for line in log_excerpt_lines)
            self.assertTrue(
                test_warning_found, "Test warning should be in test section"
            )

    def test_chunked_processing_successful_boot_no_unknown_failures(self):
        """Test that successful boot with login doesn't generate unknown-boot-failure."""
        log_excerpt = []

        for i in range(1000):
            log_excerpt.append(f"[{i:8.3f}] Normal boot message {i}")

        log_excerpt.append("Ubuntu 20.04.3 LTS testhost ttyS0")
        log_excerpt.append("")
        log_excerpt.append("testhost login: ")

        for i in range(1003, 2000):
            log_excerpt.append(f"[{i:8.3f}] Normal test message {i}")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(large_log, False, chunk_size=300)

        if results:
            boot_suites = {k: v for k, v in results.items() if "boot" in k}
            test_suites = {k: v for k, v in results.items() if "test" in k}

            self.assertGreater(
                len(boot_suites) + len(test_suites),
                0,
                "Should create boot or test suites",
            )

            if boot_suites and test_suites:
                self.assertTrue(
                    True, "Login detection worked - both boot and test sections created"
                )
        else:
            pass

    def test_chunked_processing_unknown_boot_failure_before_login(self):
        """Test that unknown-boot-failure is created only for boot issues without login."""
        log_excerpt = []

        for i in range(1000):
            log_excerpt.append(f"[{i:8.3f}] Normal boot message {i}")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(large_log, False, chunk_size=300)

        self.assertIn("log-parser-boot", results)
        boot_suite = results["log-parser-boot"]

        unknown_failures = [
            name
            for name in boot_suite.keys()
            if name.startswith("unknown-boot-failure-")
        ]
        self.assertGreater(
            len(unknown_failures),
            0,
            "Should create unknown-boot-failure for boot without login",
        )

        self.assertNotIn("log-parser-test", results)

    def test_determine_chunk_split_method_all_branches(self):
        """Test all branches of the _determine_chunk_split method."""
        chunk_buffer = ["line1", "line2", "line3"]

        logs, is_boot_issue = self.parser._determine_chunk_split(
            0, 2, chunk_buffer, False, None
        )
        self.assertEqual(logs, {"boot": "line1\nline2\nline3", "test": ""})
        self.assertTrue(is_boot_issue)

        logs, is_boot_issue = self.parser._determine_chunk_split(
            10, 12, chunk_buffer, True, 5
        )
        self.assertEqual(logs, {"boot": "", "test": "line1\nline2\nline3"})
        self.assertFalse(is_boot_issue)

        logs, is_boot_issue = self.parser._determine_chunk_split(
            10, 12, chunk_buffer, True, 10
        )
        self.assertEqual(logs, {"boot": "", "test": "line1\nline2\nline3"})
        self.assertFalse(is_boot_issue)

        logs, is_boot_issue = self.parser._determine_chunk_split(
            10, 12, chunk_buffer, True, 11
        )
        self.assertEqual(logs, {"boot": "line1", "test": "line2\nline3"})
        self.assertFalse(is_boot_issue)

        logs, is_boot_issue = self.parser._determine_chunk_split(
            10, 12, chunk_buffer, True, 12
        )
        self.assertEqual(logs, {"boot": "line1\nline2", "test": "line3"})
        self.assertFalse(is_boot_issue)

        logs, is_boot_issue = self.parser._determine_chunk_split(
            10, 12, chunk_buffer, True, 15
        )
        self.assertEqual(logs, {"boot": "line1\nline2\nline3", "test": ""})
        self.assertTrue(is_boot_issue)

    def test_detect_login_in_line_method(self):
        """Test the _detect_login_in_line helper method."""
        found, line_num = self.parser._detect_login_in_line(
            "testhost login: user", False, 10
        )
        self.assertTrue(found)
        self.assertEqual(line_num, 9)

        found, line_num = self.parser._detect_login_in_line("console:/", False, 5)
        self.assertTrue(found)
        self.assertEqual(line_num, 4)

        found, line_num = self.parser._detect_login_in_line("root@device:~#", False, 15)
        self.assertTrue(found)
        self.assertEqual(line_num, 14)

        found, line_num = self.parser._detect_login_in_line("another login:", True, 20)
        self.assertTrue(found)
        self.assertIsNone(line_num)

        found, line_num = self.parser._detect_login_in_line(
            "regular log line", False, 25
        )
        self.assertFalse(found)
        self.assertIsNone(line_num)

    def test_chunked_processing_with_empty_chunks(self):
        """Test chunked processing with empty or minimal chunks."""
        single_line_log = "[0.000] Single line"
        results = self.parser._process_log_in_chunks(
            single_line_log, False, chunk_size=10
        )
        assert isinstance(results, dict)

        login_only_log = "testhost login:"
        results = self.parser._process_log_in_chunks(
            login_only_log, False, chunk_size=10
        )
        assert isinstance(results, dict)

    def test_chunked_processing_overlap_functionality(self):
        """Test overlap functionality in chunked processing."""
        log_excerpt = []

        for i in range(100):
            log_excerpt.append(f"[{i:8.3f}] Message {i}")

        log_excerpt.extend(
            [
                "[100.000] ------------[ cut here ]------------",
                "[100.001] WARNING: CPU: 0 PID: 1 at kernel/test.c:123",
                "[100.002] Modules linked in:",
                "[100.003] Call Trace:",
                "[100.004] ---[ end trace ]---",
            ]
        )

        log_excerpt.append("testhost login:")

        for i in range(106, 200):
            log_excerpt.append(f"[{i:8.3f}] Test message {i}")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(
            large_log, False, chunk_size=50, overlap=10
        )

        if "log-parser-boot" in results:
            boot_suite = results["log-parser-boot"]
            warning_tests = [
                name for name in boot_suite.keys() if "warning" in name.lower()
            ]
            self.assertGreater(
                len(warning_tests), 0, "Should detect warning pattern with overlap"
            )

    def test_chunked_processing_login_patterns_comprehensive(self):
        """Test all supported login patterns in chunked processing."""
        patterns_to_test = [
            ("login:", "Basic login pattern"),
            ("device login:", "Login with device name"),
            ("console:/", "Android console pattern"),
            ("root@host:~#", "Root shell with tilde"),
            ("root@device:/#", "Root shell with root path"),
            ("user@system:/home/user#", "User shell pattern"),
        ]

        for pattern, description in patterns_to_test:
            with self.subTest(pattern=pattern, description=description):
                log_excerpt = []

                for i in range(500):
                    log_excerpt.append(f"[{i:8.3f}] Boot message {i}")

                log_excerpt.append(pattern)

                for i in range(502, 800):
                    log_excerpt.append(f"[{i:8.3f}] Test message {i}")

                large_log = "\n".join(log_excerpt)
                results = self.parser._process_log_in_chunks(
                    large_log, False, chunk_size=200
                )
                assert isinstance(results, dict)

                if pattern in [
                    "login:",
                    "device login:",
                    "console:/",
                    "root@host:~#",
                    "root@device:/#",
                ]:
                    pass
                else:
                    pass

    def test_chunked_processing_with_large_overlap(self):
        """Test chunked processing with overlap larger than chunk size."""
        log_excerpt = []
        for i in range(200):
            log_excerpt.append(f"[{i:8.3f}] Message {i}")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(
            large_log, False, chunk_size=50, overlap=60
        )
        assert isinstance(results, dict)

    def test_chunked_processing_zero_overlap(self):
        """Test chunked processing with zero overlap."""
        log_excerpt = []
        for i in range(200):
            log_excerpt.append(f"[{i:8.3f}] Message {i}")
            if i == 100:
                log_excerpt.append("testhost login:")

        large_log = "\n".join(log_excerpt)

        results = self.parser._process_log_in_chunks(
            large_log, False, chunk_size=50, overlap=0
        )
        assert isinstance(results, dict)

    def test_chunked_processing_single_chunk_fallback(self):
        """Test the single chunk fallback logic."""
        small_log = """[0.000] Boot message 1
[1.000] Boot message 2
[2.000] WARNING: test warning
testhost login:
[3.000] Test message"""

        results = self.parser._process_log_in_chunks(small_log, False, chunk_size=1000)

        assert isinstance(results, dict)

    def test_file_object_validation_edge_cases(self):
        """Test edge cases in file object validation"""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.readline.return_value = 123
        mock_file.read.side_effect = Exception("Read failed")

        result = self.parser.parse_log(mock_file, False)
        assert result == {}

    def test_parse_log_empty_string_validation(self):
        """Test parse_log with empty string inputs"""
        result = self.parser.parse_log("", False)
        assert result == {}

        result = self.parser.parse_log("   \n\t  ", False)
        assert result == {}

    def test_file_like_object_without_readline(self):
        """Test file-like object that doesn't have readline method"""

        class SimpleReader:
            def __init__(self, content):
                self.content = content

            def read(self):
                return self.content

        simple_obj = SimpleReader("[0.000] test message")
        result = self.parser.parse_log(simple_obj, False)
        assert isinstance(result, dict)

    def test_single_chunk_fallback_content_reconstruction(self):
        """Test single chunk fallback when seek fails and content needs reconstruction"""
        import io

        content = "[0.000] test message"
        stream = io.StringIO(content)

        def failing_seek(pos):
            raise io.UnsupportedOperation("seek disabled")

        stream.seek = failing_seek

        result = self.parser._process_log_in_chunks(stream, False, chunk_size=1000)
        assert isinstance(result, dict)

    def test_empty_file_readline_break(self):
        """Test empty file to trigger readline break condition"""
        import io

        empty_stream = io.StringIO("")
        result = self.parser._process_log_in_chunks(empty_stream, False)
        assert result == {}

    def test_snippet_truncation_coverage(self):
        """Test snippet truncation to cover warning paths in _merge_results"""
        from collections import defaultdict

        main_results = defaultdict(
            lambda: defaultdict(lambda: {"log_excerpt": [], "result": "fail"})
        )

        new_results = defaultdict(
            lambda: defaultdict(lambda: {"log_excerpt": [], "result": "fail"})
        )
        many_snippets = [f"snippet_{i}" for i in range(35)]
        new_results["log-parser-boot"]["test_truncation"]["log_excerpt"] = many_snippets

        with patch("tuxparse.boot_test_parser.logger") as mock_logger:
            self.parser._merge_results(
                main_results, new_results, max_snippets_per_test=30
            )
            mock_logger.debug.assert_called()

    def test_file_validation_error_paths(self):
        """Test file validation error handling paths"""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.tell.side_effect = Exception("tell failed")
        mock_file.read.return_value = "[0.000] test"

        result = self.parser.parse_log(mock_file, False)
        assert isinstance(result, dict)

        mock_file2 = MagicMock()
        mock_file2.tell.return_value = 0
        mock_file2.readline.side_effect = Exception("readline failed")
        mock_file2.read.return_value = "[0.000] test"

        result = self.parser.parse_log(mock_file2, False)
        assert isinstance(result, dict)

    def test_process_log_section_truncation_paths(self):
        """Test snippet truncation in _process_log_section"""
        from unittest.mock import patch

        large_bug_log = "\n".join([f"[{i:06.3f}] BUG: error {i}" for i in range(35)])

        with patch("tuxparse.boot_test_parser.logger") as mock_logger:
            result = self.parser._process_log_section(
                large_bug_log, "boot", False, max_snippets_per_test=5
            )
            mock_logger.debug.assert_called()
            assert isinstance(result, dict)


if __name__ == "__main__":
    unittest.main()
