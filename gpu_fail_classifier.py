#!/usr/bin/env python3
"""
gpu_fail_classifier.py - GPU failure log triage filter for 2am pages.

Usage:
    dmesg | python3 gpu_fail_classifier.py
    cat /var/log/syslog | python3 gpu_fail_classifier.py
    journalctl -u slurmd -n 500 | python3 gpu_fail_classifier.py

Triage buckets:
  - XID_FATAL: Xid 31, 43, 45, 48, 64, 74, 79. Unrecoverable MMU/CUDA fault. Action: GPU reset or drain node.
  - XID_WARN: Xid 13, 32, 61, 63, 68, 94. Driver/context error, may self-clear. Action: watch for repeats.
  - ECC_CORRECTABLE: Single-bit ECC corrections. Track rate per GPU/hr; >50/hr signals failing HBM/DIMM.
  - ECC_UNCORRECTABLE: Double-bit ECC or exhausted remap table. Action: pull node immediately.
  - ROW_REMAP: Pending or failed row remaps; remaps_available==0 means GPU is EOL. Action: RMA.
  - NVLINK_DEGRADED: NVLink CRC errors, high replay counts, link-down events. Action: reseat/check cables.
  - FABRIC_ERROR: NVSwitch and GPU-fabric faults. If multiple nodes fault together, suspect spine/switch.
  - THERMAL_THROTTLE: HW slowdown from thermal cap or power limit violation. Action: check fans/cooling.
  - NODE_DROP: NCCL watchdog timeout, heartbeat lost, rank failure. Action: check network & node health.
  - UNKNOWN: Unmatched log lines during triage.
"""

import sys
import re
from collections import defaultdict

BUCKET_COLORS = {
    "XID_FATAL": "\033[91m",
    "XID_WARN": "\033[93m",
    "ECC_CORRECTABLE": "\033[36m",
    "ECC_UNCORRECTABLE": "\033[95m",
    "ROW_REMAP": "\033[35m",
    "NVLINK_DEGRADED": "\033[33m",
    "FABRIC_ERROR": "\033[91m",
    "THERMAL_THROTTLE": "\033[31m",
    "NODE_DROP": "\033[94m",
    "UNKNOWN": "\033[90m",
}
RESET_COLOR = "\033[0m"

PATTERNS = [
    ("XID_FATAL", re.compile(r"\bXid\s*(?:\(PCI:[^)]+\):\s*)?(?:31|43|45|48|64|74|79)\b", re.IGNORECASE)),
    ("XID_WARN", re.compile(r"\bXid\s*(?:\(PCI:[^)]+\):\s*)?(?:13|32|61|63|68|94)\b", re.IGNORECASE)),
    ("ECC_UNCORRECTABLE", re.compile(r"(uncorrectable\s*(?:ecc|error)|double-bit|dbe\b)", re.IGNORECASE)),
    ("ECC_CORRECTABLE", re.compile(r"(correctable\s*(?:ecc|error)|single-bit|sbe\b)", re.IGNORECASE)),
    ("ROW_REMAP", re.compile(r"(row\s*remap(?:ping)?|remaps_available\s*[:=]\s*0|pending\s*remap)", re.IGNORECASE)),
    ("NVLINK_DEGRADED", re.compile(r"(nvlink.*(?:crc|replay|link\s*down|recovery|error|degraded))", re.IGNORECASE)),
    ("FABRIC_ERROR", re.compile(r"(nvswitch|gpu-fabric|fabric\s*(?:error|fault|degraded|link|manager))", re.IGNORECASE)),
    ("THERMAL_THROTTLE", re.compile(r"(thermal\s*(?:slowdown|throttle)|hw\s*slowdown|temp.*limit)", re.IGNORECASE)),
    ("NODE_DROP", re.compile(r"(nccl.*(?:timeout|watchdog|comm failure)|heartbeat\s*lost|rank\s*\d+\s*(?:failed|died))", re.IGNORECASE)),
]

def classify_line(line: str) -> str:
    for bucket, pattern in PATTERNS:
        if pattern.search(line):
            return bucket
    return "UNKNOWN"

def format_line(bucket: str, line: str, is_tty: bool) -> str:
    clean_line = line.rstrip("
")
    if is_tty and bucket in BUCKET_COLORS:
        return f"{BUCKET_COLORS[bucket]}[{bucket:<17}]{RESET_COLOR} {clean_line}"
    return f"[{bucket:<17}] {clean_line}"

def main():
    is_tty = sys.stdout.isatty()
    counts = defaultdict(int)
    total = 0

    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        total += 1
        bucket = classify_line(line_str)
        counts[bucket] += 1
        print(format_line(bucket, line_str, is_tty))

    print("
" + "=" * 40)
    print("GPU FAILURE CLASSIFICATION SUMMARY")
    print("=" * 40)
    print(f"Total lines analyzed: {total}")
    for bucket in sorted(counts.keys()):
        print(f"  {bucket:<20}: {counts[bucket]}")

if __name__ == "__main__":
    main()
