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


class ApiculaReporting(Reporting):
    """
    Apicula-specific reporting routines.
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
            # patterns for newer yosys version
            patterns = {
                "wires"           : r"(\d+)\s+wires",
                "wire_bits"       : r"(\d+)\s+wire bits",
                "public_wires"    : r"(\d+)\s+public wires",
                "public_wire_bits": r"(\d+)\s+public wire bits",
                "memories"        : r"(\d+)\s+memories",
                "memory_bits"     : r"(\d+)\s+memory bits",
                "processes"       : r"(\d+)\s+processes",
                "cells"           : r"(\d+)\s+cells",
                "ALU"             : r"(\d+)\s+ALU",
                "DFF"             : r"(\d+)\s+DFF",
                "DFFE"            : r"(\d+)\s+DFFE",
                "DFFR"            : r"(\d+)\s+DFFR",
                "DFFRE"           : r"(\d+)\s+DFFRE",
                "GND"             : r"(\d+)\s+GND",
                "IBUF"            : r"(\d+)\s+IBUF",
                "LUT1"            : r"(\d+)\s+LUT1",
                "LUT2"            : r"(\d+)\s+LUT2",
                "LUT3"            : r"(\d+)\s+LUT3",
                "LUT4"            : r"(\d+)\s+LUT4",
                "MUX2_LUT5"       : r"(\d+)\s+MUX2\_LUT5",
                "MUX2_LUT6"       : r"(\d+)\s+MUX2\_LUT6",
                "MUX2_LUT7"       : r"(\d+)\s+MUX2\_LUT7",
                "MUX2_LUT8"       : r"(\d+)\s+MUX2\_LUT8",
                "OBUF"            : r"(\d+)\s+OBUF",
                "RAM16SDP4"       : r"(\d+)\s+RAM16SDP4",
                "VCC"             : r"(\d+)\s+VCC",
            }
        else:
            # patterns for old yosys version
            patterns = {
                "wires"             : r"^\s+Number of wires:\s+(\d+)",
                "wire_bits"         : r"^\s+Number of wire bits:\s+(\d+)",
                "public_wires"      : r"^\s+Number of public wires:\s+(\d+)",
                "public_wire_bits"  : r"^\s+Number of public wire bits:\s+(\d+)",
                "memories"          : r"^\s+Number of memories:\s+(\d+)",
                "memory_bits"       : r"^\s+Number of memory bits:\s+(\d+)",
                "processes"         : r"^\s+Number of processes:\s+(\d+)",
                "cells"             : r"^\s+Number of cells:\s+(\d+)",
                "ALU"               : r"^\s+ALU\s+(\d+)",
                "DFF"               : r"^\s+DFF\s+(\d+)",
                "DFFE"              : r"^\s+DFFE\s+(\d+)",
                "DFFR"              : r"^\s+DFFR\s+(\d+)",
                "DFFRE"             : r"^\s+DFFRE\s+(\d+)",
                "GND"               : r"^\s+GND\s+(\d+)",
                "IBUF"              : r"^\s+IBUF\s+(\d+)",
                "LUT1"              : r"^\s+LUT1\s+(\d+)",
                "LUT2"              : r"^\s+LUT2\s+(\d+)",
                "LUT3"              : r"^\s+LUT3\s+(\d+)",
                "LUT4"              : r"^\s+LUT4\s+(\d+)",
                "MUX2_LUT5"         : r"^\s+MUX2\_LUT5\s+(\d+)",
                "MUX2_LUT6"         : r"^\s+MUX2\_LUT6\s+(\d+)",
                "MUX2_LUT7"         : r"^\s+MUX2\_LUT7\s+(\d+)",
                "MUX2_LUT8"         : r"^\s+MUX2\_LUT8\s+(\d+)",
                "OBUF"              : r"^\s+OBUF\s+(\d+)",
                "RAM16SDP4"         : r"^\s+RAM16SDP4\s+(\d+)",
                "VCC"               : r"^\s+VCC\s+(\d+)",
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
            "VCC"               : r"VCC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IOB"               : r"IOB:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "LUT4"              : r"LUT4:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "OSER16"            : r"OSER16:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IDES16"            : r"IDES16:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IOLOGICI"          : r"IOLOGICI:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "IOLOGICO"          : r"IOLOGICO:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MUX2_LUT5"         : r"MUX2\_LUT5:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MUX2_LUT6"         : r"MUX2\_LUT6:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MUX2_LUT7"         : r"MUX2\_LUT7:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MUX2_LUT8"         : r"MUX2\_LUT8:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ALU"               : r"ALU:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "GND"               : r"GND:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DFF"               : r"DFF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "RAM16SDP4"         : r"RAM16SDP4:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "BSRAM"             : r"BSRAM:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "ALU54D"            : r"ALU54D:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULTADDALU18X18"   : r"MULTADDALU18X18:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULTALU18X18"      : r"MULTALU18X18:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULTALU36X18"      : r"MULTALU36X18:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULT36X36"         : r"MULT36X36:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULT18X18"         : r"MULT18X18:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MULT9X9"           : r"MULT9X9:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "PADD18"            : r"PADD18:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "PADD9"             : r"PADD9:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "GSR"               : r"GSR:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "OSC"               : r"OSC:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "rPLL"              : r"rPLL:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "FLASH608K"         : r"FLASH608K:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "BUFG"              : r"BUFG:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DQCE"              : r"DQCE:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DCS"               : r"DCS:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "DHCEN"             : r"DHCEN:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CLKDIV"            : r"CLKDIV:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "CLKDIV2"           : r"CLKDIV2:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MIPI_IBUF"         : r"MIPI\_IBUF:\s+(\d+)/\s+(\d+)\s+(\d+)%",
            "MIPI_OBUF"         : r"MIPI\_OBUF:\s+(\d+)/\s+(\d+)\s+(\d+)%"
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
        n_regs = resources["DFF"] + resources["DFFE"] + resources["DFFR"] + resources["DFFRE"]
        n_luts = resources["LUT1"] + resources["LUT2"] + resources["LUT3"] + resources["LUT4"]
        
        data = {
            "constraint": None,
            "fmax": timing["fmax"],
            "lut": n_luts,
            "reg": n_regs,
            "blkmem": resources["RAM16SDP4"],
            "dsp": None
        }
        return data



