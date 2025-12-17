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


class PeppercornReporting(Reporting):
    """
    Peppercorn-specific reporting routines.
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

        i = report.find("Local Count")
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
                "CC_ADDF": r"(\d+)\s+CC_ADDF",    
                "CC_BRAM_20K": r"(\d+)\s+CC_BRAM_20K",
                "CC_BRAM_40K": r"(\d+)\s+CC_BRAM_40K",
                "CC_BUFG": r"(\d+)\s+CC_BUFG",
                "CC_DFF": r"(\d+)\s+CC_DFF",
                "CC_IBUF": r"(\d+)\s+CC_IBUF", 
                "CC_L2T4": r"(\d+)\s+CC_L2T4", 
                "CC_L2T5": r"(\d+)\s+CC_L2T5", 
                "CC_LUT1": r"(\d+)\s+CC_LUT1", 
                "CC_LUT2": r"(\d+)\s+CC_LUT2", 
                "CC_MX2": r"(\d+)\s+CC_MX2", 
                "CC_MX4": r"(\d+)\s+CC_MX4",
                "CC_OBUF": r"(\d+)\s+CC_OBUF",
                "CC_MULT": r"(\d+)\s+CC_MULT"
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
                "CC_ADDF": r"^\s+CC_ADDF\s+(\d+)",    
                "CC_BRAM_20K": r"^\s+CC_BRAM_20K\s+(\d+)",
                "CC_BRAM_40K": r"^\s+CC_BRAM_40K\s+(\d+)",
                "CC_BUFG": r"^\s+CC_BUFG\s+(\d+)",
                "CC_DFF": r"^\s+CC_DFF\s+(\d+)",
                "CC_IBUF": r"^\s+CC_IBUF\s+(\d+)", 
                "CC_L2T4": r"^\s+CC_L2T4\s+(\d+)", 
                "CC_L2T5": r"^\s+CC_L2T5\s+(\d+)", 
                "CC_LUT1": r"^\s+CC_LUT1\s+(\d+)", 
                "CC_LUT2": r"^\s+CC_LUT2\s+(\d+)", 
                "CC_MX2": r"^\s+CC_MX2\s+(\d+)", 
                "CC_MX4": r"^\s+CC_MX4\s+(\d+)",
                "CC_OBUF": r"^\s+CC_OBUF\s+(\d+)",
                "CC_MULT": r"^\s+CC_MULT\s+(\d+)"
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
            "USR_RSTN"    :	            r"USR_RSTN:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CPE_COMP"    :	            r"CPE_COMP:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CPE_CPLINES" :	         r"CPE_CPLINES:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IOSEL"       :	               r"IOSEL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "GPIO"        :	                r"GPIO:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CLKIN"       :	               r"CLKIN:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "GLBOUT"      :	              r"GLBOUT:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "PLL"         :	                 r"PLL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CFG_CTRL"    :	            r"CFG_CTRL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "SERDES"      :	              r"SERDES:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CPE_LT"      :	              r"CPE_LT:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CPE_FF"      :	              r"CPE_FF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CPE_RAMIO"   :	           r"CPE_RAMIO:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "RAM_HALF"    :	            r"RAM_HALF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
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

        nr_luts = resources["CC_LUT2"] + resources["CC_LUT1"] + \
                    resources["CC_L2T5"] + resources["CC_L2T4"]
        
        nr_blkmem = resources["CC_BRAM_20K"] + resources["CC_BRAM_40K"]

        data = {
            "constraint": None,
            "fmax": timing["fmax"],
            "lut": nr_luts,
            "reg": resources["CC_DFF"],
            "blkmem": nr_blkmem,
            "dsp": resources["CC_MULT"]
        }
        return data



