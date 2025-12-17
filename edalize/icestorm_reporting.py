import logging
import regex as re

from edalize.reporting import Reporting

logger = logging.getLogger(__name__)

# Reporting is an optional Edalize feature and its required packages may not
# be installed unless Edalize was installed as edalize[reporting]. There is
# currently reduced-functionality feedback, so if the module is used without
# being properly installed log a hopefully helpful error before throwing the
# exception.
import_msg = "Missing package %s. Was edalize installed with the reporting option? (pip install 'edalize[reporting]')"


class IcestormReporting(Reporting):
    """
    Icestorm-specific reporting routines.
    """

    # Override class variables
    _resource_rpt_pattern = "yosys.log"
    _timing_rpt_pattern = "next.log"

    @classmethod
    def report_resources(cls, report_file: str) -> dict[str, int]:
        with open(report_file, "r") as rfile:
            report = rfile.read()

        i = report.find("Printing statistics.")
        report = report[i:]

        i = report.find("=== design hierarchy ===")
        if i != -1:
            report = report[i:]
            # patterns for newer yosys version (>=v0.58)
            patterns = {
                "wires"           : r"(\d+)\s+wires",
                "wire_bits"       : r"(\d+)\s+wire bits",
                "public_wires"    : r"(\d+)\s+public wires",
                "public_wire_bits": r"(\d+)\s+public wire bits",
                "memories"        : r"(\d+)\s+memories",
                "memory_bits"     : r"(\d+)\s+memory bits",
                "processes"       : r"(\d+)\s+processes",
                "cells"           : r"(\d+)\s+cells",
                "SB_CARRY"        : r"(\d+)\s+SB_CARRY",
                "SB_DFF"          : r"(\d+)\s+SB_DFF",
                "SB_DFFE"         : r"(\d+)\s+SB_DFFE",
                "SB_DFFESR"       : r"(\d+)\s+SB_DFFESR",
                "SB_DFFSR"        : r"(\d+)\s+SB_DFFSR",
                "SB_LUT4"         : r"(\d+)\s+SB_LUT4",
                "SB_RAM40_4K"     : r"(\d+)\s+SB_RAM40_4K",
            }
        else:
            # patterns for old yosys version
            patterns = {
                "wires": r"^\s+Number of wires:\s+(\d+)",
                "wire_bits": r"^\s+Number of wire bits:\s+(\d+)",
                "public_wires": r"^\s+Number of public wires:\s+(\d+)",
                "public_wire_bits": r"^\s+Number of public wire bits:\s+(\d+)",
                "memories": r"^\s+Number of memories:\s+(\d+)",
                "memory_bits": r"^\s+Number of memory bits:\s+(\d+)",
                "processes": r"^\s+Number of processes:\s+(\d+)",
                "cells": r"^\s+Number of cells:\s+(\d+)",
                "SB_CARRY": r"^\s+SB_CARRY\s+(\d+)",
                "SB_DFF": r"^\s+SB_DFF\s+(\d+)",
                "SB_DFFE": r"^\s+SB_DFFE\s+(\d+)",
                "SB_DFFESR": r"^\s+SB_DFFESR\s+(\d+)",
                "SB_DFFSR": r"^\s+SB_DFFSR\s+(\d+)",
                "SB_LUT4": r"^\s+SB_LUT4\s+(\d+)",
                "SB_RAM40_4K": r"^\s+SB_RAM40_4K\s+(\d+)",
            }        

        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, report, re.MULTILINE)
            data[key] = int(match.group(1)) if match else 0

        return data


    @classmethod
    def report_timing(cls, report_file: str) -> dict[str, str]:
        with open(report_file, "r") as rfile:
            report = rfile.read()
        rpt_lines = report.splitlines()
        rpt_lines.reverse()

        data = {}

        # Get fmax
        for line in rpt_lines:
            if line.startswith("Info: Max frequency"):
                data["fmax"] = re.search(r"\d+\.\d+", line).group(0)
                break

        # Get post packing resources
        patterns = {
            "ICESTORM_LC" :  r"ICESTORM_LC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ICESTORM_RAM": r"ICESTORM_RAM:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SB_IO"       :        r"SB_IO:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SB_GB"       :        r"SB_GB:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ICESTORM_PLL": r"ICESTORM_PLL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SB_WARMBOOT" :  r"SB_WARMBOOT:\s+(\d+)/\s+(\d+)\s+(\d+)%"
        }
        data["post_packing"] = {}

        for key, pattern in patterns.items():
            match = re.search(pattern, report, re.MULTILINE)
            if not match:
                data["post_packing"][key] = None
                continue
            data["post_packing"][key] = {
                "count": int(match.group(1)),
                "total": int(match.group(2)),
                "utilization": int(match.group(3))
            }

        return data


    @staticmethod
    def report_summary(resources: dict[str, int], timing: dict[str, str]):
        # move post packing elements to resources dict
        resources["post_packing"] = timing.pop("post_packing", None)

        nr_regs = resources["SB_DFF"] + resources["SB_DFFE"] + \
                    resources["SB_DFFESR"] + resources["SB_DFFSR"]

        data = {
            "constraint": None,
            "fmax": timing["fmax"],
            "lut": resources["SB_LUT4"],
            "reg": nr_regs,
            "blkmem": resources["SB_RAM40_4K"],
            "dsp": None
        }
        return data



