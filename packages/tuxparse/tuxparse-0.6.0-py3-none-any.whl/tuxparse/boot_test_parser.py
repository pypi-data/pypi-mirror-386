#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2025-present Linaro Limited
#
# SPDX-License-Identifier: MIT

import io
import logging
import re
import yaml
from collections import defaultdict
from yaml import SafeLoader

from tuxparse.lib.base_log_parser import (
    BaseLogParser,
    REGEX_NAME,
    REGEX_EXTRACT_NAME,
    tstamp,
    pid,
    not_newline_or_plus,
)

logger = logging.getLogger(__name__)


def build_sanitizer_pattern(sanitizer_name):
    """Build a standardized pattern for kernel sanitizers (KASAN, KCSAN, KFENCE, etc.)

    Matches complete sanitizer reports enclosed by delimiter lines:
    ==================================================================
    BUG: SANITIZER: ...
    [full diagnostic output]
    ==================================================================
    """
    return (
        sanitizer_name.lower(),
        rf"{tstamp}\s+=+\s*\n{tstamp}{pid}?\s+BUG: {sanitizer_name.upper()}:.*?{tstamp}\s+=+",
        rf"BUG: {sanitizer_name.upper()}:{not_newline_or_plus}*",
    )


MULTILINERS = [
    (
        "exception",
        rf"{tstamp}{pid}?[^\n]*?cut here.*?{tstamp}{pid}?\s*-+\[? end trace \w* \]?-+",
        rf"\n{tstamp}{not_newline_or_plus}*",
    ),  # noqa
    (
        "ubsan",
        r"UBSAN:.*?-+\[? end trace.*?\]?-+(?:.*?Kernel panic - not syncing: UBSAN:.*?: Fatal exception)?",
        rf"UBSAN:{not_newline_or_plus}*",
    ),  # noqa
    # Kernel sanitizers - using standardized pattern builder
    *[build_sanitizer_pattern(name) for name in ["KASAN", "KCSAN", "KFENCE"]],
    (
        "rcu-stall",
        rf"{tstamp}{pid}?\s+rcu: INFO: \w+ detected stalls on CPUs/tasks:[^\n]*(?:\n[^\n]*){{0,30}}",
        rf"\w+ detected stalls on CPUs/tasks:{not_newline_or_plus}*",
    ),  # noqa
    (
        "panic-multiline",
        rf"{tstamp}{pid}?\s+Kernel panic - [^\n]+\n.*?-+\[? end Kernel panic - [^\n]+ \]?-*",
        rf"Kernel {not_newline_or_plus}*",
    ),  # noqa
    (
        "oops-multiline",
        rf"{tstamp}{pid}?\s+Oops(?: -|:).*?{tstamp}{pid}?\s+-+\[? end trace \w* \]?-+",
        rf"Oops{not_newline_or_plus}*",
    ),  # noqa
    (
        "internal-error-oops",
        rf"{tstamp}{pid}?\s+Internal error: Oops.*?-+\[? end trace \w+ \]?-+",
        rf"Oops{not_newline_or_plus}*",
    ),  # noqa
    (
        "oom",
        rf"{tstamp}[^\n]*invoked oom-killer:[^\n]*\n(?:[^\n]*\n){{0,8}}{tstamp}.*?Out of memory: Killed process \d+",
        rf"oom-killer:{not_newline_or_plus}*",
    ),  # noqa
]

ONELINERS = [
    ("oops", r"^[^\n]+Oops(?: -|:).*?$", rf"Oops{not_newline_or_plus}*"),  # noqa
    (
        "fault",
        r"^[^\n]+Unhandled fault.*?$",
        rf"Unhandled {not_newline_or_plus}*",
    ),  # noqa
    ("warning", r"^[^\n]+WARNING:.*?$", rf"WARNING:{not_newline_or_plus}*"),  # noqa
    (
        "bug",
        r"^[^\n]+(?: kernel BUG at| BUG:).*?$",
        rf"BUG{not_newline_or_plus}*",
    ),  # noqa
    (
        "invalid-opcode",
        r"^[^\n]+invalid opcode:.*?$",
        rf"invalid opcode:{not_newline_or_plus}*",
    ),  # noqa
    (
        "panic",
        r"Kernel panic - not syncing.*?$",
        rf"Kernel {not_newline_or_plus}*",
    ),  # noqa
]

# LAVA-specific infrastructure issue patterns
LAVA_ISSUES = [
    ("lava-timeout", r"^[^\n]*\[LAVA-INFRA\] LAVA Timeout:.*?$", r"LAVA Timeout.*"),
    ("lava-error", r"^[^\n]*\[LAVA-INFRA\] LAVA Error:.*?$", r"LAVA Error.*"),
    (
        "lava-connection",
        r"^[^\n]*\[LAVA-INFRA\] LAVA Connection Lost:.*?$",
        r"LAVA Connection.*",
    ),
    (
        "lava-validation",
        r"^[^\n]*\[LAVA-INFRA\] LAVA Validation Failed:.*?$",
        r"LAVA Validation.*",
    ),
    (
        "lava-command",
        r"^[^\n]*\[LAVA-INFRA\] LAVA Command Failed:.*?$",
        r"LAVA Command.*",
    ),
]

# Tip: broader regexes should come first
REGEXES = LAVA_ISSUES + MULTILINERS + ONELINERS


class BootTestParser(BaseLogParser):
    split_patterns = [r" login:", r"console:/", r"root@(.*):[/~]#"]

    def __cutoff_boot_log(self, log):
        split_index = None

        for pattern in self.split_patterns:
            match = re.search(pattern, log)
            if match:
                # Find the earliest split point
                if split_index is None or match.start() < split_index:
                    split_index = match.start()

        if split_index is not None:
            boot_log = log[:split_index]
            test_log = log[split_index:]
            return boot_log, test_log

        # No match found; return whole log as boot log
        return log, ""

    def __kernel_msgs_only(self, log):
        # Support both timestamp formats: [timestamp] and <syslog_priority>
        # Pattern matches:
        # - [    0.000000] message (traditional kernel timestamp with space)
        # - <4>message (syslog priority format without space)
        kernel_msgs = re.findall(f"({tstamp}{pid}? ?.*?)$", log, re.S | re.M)  # noqa
        return "\n".join(kernel_msgs)

    def _parse_lava_log_entry(self, line):
        """Parse a single LAVA log entry from YAML format"""
        try:
            data = yaml.load(line, Loader=SafeLoader)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            elif not isinstance(data, dict):
                return None

            if not data:
                return None
            if not isinstance(data, dict) or not set(["dt", "lvl", "msg"]).issubset(
                data.keys()
            ):
                return None
            return data
        except (TypeError, yaml.YAMLError, AttributeError):
            return None

    def _extract_lava_phases(self, log_entries):
        """Extract and categorize LAVA test phases"""
        phases = {
            "infrastructure": [],  # LAVA setup, validation, downloads
            "boot": [],  # Boot process and kernel messages
            "test": [],  # Test execution phase
            "errors": [],  # LAVA-detected errors and timeouts
        }

        current_phase = "infrastructure"

        for entry in log_entries:
            msg = entry.get("msg", "")
            lvl = entry.get("lvl", "")

            # Handle msg being a dict (for results entries)
            if isinstance(msg, dict):
                msg_str = str(msg)
            else:
                msg_str = str(msg)

            # Phase detection based on LAVA messages
            if (
                "auto-login-action" in msg_str
                or "Waiting for the login prompt" in msg_str
            ):
                current_phase = "boot"
            elif "login-action" in msg_str and "end:" in msg_str:
                current_phase = "test"
            elif (
                lvl == "error"
                or "timeout" in msg_str.lower()
                or "failed" in msg_str.lower()
            ):
                phases["errors"].append(entry)
                continue

            # Categorize by current phase
            if current_phase == "boot" and lvl == "target":
                # Kernel messages during boot
                phases["boot"].append(entry)
            elif current_phase == "test" and lvl in ["target", "feedback"]:
                # Test execution messages
                phases["test"].append(entry)
            else:
                # Infrastructure/setup messages
                phases["infrastructure"].append(entry)

        return phases

    def _detect_lava_infrastructure_issues(self, entries):
        """Detect LAVA infrastructure problems"""
        issues = []

        for entry in entries:
            msg = entry.get("msg", "")
            lvl = entry.get("lvl", "")

            # Handle msg being a dict (for results entries)
            if isinstance(msg, dict):
                msg_str = str(msg)
            else:
                msg_str = str(msg)

            # LAVA-specific error patterns
            if lvl == "error":
                issues.append(f"LAVA Error: {msg_str}")
            elif "timeout" in msg_str.lower():
                issues.append(f"LAVA Timeout: {msg_str}")
            elif "connection lost" in msg_str.lower():
                issues.append(f"LAVA Connection Lost: {msg_str}")
            elif "validation failed" in msg_str.lower():
                issues.append(f"LAVA Validation Failed: {msg_str}")
            elif "Returned" in msg_str and "in 0 seconds" not in msg_str:
                # Command failures
                if any(
                    code in msg_str
                    for code in ["Returned 1", "Returned 2", "Returned -"]
                ):
                    issues.append(f"LAVA Command Failed: {msg_str}")

        return issues

    def logs_txt(self, f_in):
        """Enhanced LAVA log parsing with structured YAML handling"""
        log_entries = []

        for line in io.StringIO(f_in):
            line = line.rstrip("\n")
            entry = self._parse_lava_log_entry(line)
            if entry:
                log_entries.append(entry)

        if not log_entries:
            return ""

        # Build output using existing simple approach for now
        f_text = io.StringIO()

        for entry in log_entries:
            msg = entry.get("msg", "")
            lvl = entry.get("lvl", "")

            # Handle msg being a dict (for results entries)
            if isinstance(msg, dict):
                msg_str = str(msg)
            else:
                msg_str = str(msg)

            # Filter by level
            if lvl not in ["target", "feedback"]:
                continue

            # Add namespace prefix for feedback
            if lvl == "feedback" and "ns" in entry:
                f_text.write(f"<{entry['ns']}> {msg_str}\n")
            else:
                f_text.write(f"{msg_str}\n")

        return f_text.getvalue()

    def append_function_from_call_trace(self, name, lines):
        function_name = ""
        sha = ""
        snippet = "\n".join(lines)

        # Find SHA at end of name, e.g. -deadbeef... or longer
        sha_match = re.search(r"-(?P<sha>[a-f0-9]{7,64})$", name)
        if sha_match:
            sha = sha_match.group("sha")
            name = name[: -len(sha) - 1]  # remove "-<sha>"

        # Extract function after "Call trace:"
        capture_next = False
        for line in snippet.split("\n"):
            if capture_next:
                match = re.search(r"\b([a-zA-Z0-9_]+)\+0x", line)
                if match:
                    function_name = match.group(1)
                break
            if "Call trace:" in line:
                capture_next = True

        new_name = f"{name}__{function_name}" if function_name else name
        if sha:
            new_name += f"-{sha}"
        return new_name

    def _add_test_to_results(
        self, suite_name, name, lines, results, max_snippets_per_test=30
    ):
        """Helper to add a test to results with proper log_excerpt formatting"""
        extended_name = self.append_function_from_call_trace(name, lines)
        log_excerpt = []
        for line in lines:
            log_excerpt.extend(line.split("\n"))
        if len(log_excerpt) > max_snippets_per_test:
            log_excerpt = log_excerpt[:max_snippets_per_test]
            logger.debug(
                f"Test '{extended_name}' truncated to {max_snippets_per_test} snippets"
            )
        results[suite_name][extended_name]["log_excerpt"] = log_excerpt

    def _merge_results(self, main_results, new_results, max_snippets_per_test=30):
        """Merge new results into main results, avoiding duplicates while preserving order and limiting snippets per test"""
        for suite_name, tests in new_results.items():
            for test_name, test_data in tests.items():
                if test_name not in main_results[suite_name]:
                    # New test - limit snippets if needed
                    log_excerpt = test_data["log_excerpt"]
                    if len(log_excerpt) > max_snippets_per_test:
                        log_excerpt = log_excerpt[:max_snippets_per_test]
                        logger.debug(
                            f"Test '{test_name}' truncated to {max_snippets_per_test} snippets"
                        )
                    main_results[suite_name][test_name] = {
                        "log_excerpt": log_excerpt,
                        "result": test_data["result"],
                    }
                else:
                    # If test already exists, merge log lines avoiding duplicates while preserving order
                    existing_lines = main_results[suite_name][test_name]["log_excerpt"]
                    new_lines = test_data["log_excerpt"]

                    # Maintain order: start with existing lines, then add new unique lines
                    merged_lines = list(existing_lines)
                    for line in new_lines:
                        if line not in merged_lines:
                            merged_lines.append(line)

                    # Limit total snippets per test
                    if len(merged_lines) > max_snippets_per_test:
                        merged_lines = merged_lines[:max_snippets_per_test]
                        logger.debug(
                            f"Test '{test_name}' truncated to {max_snippets_per_test} snippets after merge"
                        )

                    main_results[suite_name][test_name]["log_excerpt"] = merged_lines

    def _process_log_section(
        self, log, log_type, unique, max_snippets_per_test=30, is_boot_issue=False
    ):
        """Process a single log section (boot or test)"""
        results = defaultdict(
            lambda: defaultdict(lambda: {"log_excerpt": "", "result": "fail"})
        )

        log = self.__kernel_msgs_only(log)
        suite_name = f"log-parser-{log_type}"

        regex = self.compile_regexes(REGEXES)
        matches = regex.findall(log)
        snippets = self.join_matches(matches, REGEXES)

        has_matches = any(snippets[regex_id] for regex_id in range(len(REGEXES)))

        for regex_id in range(len(REGEXES)):
            test_name = REGEXES[regex_id][REGEX_NAME]
            regex_pattern = REGEXES[regex_id][REGEX_EXTRACT_NAME]
            test_name_regex = None
            if regex_pattern:
                test_name_regex = re.compile(regex_pattern, re.S | re.M)
            tests_without_shas_to_create, tests_with_shas_to_create = self.create_tests(
                suite_name, test_name, snippets[regex_id], test_name_regex
            )

            if not unique:
                for name, lines in tests_without_shas_to_create.items():
                    self._add_test_to_results(
                        suite_name, name, lines, results, max_snippets_per_test
                    )

            for name, lines in tests_with_shas_to_create.items():
                self._add_test_to_results(
                    suite_name, name, lines, results, max_snippets_per_test
                )

        if not has_matches and log_type == "boot" and is_boot_issue and log.strip():
            log_lines = log.strip().split("\n")
            last_20_lines = log_lines[-20:] if len(log_lines) >= 20 else log_lines

            snippet_text = "\n".join(last_20_lines)
            sha = self.create_shasum(snippet_text)
            test_name = f"unknown-boot-failure-{sha}"
            results[suite_name][test_name]["log_excerpt"] = last_20_lines

        return results

    def _process_logs_and_merge(self, logs, is_boot_issue, unique, results_dict):
        """Process both boot and test logs and merge results into results_dict"""
        for log_type, log in logs.items():
            section_results = self._process_log_section(
                log,
                log_type,
                unique,
                is_boot_issue=(is_boot_issue and log_type == "boot"),
            )
            self._merge_results(results_dict, section_results)

    def _determine_chunk_split(
        self,
        chunk_start_line,
        chunk_end_line,
        chunk_buffer,
        login_split_found,
        login_split_line,
    ):
        """Determine how to split a chunk based on login detection"""
        if not login_split_found:
            return {"boot": "\n".join(chunk_buffer), "test": ""}, True
        elif login_split_line < chunk_start_line:
            return {"boot": "", "test": "\n".join(chunk_buffer)}, False
        elif (
            login_split_line >= chunk_start_line and login_split_line <= chunk_end_line
        ):
            split_index_in_chunk = login_split_line - chunk_start_line
            boot_lines = chunk_buffer[:split_index_in_chunk]
            test_lines = chunk_buffer[split_index_in_chunk:]
            return {"boot": "\n".join(boot_lines), "test": "\n".join(test_lines)}, False
        else:
            return {"boot": "\n".join(chunk_buffer), "test": ""}, True

    def _process_single_chunk(
        self,
        chunk_num,
        chunk_buffer,
        line_count,
        login_split_found,
        login_split_line,
        unique,
        results,
    ):
        """Process a single chunk and merge results"""
        logger.debug(f"Processing chunk {chunk_num} with {len(chunk_buffer)} lines")

        chunk_start_line = line_count - len(chunk_buffer)
        chunk_end_line = line_count - 1
        logs, is_boot_issue = self._determine_chunk_split(
            chunk_start_line,
            chunk_end_line,
            chunk_buffer,
            login_split_found,
            login_split_line,
        )

        chunk_results = defaultdict(
            lambda: defaultdict(lambda: {"log_excerpt": "", "result": "fail"})
        )
        self._process_logs_and_merge(logs, is_boot_issue, unique, chunk_results)
        self._merge_results(results, chunk_results)

    def _detect_login_in_line(self, line, login_split_found, line_count):
        """Detect login pattern in a line and return updated state"""
        if not login_split_found:
            for pattern in self.split_patterns:
                if re.search(pattern, line):
                    login_split_line = line_count - 1
                    logger.debug(f"Login split found at line {login_split_line}")
                    return True, login_split_line
        return login_split_found, None

    def _process_log_in_chunks(self, log_input, unique, chunk_size=5000, overlap=200):
        """Process large logs in chunks to prevent memory exhaustion while preserving data"""

        if hasattr(log_input, "readline"):
            log_file = log_input
        elif isinstance(log_input, str):
            log_file = io.StringIO(log_input)
        else:
            log_file = log_input

        line_count = 0
        chunk_buffer = []
        overlap_buffer = []
        login_split_found = False
        login_split_line = None

        results = defaultdict(
            lambda: defaultdict(lambda: {"log_excerpt": "", "result": "fail"})
        )

        chunk_num = 0

        while line := log_file.readline():
            if not line:
                break

            line = line.rstrip("\n\r")
            chunk_buffer.append(line)
            line_count += 1

            login_split_found, detected_line = self._detect_login_in_line(
                line, login_split_found, line_count
            )
            if detected_line is not None:
                login_split_line = detected_line

            if len(chunk_buffer) >= chunk_size:
                chunk_num += 1
                self._process_single_chunk(
                    chunk_num,
                    chunk_buffer,
                    line_count,
                    login_split_found,
                    login_split_line,
                    unique,
                    results,
                )

                if overlap > 0 and len(chunk_buffer) > overlap:
                    overlap_buffer = chunk_buffer[-overlap:]
                else:
                    overlap_buffer = []
                chunk_buffer = overlap_buffer.copy()

        if chunk_buffer:
            chunk_num += 1
            self._process_single_chunk(
                chunk_num,
                chunk_buffer,
                line_count,
                login_split_found,
                login_split_line,
                unique,
                results,
            )

        logger.debug(
            f"Completed processing {line_count} total lines in {chunk_num} chunks"
        )

        if chunk_num <= 1:
            try:
                log_file.seek(0)
                log_content = log_file.read()
            except (OSError, io.UnsupportedOperation):
                log_content = "\n".join(chunk_buffer) if chunk_buffer else ""

            if log_content:
                boot_log, test_log = self.__cutoff_boot_log(log_content)
                logs = {"boot": boot_log, "test": test_log}
                is_boot_issue = test_log == ""

                simple_results = defaultdict(
                    lambda: defaultdict(lambda: {"log_excerpt": "", "result": "fail"})
                )
                self._process_logs_and_merge(
                    logs, is_boot_issue, unique, simple_results
                )
                return simple_results

        return results

    def parse_log(self, log_input, unique):
        # If running as SQUAD plugin, only run boot/test parser if not build
        if log_input is None:
            return {}

        if hasattr(log_input, "readline") and hasattr(log_input, "read"):
            try:
                current_pos = getattr(log_input, "tell", lambda: None)()
                test_line = log_input.readline()

                if not isinstance(test_line, (str, bytes)):
                    raise TypeError("readline() did not return string or bytes")

                if current_pos is not None:
                    log_input.seek(current_pos)
                elif hasattr(log_input, "seek"):
                    log_input.seek(0)
            except (OSError, io.UnsupportedOperation, AttributeError, TypeError):
                try:
                    log_input = log_input.read()
                except Exception as e:
                    logger.error(f"Failed to read log input: {e}")
                    return {}
            except Exception:
                try:
                    log_input = log_input.read()
                except Exception as e:
                    logger.error(f"Failed to read log input: {e}")
                    return {}
        elif not isinstance(log_input, str):
            try:
                log_input = log_input.read()
            except Exception as e:
                logger.error(f"Failed to read log input: {e}")
                return {}

        if isinstance(log_input, str):
            try:
                if not log_input or not log_input.strip():
                    return {}
            except (AttributeError, TypeError):
                logger.error("Invalid log input format")
                return {}

        results = self._process_log_in_chunks(log_input, unique)

        return results
