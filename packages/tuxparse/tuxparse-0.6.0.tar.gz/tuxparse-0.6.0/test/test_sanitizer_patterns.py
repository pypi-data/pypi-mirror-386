#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import time
import unittest

from tuxparse.boot_test_parser import BootTestParser, build_sanitizer_pattern


class TestSanitizerPatterns(unittest.TestCase):
    """Test the sanitizer pattern builder and multiline detection"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = BootTestParser()
        # Disable warnings for cleaner test output
        logging.getLogger().setLevel(logging.ERROR)

    def test_build_sanitizer_pattern_structure(self):
        """Test that build_sanitizer_pattern returns correct tuple structure"""
        pattern_tuple = build_sanitizer_pattern("KASAN")

        # Should return tuple with 3 elements
        self.assertEqual(len(pattern_tuple), 3)

        # First element should be lowercase sanitizer name
        self.assertEqual(pattern_tuple[0], "kasan")

        # Second element should be multiline pattern containing sanitizer name
        self.assertIn("KASAN", pattern_tuple[1])

        # Third element should be single line pattern for name extraction
        self.assertIn("KASAN", pattern_tuple[2])

    def test_sanitizer_pattern_consistency(self):
        """Test that all sanitizers get consistent pattern structure"""
        sanitizers = ["KASAN", "KCSAN", "KFENCE"]

        for sanitizer in sanitizers:
            with self.subTest(sanitizer=sanitizer):
                pattern_tuple = build_sanitizer_pattern(sanitizer)

                # Check structure consistency
                self.assertEqual(pattern_tuple[0], sanitizer.lower())
                self.assertIn(sanitizer.upper(), pattern_tuple[1])
                self.assertIn(sanitizer.upper(), pattern_tuple[2])

                # Both patterns should start with BUG: SANITIZER:
                self.assertIn(f"BUG: {sanitizer.upper()}:", pattern_tuple[1])
                self.assertIn(f"BUG: {sanitizer.upper()}:", pattern_tuple[2])

    def test_kasan_multiline_detection(self):
        """Test KASAN multiline report detection"""
        kasan_log = """
[   18.621478] ==================================================================
[   18.621479] BUG: KASAN: slab-out-of-bounds in kmalloc_test+0x5a4/0x660
[   18.621480] Write of size 1 at addr ffff000082192373 by task test/240
[   18.621481] CPU: 0 PID: 240 Comm: test Tainted: G N 6.9.9-rc1 #1
[   18.621482] Call trace:
[   18.621483]  dump_backtrace+0x9c/0x128
[   18.621484]  show_stack+0x20/0x38
[   18.621485] Memory state around the buggy address:
[   18.621486]  ffff000082192300: 00 00 00 00 fc fc fc fc
[   18.621487] ==================================================================
[   19.000000] Some other log message
"""

        data = self.parser.parse_log(kasan_log, unique=False)

        # Test data structure directly instead of JSON dumps
        self.assertTrue(data, "Should detect KASAN issues")

        # Get boot parser results
        suite = data.get("log-parser-boot", {})
        self.assertTrue(suite, "Should have boot parser results")

        # Verify KASAN tests were created
        kasan_tests = {k: v for k, v in suite.items() if "kasan-" in k}
        self.assertGreater(len(kasan_tests), 0, "Should detect KASAN patterns")

        # Verify log excerpts contain expected KASAN content
        found_kasan_content = False
        for test_name, test_data in kasan_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])
            excerpt_text = " ".join(log_excerpt)
            if "BUG: KASAN:" in excerpt_text and "slab-out-of-bounds" in excerpt_text:
                found_kasan_content = True
                break

        self.assertTrue(
            found_kasan_content, "Should capture KASAN slab-out-of-bounds content"
        )

        # Check multiline content is captured
        for test_name, test_data in kasan_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])

            self.assertGreater(len(log_excerpt), 3, "Should capture multiline content")

            # Should contain key KASAN information
            excerpt_text = " ".join(log_excerpt)
            self.assertIn("BUG: KASAN:", excerpt_text)
            self.assertIn("slab-out-of-bounds", excerpt_text)
            self.assertIn("Call trace:", excerpt_text)

    def test_kcsan_multiline_detection(self):
        """Test KCSAN multiline report detection"""
        kcsan_log = """
[   19.621478] ==================================================================
[   19.621479] BUG: KCSAN: data-race in test_function+0x20/0x40
[   19.621480] race on test_var, by task 123:
[   19.621481] test_function+0x20/0x40
[   19.621482] kthread+0x180/0x1a0
[   19.621483] ret_from_fork+0x10/0x20
[   19.621484] ==================================================================
[   20.000000] Next log entry
"""

        data = self.parser.parse_log(kcsan_log, unique=False)

        # Test data structure directly instead of JSON dumps
        self.assertTrue(data, "Should detect KCSAN issues")

        # Get boot parser results
        suite = data.get("log-parser-boot", {})
        self.assertTrue(suite, "Should have boot parser results")

        # Verify KCSAN tests were created
        kcsan_tests = {k: v for k, v in suite.items() if "kcsan-" in k}
        self.assertGreater(len(kcsan_tests), 0, "Should detect KCSAN patterns")

        # Check multiline content
        # data already available as return value
        suite = data.get("log-parser-boot", {})
        kcsan_tests = {k: v for k, v in suite.items() if "kcsan-" in k}

        self.assertGreater(len(kcsan_tests), 0)

        for test_name, test_data in kcsan_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])
            excerpt_text = " ".join(log_excerpt)

            self.assertIn("BUG: KCSAN:", excerpt_text)
            self.assertIn("data-race", excerpt_text)
            self.assertIn("race on test_var", excerpt_text)

    def test_kfence_multiline_detection(self):
        """Test KFENCE multiline report detection"""
        kfence_log = """
[   20.621478] ==================================================================
[   20.621479] BUG: KFENCE: use-after-free in kfence_test+0x123/0x456
[   20.621480] Invalid read at 0xffff000081234567 (in kfence pool):
[   20.621481] kfence_test+0x123/0x456
[   20.621482] allocated by task 456:
[   20.621483] kfence_test+0x100/0x456
[   20.621484] ==================================================================
[   21.000000] Another message
"""

        data = self.parser.parse_log(kfence_log, unique=False)

        # Test data structure directly instead of JSON dumps
        self.assertTrue(data, "Should detect KFENCE issues")

        # Handle KFENCE potentially being under different parser types
        if "log-parser-boot" in data:
            suite = data["log-parser-boot"]
        elif "log-parser-test" in data:
            suite = data["log-parser-test"]
        else:
            self.fail(f"Should have parser results, got keys: {list(data.keys())}")

        # Verify KFENCE tests were created
        kfence_tests = {k: v for k, v in suite.items() if "kfence-" in k}
        self.assertGreater(len(kfence_tests), 0, "Should detect KFENCE patterns")

        # Check multiline content
        # data already available as return value
        suite = data.get("log-parser-boot", {})
        kfence_tests = {k: v for k, v in suite.items() if "kfence-" in k}

        self.assertGreater(len(kfence_tests), 0)

        for test_name, test_data in kfence_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])
            excerpt_text = " ".join(log_excerpt)

            self.assertIn("BUG: KFENCE:", excerpt_text)
            self.assertIn("use-after-free", excerpt_text)
            self.assertIn("Invalid read", excerpt_text)

    def test_oops_multiline_detection(self):
        """Test standard Oops multiline report detection"""
        oops_log = """
[  123.330937] Oops: 0000 [#1] PREEMPT SMP
[  123.331260] CPU: 0 UID: 0 PID: 2415 Comm: test Tainted: G W 6.12.51-rc1 #1
[  123.332328] Hardware name: QEMU Standard PC (Q35 + ICH9, 2009)
[  123.333060] EIP: test_function+0x13a/0x190
[  123.333221] Code: 00 83 c0 04 f7 c7 02 00 00 00 74 08 66 c7 00 00 00 83 c0 02
[  123.333871] EAX: fffffffe EBX: c23b9900 ECX: 00000000 EDX: 00000090
[  123.335284] CR0: 80050033 CR2: 00000016 CR3: 037c0000 CR4: 000006d0
[  123.335645] Call Trace:
[  123.335737]  function_a+0xae/0xf0
[  123.336227]  function_b+0x4f/0x60
[  123.337386]  function_c+0x139/0x420
[  123.348320] ---[ end trace 0000000000000000 ]---
[  124.000000] Normal log message
"""

        data = self.parser.parse_log(oops_log, unique=False)

        self.assertTrue(data, "Should detect Oops issues")

        suite = data.get("log-parser-boot", {})
        self.assertTrue(suite, "Should have boot parser results")

        oops_tests = {k: v for k, v in suite.items() if "oops-multiline-" in k}
        self.assertGreater(len(oops_tests), 0, "Should detect Oops multiline patterns")

        for test_name, test_data in oops_tests.items():
            log_excerpt = test_data.get("log_excerpt", [])
            self.assertGreater(
                len(log_excerpt), 5, "Should capture multiline Oops content"
            )

            excerpt_text = " ".join(log_excerpt)
            self.assertIn("Oops:", excerpt_text)
            self.assertIn("Call Trace:", excerpt_text)
            self.assertIn("end trace", excerpt_text)

    def test_exception_various_cut_here_formats(self):
        """Test exception pattern with various 'cut here' formats"""
        exception_log1 = """
<4>------------[ cut here ]------------
<4>WARNING: CPU: 0 PID: 435 at lib/math/int_log.c:63 intlog2+0x78/0x88
<4>Modules linked in:
<4>CPU: 0 UID: 0 PID: 435 Comm: kunit_try_catch Tainted: G      D          N  6.18.0-rc1 #1 PREEMPT
<4>Call Trace:
<4> show_stack+0x20/0x38
<4> dump_stack+0x30/0x40
<4>---[ end trace 0000000000000000 ]---
<5>Normal message
"""

        exception_log2 = """
<1>8<--- cut here ---
<1>Unable to handle kernel NULL pointer dereference at virtual address 00000000 when write
<1>[00000000] *pgd=00000000
<0>Internal error: Oops: 805 [#1] ARM
<4>Call Trace:
<4> kunit_test_null_dereference+0x30/0x88
<0>---[ end trace 0000000000000001 ]---
<5>Normal message
"""

        exception_log3 = """
[  123.456789] ------------[ cut here ]------------
[  123.456790] WARNING: CPU: 0 PID: 100 at kernel/sched/core.c:1234 test_func+0x20/0x40
[  123.456791] Modules linked in:
[  123.456792] CPU: 0 PID: 100 Comm: test Not tainted 6.16.0 #1
[  123.456793] Call Trace:
[  123.456794]  <TASK>
[  123.456795]  dump_stack+0x5c/0x80
[  123.456796]  test_func+0x20/0x40
[  123.456797]  </TASK>
[  123.456798] ---[ end trace 0000000000000002 ]---
[  124.000000] Normal message
"""

        exception_log4 = """
<4>[  123.456789] ------------[ cut here ]------------
<4>[  123.456790] WARNING: CPU: 1 PID: 200 at drivers/gpu/drm/test.c:567 drm_test+0x30/0x50
<4>[  123.456791] Modules linked in:
<4>[  123.456792] Call Trace:
<4>[  123.456793]  show_stack+0x40/0x60
<4>[  123.456794] ---[ end trace 0000000000000003 ]---
<5>[  124.000000] Normal message
"""

        for log in [exception_log1, exception_log2, exception_log3, exception_log4]:
            data = self.parser.parse_log(log, unique=False)

            self.assertTrue(data, "Should detect exception issues")

            suite = data.get("log-parser-boot", {})
            self.assertTrue(suite, "Should have boot parser results")

            exception_tests = {k: v for k, v in suite.items() if "exception-" in k}
            self.assertGreater(
                len(exception_tests), 0, "Should detect exception patterns"
            )

            for test_name, test_data in exception_tests.items():
                log_excerpt = test_data.get("log_excerpt", [])
                self.assertGreater(
                    len(log_excerpt), 3, "Should capture multiline exception content"
                )

                excerpt_text = " ".join(log_excerpt)
                self.assertIn("cut here", excerpt_text)
                self.assertIn("end trace", excerpt_text)

    def test_multiple_sanitizers_independent_detection(self):
        """Test that multiple sanitizers are detected independently"""
        mixed_log = """
[   17.999999] ==================================================================
[   18.000000] BUG: KASAN: slab-out-of-bounds in kasan_func+0x123/0x456
[   18.000001] Write of size 1 at addr ffff000082192373
[   18.000002] ==================================================================
[   18.999999] ==================================================================
[   19.000000] BUG: KCSAN: data-race in kcsan_func+0x789/0xabc
[   19.000001] race on shared_var, by task 100:
[   19.000002] ==================================================================
[   19.999999] ==================================================================
[   20.000000] BUG: KFENCE: use-after-free in kfence_func+0xdef/0x111
[   20.000001] Invalid read at 0xffff000081234567
[   20.000002] ==================================================================
[   21.000000] Normal log message
"""

        data = self.parser.parse_log(mixed_log, unique=False)

        # Test data structure directly instead of JSON dumps
        self.assertTrue(data, "Should detect mixed sanitizer issues")

        # Get boot parser results
        suite = data.get("log-parser-boot", {})
        self.assertTrue(suite, "Should have boot parser results")

        # Should detect all three sanitizer types
        kasan_tests = {k: v for k, v in suite.items() if "kasan-" in k}
        kcsan_tests = {k: v for k, v in suite.items() if "kcsan-" in k}
        kfence_tests = {k: v for k, v in suite.items() if "kfence-" in k}

        self.assertGreater(len(kasan_tests), 0, "Should detect KASAN patterns")
        self.assertGreater(len(kcsan_tests), 0, "Should detect KCSAN patterns")
        self.assertGreater(len(kfence_tests), 0, "Should detect KFENCE patterns")

        # Parse and verify independent detection
        # data already available as return value
        suite = data.get("log-parser-boot", {})

        kasan_tests = {k: v for k, v in suite.items() if "kasan-" in k}
        kcsan_tests = {k: v for k, v in suite.items() if "kcsan-" in k}
        kfence_tests = {k: v for k, v in suite.items() if "kfence-" in k}

        self.assertGreater(len(kasan_tests), 0, "Should detect KASAN")
        self.assertGreater(len(kcsan_tests), 0, "Should detect KCSAN")
        self.assertGreater(len(kfence_tests), 0, "Should detect KFENCE")

    def test_sanitizer_pattern_performance(self):
        """Test that sanitizer patterns perform well with reasonable input"""
        # Create moderately sized log with mixed sanitizer reports
        log_lines = []

        # Add various sanitizer reports
        for i in range(20):
            log_lines.append(
                f"[  {10 + i}.000000] =================================================================="
            )
            log_lines.append(
                f"[  {10 + i}.000001] BUG: KASAN: slab-out-of-bounds in func_{i}+0x123/0x456"
            )
            log_lines.append(
                f"[  {10 + i}.000002] Write of size 1 at addr ffff{i:012x}"
            )
            log_lines.append(
                f"[  {10 + i}.000003] =================================================================="
            )
            log_lines.append(
                f"[  {30 + i}.000000] =================================================================="
            )
            log_lines.append(
                f"[  {30 + i}.000001] BUG: KCSAN: data-race in func_{i}+0x789/0xabc"
            )
            log_lines.append(f"[  {30 + i}.000002] race on var_{i}, by task {100 + i}:")
            log_lines.append(
                f"[  {30 + i}.000003] =================================================================="
            )
            log_lines.append(
                f"[  {50 + i}.000000] =================================================================="
            )
            log_lines.append(
                f"[  {50 + i}.000001] BUG: KFENCE: use-after-free in func_{i}+0xdef/0x111"
            )
            log_lines.append(f"[  {50 + i}.000002] Invalid read at 0xffff{i:012x}")
            log_lines.append(
                f"[  {50 + i}.000003] =================================================================="
            )

        test_log = "\n".join(log_lines)

        # Should complete parsing in reasonable time without hanging
        start_time = time.time()

        data = self.parser.parse_log(test_log, unique=False)

        end_time = time.time()
        parse_time = end_time - start_time

        # Test data structure directly instead of JSON dumps
        self.assertTrue(data, "Should detect issues in performance test")

        # Get boot parser results
        suite = data.get("log-parser-boot", {})
        self.assertTrue(suite, "Should have boot parser results for performance test")

        # Should complete in under 5 seconds for this moderate input
        self.assertLess(parse_time, 5.0, "Pattern should not cause performance issues")

        # Should produce substantial test results
        total_tests = len(suite)
        self.assertGreater(
            total_tests,
            10,
            "Should produce substantial number of tests for large input",
        )

    def test_pattern_builder_extensibility(self):
        """Test that pattern builder makes it easy to add new sanitizers"""
        # Test adding a hypothetical new sanitizer
        test_pattern = build_sanitizer_pattern("UBSAN")

        self.assertEqual(test_pattern[0], "ubsan")
        self.assertIn("BUG: UBSAN:", test_pattern[1])
        self.assertIn("BUG: UBSAN:", test_pattern[2])

        # Pattern should be valid regex
        try:
            re.compile(test_pattern[1])
            re.compile(test_pattern[2])
        except re.error:
            self.fail("Generated patterns should be valid regex")


if __name__ == "__main__":
    unittest.main()
