# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

MAKE_HEADER = """#Generated by Edalize
ifndef MODEL_TECH
$(error Environment variable MODEL_TECH was not found. It should be set to <modelsim install path>/bin)
endif

CC ?= gcc
CFLAGS   := -fPIC -fno-stack-protector -g -std=c99
CXXFLAGS := -fPIC -fno-stack-protector -g

LD ?= ld
LDFLAGS := -shared -E

#Try to determine if ModelSim is 32- or 64-bit.
#To manually override, set the environment MTI_VCO_MODE to 32 or 64
ifeq ($(findstring 64, $(shell $(MODEL_TECH)/../vco)),)
CFLAGS   += -m32
CXXFLAGS += -m32
LDFLAGS  += -melf_i386
endif

RM ?= rm
INCS := -I$(MODEL_TECH)/../include

VSIM ?= $(MODEL_TECH)/vsim

TOPLEVEL      := {toplevel}
VPI_MODULES   := {modules}
PARAMETERS    ?= {parameters}
PLUSARGS      ?= {plusargs}
VSIM_OPTIONS  ?= {vsim_options}
EXTRA_OPTIONS ?= $(VSIM_OPTIONS) $(addprefix -g,$(PARAMETERS)) $(addprefix +,$(PLUSARGS))

all: work $(VPI_MODULES)

run: work $(VPI_MODULES)
	$(VSIM) -c $(addprefix -pli ,$(VPI_MODULES)) $(EXTRA_OPTIONS) -do "run -all; quit -code [expr [coverage attribute -name TESTSTATUS -concise] >= 2 ? [coverage attribute -name TESTSTATUS -concise] : 0]; exit" $(TOPLEVEL)

run-gui: work $(VPI_MODULES)
	$(VSIM) -gui $(addprefix -pli ,$(VPI_MODULES)) $(EXTRA_OPTIONS) $(TOPLEVEL)

work:
	$(VSIM) -c -do "do edalize_main.tcl; exit"

clean: {clean_targets}
"""

VPI_MAKE_SECTION = """
{name}_OBJS := {objs}
{name}_LIBS := {libs}
{name}_INCS := $(INCS) {incs}

$({name}_OBJS): CPPFLAGS := $({name}_INCS)

{name}: $({name}_OBJS)
	$(LD) $(LDFLAGS) -o $@ $? $({name}_LIBS)

clean_{name}:
	$(RM) $({name}_OBJS) {name}
"""


class Modelsim(Edatool):
    argtypes = ["plusarg", "vlogdefine", "vlogparam", "generic"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "ModelSim simulator from Mentor Graphics",
                "members": [
                    {
                        "name": "compilation_mode",
                        "type": "String",
                        "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
                    }
                ],
                "lists": [
                    {
                        "name": "vcom_options",
                        "type": "String",
                        "desc": "Additional options for compilation with vcom",
                    },
                    {
                        "name": "vlog_options",
                        "type": "String",
                        "desc": "Additional options for compilation with vlog",
                    },
                    {
                        "name": "vsim_options",
                        "type": "String",
                        "desc": "Additional run options for vsim",
                    },
                ],
            }

    def _write_build_rtl_tcl_file(self, tcl_main):
        tcl_build_rtl = open(os.path.join(self.work_root, "edalize_build_rtl.tcl"), "w")

        (src_files, incdirs) = self._get_fileset_files()
        vlog_include_dirs = ["+incdir+" + d.replace("\\", "/") for d in incdirs]

        libs = []

        vlog_files = []

        common_compilation = self.tool_options.get("compilation_mode") == "common"
        for f in src_files:
            if not f.logical_name:
                f.logical_name = "work"
            if not f.logical_name in libs:
                tcl_build_rtl.write("vlib {}\n".format(f.logical_name))
                libs.append(f.logical_name)
            if f.file_type.startswith("verilogSource") or f.file_type.startswith(
                "systemVerilogSource"
            ):
                vlog_files.append(f)
                cmd = "vlog"
                args = []

                args += self.tool_options.get("vlog_options", [])

                for k, v in self.vlogdefine.items():
                    args += ["+define+{}={}".format(k, self._param_value_str(v))]

                if f.file_type.startswith("systemVerilogSource"):
                    args += ["-sv"]
                args += vlog_include_dirs
            elif f.file_type.startswith("vhdlSource"):
                cmd = "vcom"
                if f.file_type.endswith("-87"):
                    args = ["-87"]
                if f.file_type.endswith("-93"):
                    args = ["-93"]
                if f.file_type.endswith("-2008"):
                    args = ["-2008"]
                else:
                    args = []

                args += self.tool_options.get("vcom_options", [])

            elif f.file_type == "tclSource":
                cmd = None
                tcl_main.write("do {}\n".format(f.name))
            elif f.file_type == "user":
                cmd = None
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(f.name, f.file_type))
                cmd = None
            if cmd and ((cmd != "vlog") or not common_compilation):
                args += ["-quiet"]
                args += ["-work", f.logical_name]
                args += [f.name.replace("\\", "/")]
                tcl_build_rtl.write("{} {}\n".format(cmd, " ".join(args)))
        if common_compilation:
            args = self.tool_options.get("vlog_options", [])
            for k, v in self.vlogdefine.items():
                args += ["+define+{}={}".format(k, self._param_value_str(v))]

            _vlog_files = []
            has_sv = False
            for f in vlog_files:
                _vlog_files.append(f.name.replace("\\", "/"))
                if f.file_type.startswith("systemVerilogSource"):
                    has_sv = True

            if has_sv:
                args += ["-sv"]
            args += vlog_include_dirs
            args += ["-quiet"]
            args += ["-work", "work"]
            args += ["-mfcu"]
            tcl_build_rtl.write(f"vlog {' '.join(args)} {' '.join(_vlog_files)}")

    def _write_makefile(self):
        vpi_make = open(os.path.join(self.work_root, "Makefile"), "w")
        _parameters = []
        for key, value in self.vlogparam.items():
            _parameters += ["{}={}".format(key, self._param_value_str(value))]
        for key, value in self.generic.items():
            _parameters += [
                "{}={}".format(key, self._param_value_str(value, bool_is_str=True))
            ]
        _plusargs = []
        for key, value in self.plusarg.items():
            _plusargs += ["{}={}".format(key, self._param_value_str(value))]

        _vsim_options = self.tool_options.get("vsim_options", [])

        _modules = [m["name"] for m in self.vpi_modules]
        _clean_targets = " ".join(["clean_" + m for m in _modules])
        _s = MAKE_HEADER.format(
            toplevel=self.toplevel,
            parameters=" ".join(_parameters),
            plusargs=" ".join(_plusargs),
            vsim_options=" ".join(_vsim_options),
            modules=" ".join(_modules),
            clean_targets=_clean_targets,
        )
        vpi_make.write(_s)

        for vpi_module in self.vpi_modules:
            _name = vpi_module["name"]
            _objs = [os.path.splitext(s)[0] + ".o" for s in vpi_module["src_files"]]
            _libs = ["-l" + l for l in vpi_module["libs"]]
            _incs = ["-I" + d for d in vpi_module["include_dirs"]]
            _s = VPI_MAKE_SECTION.format(
                name=_name,
                objs=" ".join(_objs),
                libs=" ".join(_libs),
                incs=" ".join(_incs),
            )
            vpi_make.write(_s)

        vpi_make.close()

    def configure_main(self):
        tcl_main = open(os.path.join(self.work_root, "edalize_main.tcl"), "w")
        tcl_main.write("onerror { quit -code 1; }\n")
        tcl_main.write("do edalize_build_rtl.tcl\n")

        self._write_build_rtl_tcl_file(tcl_main)
        self._write_makefile()
        tcl_main.close()

    def run_main(self):
        args = ["run"]

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ["{}={}".format(key, self._param_value_str(value))]
            args.append("PLUSARGS=" + " ".join(plusargs))

        self._run_tool("make", args)
