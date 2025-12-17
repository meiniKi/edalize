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


class TrellisReporting(Reporting):
    """
    Trellis-specific reporting routines.
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
                "wires": r"(\d+)\s+wires",
                "wire_bits": r"(\d+)\s+wire bits",
                "public_wires": r"(\d+)\s+public wires",
                "public_wire_bits": r"(\d+)\s+public wire bits",
                "memories": r"(\d+)\s+memories",
                "memory_bits": r"(\d+)\s+memory bits",
                "processes": r"(\d+)\s+processes",
                "cells": r"(\d+)\s+cells",
                "CCU2C": r"(\d+)\s+CCU2C",
                "DP16KD": r"(\d+)\s+DP16KD",
                "L6MUX21": r"(\d+)\s+L6MUX21",
                "LUT4": r"(\d+)\s+LUT4",
                "PFUMX": r"(\d+)\s+PFUMX",
                "TRELLIS_DPR16X4": r"(\d+)\s+TRELLIS_DPR16X4",
                "TRELLIS_FF": r"(\d+)\s+TRELLIS_FF",
                "MULT18X18D": r"(\d+)\s+MULT18X18D",
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
                "CCU2C": r"^\s+CCU2C\s+(\d+)",
                "DP16KD": r"^\s+DP16KD\s+(\d+)",
                "L6MUX21": r"^\s+L6MUX21\s+(\d+)",
                "LUT4": r"^\s+LUT4\s+(\d+)",
                "PFUMX": r"^\s+PFUMX\s+(\d+)",
                "TRELLIS_DPR16X4": r"^\s+TRELLIS_DPR16X4\s+(\d+)",
                "TRELLIS_FF": r"^\s+TRELLIS_FF\s+(\d+)",
                "MULT18X18D": r"^\s+MULT18X18D\s+(\d+)",
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

        # get fmax
        for line in rpt_lines:
            if line.startswith("Info: Max frequency"):
                data["fmax"] = re.search(r"\d+\.\d+", line).group(0)
                break

        # Get post packing resources
        patterns = {
            "TRELLIS_IO"        :       r"TRELLIS_IO:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DCCA"              :             r"DCCA:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DP16KD"            :           r"DP16KD:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULT18X18D"        :       r"MULT18X18D:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ALU54B"            :           r"ALU54B:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "EHXPLLL"           :          r"EHXPLLL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "EXTREFB"           :          r"EXTREFB:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DCUA"              :             r"DCUA:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "PCSCLKDIV"         :        r"PCSCLKDIV:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IOLOGIC"           :          r"IOLOGIC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SIOLOGIC"          :         r"SIOLOGIC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "GSR"               :              r"GSR:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "JTAGG"             :            r"JTAGG:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "OSCG"              :             r"OSCG:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SEDGA"             :            r"SEDGA:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DTR"               :              r"DTR:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "USRMCLK"           :          r"USRMCLK:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CLKDIVF"           :          r"CLKDIVF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ECLKSYNCB"         :        r"ECLKSYNCB:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DLLDELD"           :          r"DLLDELD:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DDRDLL"            :           r"DDRDLL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DQSBUFM"           :          r"DQSBUFM:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "TRELLIS_ECLKBUF"   :  r"TRELLIS_ECLKBUF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ECLKBRIDGECS"      :     r"ECLKBRIDGECS:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DCSC"              :             r"DCSC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "TRELLIS_FF"        :       r"TRELLIS_FF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "TRELLIS_COMB"      :     r"TRELLIS_COMB:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "TRELLIS_RAMW"      :     r"TRELLIS_RAMW:\s+(\d+)/\s+(\d+)\s+(\d+)%",
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

        blkmem = resources["DP16KD"] if resources["DP16KD"] else 0

        data = {
            "constraint": None,
            "fmax": timing["fmax"],
            "lut": resources["LUT4"],
            "reg": resources["TRELLIS_FF"],
            "blkmem": blkmem,
            "dsp": resources["MULT18X18D"]
        }
        return data



