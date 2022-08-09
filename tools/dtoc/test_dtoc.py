#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) 2012 The Chromium OS Authors.
#

"""Tests for the dtb_platdata module

This includes unit tests for some functions and functional tests for the dtoc
tool.
"""

import collections
import glob
import os
import struct
import unittest

from dtb_platdata import get_value
from dtb_platdata import tab_to
from dtoc import dtb_platdata
from dtoc import fdt
from dtoc import fdt_util
from dtoc.src_scan import conv_name_to_c
from dtoc.src_scan import get_compat_name
from patman import test_util
from patman import tools

OUR_PATH = os.path.dirname(os.path.realpath(__file__))


HEADER = '''/*
 * DO NOT MODIFY
 *
 * Defines the structs used to hold devicetree data.
 * This was generated by dtoc from a .dtb (device tree binary) file.
 */

#include <stdbool.h>
#include <linux/libfdt.h>'''

C_HEADER = '''/*
 * DO NOT MODIFY
 *
 * Declares the U_BOOT_DRIVER() records and platform data.
 * This was generated by dtoc from a .dtb (device tree binary) file.
 */

/* Allow use of U_BOOT_DRVINFO() in this file */
#define DT_PLAT_C

#include <common.h>
#include <dm.h>
#include <dt-structs.h>
'''

# This is a test so is allowed to access private things in the module it is
# testing
# pylint: disable=W0212

def get_dtb_file(dts_fname, capture_stderr=False):
    """Compile a .dts file to a .dtb

    Args:
        dts_fname (str): Filename of .dts file in the current directory
        capture_stderr (bool): True to capture and discard stderr output

    Returns:
        str: Filename of compiled file in output directory
    """
    return fdt_util.EnsureCompiled(os.path.join(OUR_PATH, dts_fname),
                                   capture_stderr=capture_stderr)


class TestDtoc(unittest.TestCase):
    """Tests for dtoc"""
    @classmethod
    def setUpClass(cls):
        tools.PrepareOutputDir(None)
        cls.maxDiff = None

    @classmethod
    def tearDownClass(cls):
        tools.FinaliseOutputDir()

    @staticmethod
    def _write_python_string(fname, data):
        """Write a string with tabs expanded as done in this Python file

        Args:
            fname (str): Filename to write to
            data (str): Raw string to convert
        """
        data = data.replace('\t', '\\t')
        with open(fname, 'w') as fout:
            fout.write(data)

    def _check_strings(self, expected, actual):
        """Check that a string matches its expected value

        If the strings do not match, they are written to the /tmp directory in
        the same Python format as is used here in the test. This allows for
        easy comparison and update of the tests.

        Args:
            expected (str): Expected string
            actual (str): Actual string
        """
        if expected != actual:
            self._write_python_string('/tmp/binman.expected', expected)
            self._write_python_string('/tmp/binman.actual', actual)
            print('Failures written to /tmp/binman.{expected,actual}')
        self.assertEqual(expected, actual)

    @staticmethod
    def run_test(args, dtb_file, output):
        """Run a test using dtoc

        Args:
            args (list of str): List of arguments for dtoc
            dtb_file (str): Filename of .dtb file
            output (str): Filename of output file
        """
        dtb_platdata.run_steps(args, dtb_file, False, output, [], True)

    def test_name(self):
        """Test conversion of device tree names to C identifiers"""
        self.assertEqual('serial_at_0x12', conv_name_to_c('serial@0x12'))
        self.assertEqual('vendor_clock_frequency',
                         conv_name_to_c('vendor,clock-frequency'))
        self.assertEqual('rockchip_rk3399_sdhci_5_1',
                         conv_name_to_c('rockchip,rk3399-sdhci-5.1'))

    def test_tab_to(self):
        """Test operation of tab_to() function"""
        self.assertEqual('fred ', tab_to(0, 'fred'))
        self.assertEqual('fred\t', tab_to(1, 'fred'))
        self.assertEqual('fred was here ', tab_to(1, 'fred was here'))
        self.assertEqual('fred was here\t\t', tab_to(3, 'fred was here'))
        self.assertEqual('exactly8 ', tab_to(1, 'exactly8'))
        self.assertEqual('exactly8\t', tab_to(2, 'exactly8'))

    def test_get_value(self):
        """Test operation of get_value() function"""
        self.assertEqual('0x45',
                         get_value(fdt.Type.INT, struct.pack('>I', 0x45)))
        self.assertEqual('0x45',
                         get_value(fdt.Type.BYTE, struct.pack('<I', 0x45)))
        self.assertEqual('0x0',
                         get_value(fdt.Type.BYTE, struct.pack('>I', 0x45)))
        self.assertEqual('"test"', get_value(fdt.Type.STRING, 'test'))
        self.assertEqual('true', get_value(fdt.Type.BOOL, None))

    def test_get_compat_name(self):
        """Test operation of get_compat_name() function"""
        Prop = collections.namedtuple('Prop', ['value'])
        Node = collections.namedtuple('Node', ['props'])

        prop = Prop(['rockchip,rk3399-sdhci-5.1', 'arasan,sdhci-5.1'])
        node = Node({'compatible': prop})
        self.assertEqual((['rockchip_rk3399_sdhci_5_1', 'arasan_sdhci_5_1']),
                         get_compat_name(node))

        prop = Prop(['rockchip,rk3399-sdhci-5.1'])
        node = Node({'compatible': prop})
        self.assertEqual((['rockchip_rk3399_sdhci_5_1']),
                         get_compat_name(node))

        prop = Prop(['rockchip,rk3399-sdhci-5.1', 'arasan,sdhci-5.1', 'third'])
        node = Node({'compatible': prop})
        self.assertEqual((['rockchip_rk3399_sdhci_5_1',
                           'arasan_sdhci_5_1', 'third']),
                         get_compat_name(node))

    def test_empty_file(self):
        """Test output from a device tree file with no nodes"""
        dtb_file = get_dtb_file('dtoc_test_empty.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            lines = infile.read().splitlines()
        self.assertEqual(HEADER.splitlines(), lines)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            lines = infile.read().splitlines()
        self.assertEqual(C_HEADER.splitlines() + [''], lines)

    struct_text = HEADER + '''
struct dtd_sandbox_i2c_test {
};
struct dtd_sandbox_pmic_test {
\tbool\t\tlow_power;
\tfdt64_t\t\treg[2];
};
struct dtd_sandbox_spl_test {
\tconst char *	acpi_name;
\tbool\t\tboolval;
\tunsigned char\tbytearray[3];
\tunsigned char\tbyteval;
\tfdt32_t\t\tintarray[4];
\tfdt32_t\t\tintval;
\tunsigned char\tlongbytearray[9];
\tunsigned char\tnotstring[5];
\tconst char *\tstringarray[3];
\tconst char *\tstringval;
};
'''

    platdata_text = C_HEADER + '''
/* Node /i2c@0 index 0 */
static struct dtd_sandbox_i2c_test dtv_i2c_at_0 = {
};
U_BOOT_DRVINFO(i2c_at_0) = {
\t.name\t\t= "sandbox_i2c_test",
\t.plat\t= &dtv_i2c_at_0,
\t.plat_size\t= sizeof(dtv_i2c_at_0),
\t.parent_idx\t= -1,
};

/* Node /i2c@0/pmic@9 index 1 */
static struct dtd_sandbox_pmic_test dtv_pmic_at_9 = {
\t.low_power\t\t= true,
\t.reg\t\t\t= {0x9, 0x0},
};
U_BOOT_DRVINFO(pmic_at_9) = {
\t.name\t\t= "sandbox_pmic_test",
\t.plat\t= &dtv_pmic_at_9,
\t.plat_size\t= sizeof(dtv_pmic_at_9),
\t.parent_idx\t= 0,
};

/* Node /spl-test index 2 */
static struct dtd_sandbox_spl_test dtv_spl_test = {
\t.boolval\t\t= true,
\t.bytearray\t\t= {0x6, 0x0, 0x0},
\t.byteval\t\t= 0x5,
\t.intarray\t\t= {0x2, 0x3, 0x4, 0x0},
\t.intval\t\t\t= 0x1,
\t.longbytearray\t\t= {0x9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x10,
\t\t0x11},
\t.notstring\t\t= {0x20, 0x21, 0x22, 0x10, 0x0},
\t.stringarray\t\t= {"multi-word", "message", ""},
\t.stringval\t\t= "message",
};
U_BOOT_DRVINFO(spl_test) = {
\t.name\t\t= "sandbox_spl_test",
\t.plat\t= &dtv_spl_test,
\t.plat_size\t= sizeof(dtv_spl_test),
\t.parent_idx\t= -1,
};

/* Node /spl-test2 index 3 */
static struct dtd_sandbox_spl_test dtv_spl_test2 = {
\t.acpi_name\t\t= "\\\\_SB.GPO0",
\t.bytearray\t\t= {0x1, 0x23, 0x34},
\t.byteval\t\t= 0x8,
\t.intarray\t\t= {0x5, 0x0, 0x0, 0x0},
\t.intval\t\t\t= 0x3,
\t.longbytearray\t\t= {0x9, 0xa, 0xb, 0xc, 0x0, 0x0, 0x0, 0x0,
\t\t0x0},
\t.stringarray\t\t= {"another", "multi-word", "message"},
\t.stringval\t\t= "message2",
};
U_BOOT_DRVINFO(spl_test2) = {
\t.name\t\t= "sandbox_spl_test",
\t.plat\t= &dtv_spl_test2,
\t.plat_size\t= sizeof(dtv_spl_test2),
\t.parent_idx\t= -1,
};

/* Node /spl-test3 index 4 */
static struct dtd_sandbox_spl_test dtv_spl_test3 = {
\t.longbytearray\t\t= {0x9, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x10,
\t\t0x0},
\t.stringarray\t\t= {"one", "", ""},
};
U_BOOT_DRVINFO(spl_test3) = {
\t.name\t\t= "sandbox_spl_test",
\t.plat\t= &dtv_spl_test3,
\t.plat_size\t= sizeof(dtv_spl_test3),
\t.parent_idx\t= -1,
};

'''

    def test_simple(self):
        """Test output from some simple nodes with various types of data"""
        dtb_file = get_dtb_file('dtoc_test_simple.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()

        self._check_strings(self.struct_text, data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()

        self._check_strings(self.platdata_text, data)

        # Try the 'all' command
        self.run_test(['all'], dtb_file, output)
        data = tools.ReadFile(output, binary=False)
        self._check_strings(self.platdata_text + self.struct_text, data)

    def test_driver_alias(self):
        """Test output from a device tree file with a driver alias"""
        dtb_file = get_dtb_file('dtoc_test_driver_alias.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_sandbox_gpio {
\tconst char *\tgpio_bank_name;
\tbool\t\tgpio_controller;
\tfdt32_t\t\tsandbox_gpio_count;
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /gpios@0 index 0 */
static struct dtd_sandbox_gpio dtv_gpios_at_0 = {
\t.gpio_bank_name\t\t= "a",
\t.gpio_controller\t= true,
\t.sandbox_gpio_count\t= 0x14,
};
U_BOOT_DRVINFO(gpios_at_0) = {
\t.name\t\t= "sandbox_gpio",
\t.plat\t= &dtv_gpios_at_0,
\t.plat_size\t= sizeof(dtv_gpios_at_0),
\t.parent_idx\t= -1,
};

''', data)

    def test_invalid_driver(self):
        """Test output from a device tree file with an invalid driver"""
        dtb_file = get_dtb_file('dtoc_test_invalid_driver.dts')
        output = tools.GetOutputFilename('output')
        with test_util.capture_sys_output() as _:
            dtb_platdata.run_steps(['struct'], dtb_file, False, output, [])
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_invalid {
};
''', data)

        with test_util.capture_sys_output() as _:
            dtb_platdata.run_steps(['platdata'], dtb_file, False, output, [])
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /spl-test index 0 */
static struct dtd_invalid dtv_spl_test = {
};
U_BOOT_DRVINFO(spl_test) = {
\t.name\t\t= "invalid",
\t.plat\t= &dtv_spl_test,
\t.plat_size\t= sizeof(dtv_spl_test),
\t.parent_idx\t= -1,
};

''', data)

    def test_phandle(self):
        """Test output from a node containing a phandle reference"""
        dtb_file = get_dtb_file('dtoc_test_phandle.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_source {
\tstruct phandle_2_arg clocks[4];
};
struct dtd_target {
\tfdt32_t\t\tintval;
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /phandle2-target index 0 */
static struct dtd_target dtv_phandle2_target = {
\t.intval\t\t\t= 0x1,
};
U_BOOT_DRVINFO(phandle2_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle2_target,
\t.plat_size\t= sizeof(dtv_phandle2_target),
\t.parent_idx\t= -1,
};

/* Node /phandle3-target index 1 */
static struct dtd_target dtv_phandle3_target = {
\t.intval\t\t\t= 0x2,
};
U_BOOT_DRVINFO(phandle3_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle3_target,
\t.plat_size\t= sizeof(dtv_phandle3_target),
\t.parent_idx\t= -1,
};

/* Node /phandle-source index 2 */
static struct dtd_source dtv_phandle_source = {
\t.clocks\t\t\t= {
\t\t\t{4, {}},
\t\t\t{0, {11}},
\t\t\t{1, {12, 13}},
\t\t\t{4, {}},},
};
U_BOOT_DRVINFO(phandle_source) = {
\t.name\t\t= "source",
\t.plat\t= &dtv_phandle_source,
\t.plat_size\t= sizeof(dtv_phandle_source),
\t.parent_idx\t= -1,
};

/* Node /phandle-source2 index 3 */
static struct dtd_source dtv_phandle_source2 = {
\t.clocks\t\t\t= {
\t\t\t{4, {}},},
};
U_BOOT_DRVINFO(phandle_source2) = {
\t.name\t\t= "source",
\t.plat\t= &dtv_phandle_source2,
\t.plat_size\t= sizeof(dtv_phandle_source2),
\t.parent_idx\t= -1,
};

/* Node /phandle-target index 4 */
static struct dtd_target dtv_phandle_target = {
\t.intval\t\t\t= 0x0,
};
U_BOOT_DRVINFO(phandle_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle_target,
\t.plat_size\t= sizeof(dtv_phandle_target),
\t.parent_idx\t= -1,
};

''', data)

    def test_phandle_single(self):
        """Test output from a node containing a phandle reference"""
        dtb_file = get_dtb_file('dtoc_test_phandle_single.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_source {
\tstruct phandle_0_arg clocks[1];
};
struct dtd_target {
\tfdt32_t\t\tintval;
};
''', data)

    def test_phandle_reorder(self):
        """Test that phandle targets are generated before their references"""
        dtb_file = get_dtb_file('dtoc_test_phandle_reorder.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /phandle-source2 index 0 */
static struct dtd_source dtv_phandle_source2 = {
\t.clocks\t\t\t= {
\t\t\t{1, {}},},
};
U_BOOT_DRVINFO(phandle_source2) = {
\t.name\t\t= "source",
\t.plat\t= &dtv_phandle_source2,
\t.plat_size\t= sizeof(dtv_phandle_source2),
\t.parent_idx\t= -1,
};

/* Node /phandle-target index 1 */
static struct dtd_target dtv_phandle_target = {
};
U_BOOT_DRVINFO(phandle_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle_target,
\t.plat_size\t= sizeof(dtv_phandle_target),
\t.parent_idx\t= -1,
};

''', data)

    def test_phandle_cd_gpio(self):
        """Test that phandle targets are generated when unsing cd-gpios"""
        dtb_file = get_dtb_file('dtoc_test_phandle_cd_gpios.dts')
        output = tools.GetOutputFilename('output')
        dtb_platdata.run_steps(['platdata'], dtb_file, False, output, [], True)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /phandle2-target index 0 */
static struct dtd_target dtv_phandle2_target = {
\t.intval\t\t\t= 0x1,
};
U_BOOT_DRVINFO(phandle2_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle2_target,
\t.plat_size\t= sizeof(dtv_phandle2_target),
\t.parent_idx\t= -1,
};

/* Node /phandle3-target index 1 */
static struct dtd_target dtv_phandle3_target = {
\t.intval\t\t\t= 0x2,
};
U_BOOT_DRVINFO(phandle3_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle3_target,
\t.plat_size\t= sizeof(dtv_phandle3_target),
\t.parent_idx\t= -1,
};

/* Node /phandle-source index 2 */
static struct dtd_source dtv_phandle_source = {
\t.cd_gpios\t\t= {
\t\t\t{4, {}},
\t\t\t{0, {11}},
\t\t\t{1, {12, 13}},
\t\t\t{4, {}},},
};
U_BOOT_DRVINFO(phandle_source) = {
\t.name\t\t= "source",
\t.plat\t= &dtv_phandle_source,
\t.plat_size\t= sizeof(dtv_phandle_source),
\t.parent_idx\t= -1,
};

/* Node /phandle-source2 index 3 */
static struct dtd_source dtv_phandle_source2 = {
\t.cd_gpios\t\t= {
\t\t\t{4, {}},},
};
U_BOOT_DRVINFO(phandle_source2) = {
\t.name\t\t= "source",
\t.plat\t= &dtv_phandle_source2,
\t.plat_size\t= sizeof(dtv_phandle_source2),
\t.parent_idx\t= -1,
};

/* Node /phandle-target index 4 */
static struct dtd_target dtv_phandle_target = {
\t.intval\t\t\t= 0x0,
};
U_BOOT_DRVINFO(phandle_target) = {
\t.name\t\t= "target",
\t.plat\t= &dtv_phandle_target,
\t.plat_size\t= sizeof(dtv_phandle_target),
\t.parent_idx\t= -1,
};

''', data)

    def test_phandle_bad(self):
        """Test a node containing an invalid phandle fails"""
        dtb_file = get_dtb_file('dtoc_test_phandle_bad.dts',
                                capture_stderr=True)
        output = tools.GetOutputFilename('output')
        with self.assertRaises(ValueError) as exc:
            self.run_test(['struct'], dtb_file, output)
        self.assertIn("Cannot parse 'clocks' in node 'phandle-source'",
                      str(exc.exception))

    def test_phandle_bad2(self):
        """Test a phandle target missing its #*-cells property"""
        dtb_file = get_dtb_file('dtoc_test_phandle_bad2.dts',
                                capture_stderr=True)
        output = tools.GetOutputFilename('output')
        with self.assertRaises(ValueError) as exc:
            self.run_test(['struct'], dtb_file, output)
        self.assertIn("Node 'phandle-target' has no cells property",
                      str(exc.exception))

    def test_addresses64(self):
        """Test output from a node with a 'reg' property with na=2, ns=2"""
        dtb_file = get_dtb_file('dtoc_test_addr64.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_test1 {
\tfdt64_t\t\treg[2];
};
struct dtd_test2 {
\tfdt64_t\t\treg[2];
};
struct dtd_test3 {
\tfdt64_t\t\treg[4];
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /test1 index 0 */
static struct dtd_test1 dtv_test1 = {
\t.reg\t\t\t= {0x1234, 0x5678},
};
U_BOOT_DRVINFO(test1) = {
\t.name\t\t= "test1",
\t.plat\t= &dtv_test1,
\t.plat_size\t= sizeof(dtv_test1),
\t.parent_idx\t= -1,
};

/* Node /test2 index 1 */
static struct dtd_test2 dtv_test2 = {
\t.reg\t\t\t= {0x1234567890123456, 0x9876543210987654},
};
U_BOOT_DRVINFO(test2) = {
\t.name\t\t= "test2",
\t.plat\t= &dtv_test2,
\t.plat_size\t= sizeof(dtv_test2),
\t.parent_idx\t= -1,
};

/* Node /test3 index 2 */
static struct dtd_test3 dtv_test3 = {
\t.reg\t\t\t= {0x1234567890123456, 0x9876543210987654, 0x2, 0x3},
};
U_BOOT_DRVINFO(test3) = {
\t.name\t\t= "test3",
\t.plat\t= &dtv_test3,
\t.plat_size\t= sizeof(dtv_test3),
\t.parent_idx\t= -1,
};

''', data)

    def test_addresses32(self):
        """Test output from a node with a 'reg' property with na=1, ns=1"""
        dtb_file = get_dtb_file('dtoc_test_addr32.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_test1 {
\tfdt32_t\t\treg[2];
};
struct dtd_test2 {
\tfdt32_t\t\treg[4];
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /test1 index 0 */
static struct dtd_test1 dtv_test1 = {
\t.reg\t\t\t= {0x1234, 0x5678},
};
U_BOOT_DRVINFO(test1) = {
\t.name\t\t= "test1",
\t.plat\t= &dtv_test1,
\t.plat_size\t= sizeof(dtv_test1),
\t.parent_idx\t= -1,
};

/* Node /test2 index 1 */
static struct dtd_test2 dtv_test2 = {
\t.reg\t\t\t= {0x12345678, 0x98765432, 0x2, 0x3},
};
U_BOOT_DRVINFO(test2) = {
\t.name\t\t= "test2",
\t.plat\t= &dtv_test2,
\t.plat_size\t= sizeof(dtv_test2),
\t.parent_idx\t= -1,
};

''', data)

    def test_addresses64_32(self):
        """Test output from a node with a 'reg' property with na=2, ns=1"""
        dtb_file = get_dtb_file('dtoc_test_addr64_32.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_test1 {
\tfdt64_t\t\treg[2];
};
struct dtd_test2 {
\tfdt64_t\t\treg[2];
};
struct dtd_test3 {
\tfdt64_t\t\treg[4];
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /test1 index 0 */
static struct dtd_test1 dtv_test1 = {
\t.reg\t\t\t= {0x123400000000, 0x5678},
};
U_BOOT_DRVINFO(test1) = {
\t.name\t\t= "test1",
\t.plat\t= &dtv_test1,
\t.plat_size\t= sizeof(dtv_test1),
\t.parent_idx\t= -1,
};

/* Node /test2 index 1 */
static struct dtd_test2 dtv_test2 = {
\t.reg\t\t\t= {0x1234567890123456, 0x98765432},
};
U_BOOT_DRVINFO(test2) = {
\t.name\t\t= "test2",
\t.plat\t= &dtv_test2,
\t.plat_size\t= sizeof(dtv_test2),
\t.parent_idx\t= -1,
};

/* Node /test3 index 2 */
static struct dtd_test3 dtv_test3 = {
\t.reg\t\t\t= {0x1234567890123456, 0x98765432, 0x2, 0x3},
};
U_BOOT_DRVINFO(test3) = {
\t.name\t\t= "test3",
\t.plat\t= &dtv_test3,
\t.plat_size\t= sizeof(dtv_test3),
\t.parent_idx\t= -1,
};

''', data)

    def test_addresses32_64(self):
        """Test output from a node with a 'reg' property with na=1, ns=2"""
        dtb_file = get_dtb_file('dtoc_test_addr32_64.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_test1 {
\tfdt64_t\t\treg[2];
};
struct dtd_test2 {
\tfdt64_t\t\treg[2];
};
struct dtd_test3 {
\tfdt64_t\t\treg[4];
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /test1 index 0 */
static struct dtd_test1 dtv_test1 = {
\t.reg\t\t\t= {0x1234, 0x567800000000},
};
U_BOOT_DRVINFO(test1) = {
\t.name\t\t= "test1",
\t.plat\t= &dtv_test1,
\t.plat_size\t= sizeof(dtv_test1),
\t.parent_idx\t= -1,
};

/* Node /test2 index 1 */
static struct dtd_test2 dtv_test2 = {
\t.reg\t\t\t= {0x12345678, 0x9876543210987654},
};
U_BOOT_DRVINFO(test2) = {
\t.name\t\t= "test2",
\t.plat\t= &dtv_test2,
\t.plat_size\t= sizeof(dtv_test2),
\t.parent_idx\t= -1,
};

/* Node /test3 index 2 */
static struct dtd_test3 dtv_test3 = {
\t.reg\t\t\t= {0x12345678, 0x9876543210987654, 0x2, 0x3},
};
U_BOOT_DRVINFO(test3) = {
\t.name\t\t= "test3",
\t.plat\t= &dtv_test3,
\t.plat_size\t= sizeof(dtv_test3),
\t.parent_idx\t= -1,
};

''', data)

    def test_bad_reg(self):
        """Test that a reg property with an invalid type generates an error"""
        # Capture stderr since dtc will emit warnings for this file
        dtb_file = get_dtb_file('dtoc_test_bad_reg.dts', capture_stderr=True)
        output = tools.GetOutputFilename('output')
        with self.assertRaises(ValueError) as exc:
            self.run_test(['struct'], dtb_file, output)
        self.assertIn("Node 'spl-test' reg property is not an int",
                      str(exc.exception))

    def test_bad_reg2(self):
        """Test that a reg property with an invalid cell count is detected"""
        # Capture stderr since dtc will emit warnings for this file
        dtb_file = get_dtb_file('dtoc_test_bad_reg2.dts', capture_stderr=True)
        output = tools.GetOutputFilename('output')
        with self.assertRaises(ValueError) as exc:
            self.run_test(['struct'], dtb_file, output)
        self.assertIn(
            "Node 'spl-test' reg property has 3 cells which is not a multiple of na + ns = 1 + 1)",
            str(exc.exception))

    def test_add_prop(self):
        """Test that a subequent node can add a new property to a struct"""
        dtb_file = get_dtb_file('dtoc_test_add_prop.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['struct'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(HEADER + '''
struct dtd_sandbox_spl_test {
\tfdt32_t\t\tintarray;
\tfdt32_t\t\tintval;
};
''', data)

        self.run_test(['platdata'], dtb_file, output)
        with open(output) as infile:
            data = infile.read()
        self._check_strings(C_HEADER + '''
/* Node /spl-test index 0 */
static struct dtd_sandbox_spl_test dtv_spl_test = {
\t.intval\t\t\t= 0x1,
};
U_BOOT_DRVINFO(spl_test) = {
\t.name\t\t= "sandbox_spl_test",
\t.plat\t= &dtv_spl_test,
\t.plat_size\t= sizeof(dtv_spl_test),
\t.parent_idx\t= -1,
};

/* Node /spl-test2 index 1 */
static struct dtd_sandbox_spl_test dtv_spl_test2 = {
\t.intarray\t\t= 0x5,
};
U_BOOT_DRVINFO(spl_test2) = {
\t.name\t\t= "sandbox_spl_test",
\t.plat\t= &dtv_spl_test2,
\t.plat_size\t= sizeof(dtv_spl_test2),
\t.parent_idx\t= -1,
};

''', data)

    def test_stdout(self):
        """Test output to stdout"""
        dtb_file = get_dtb_file('dtoc_test_simple.dts')
        with test_util.capture_sys_output() as (stdout, _):
            self.run_test(['struct'], dtb_file, None)
        self._check_strings(self.struct_text, stdout.getvalue())

    def test_multi_to_file(self):
        """Test output of multiple pieces to a single file"""
        dtb_file = get_dtb_file('dtoc_test_simple.dts')
        output = tools.GetOutputFilename('output')
        self.run_test(['all'], dtb_file, output)
        data = tools.ReadFile(output, binary=False)
        self._check_strings(self.platdata_text + self.struct_text, data)

    def test_no_command(self):
        """Test running dtoc without a command"""
        with self.assertRaises(ValueError) as exc:
            self.run_test([], '', '')
        self.assertIn("Please specify a command: struct, platdata",
                      str(exc.exception))

    def test_bad_command(self):
        """Test running dtoc with an invalid command"""
        dtb_file = get_dtb_file('dtoc_test_simple.dts')
        output = tools.GetOutputFilename('output')
        with self.assertRaises(ValueError) as exc:
            self.run_test(['invalid-cmd'], dtb_file, output)
        self.assertIn("Unknown command 'invalid-cmd': (use: platdata, struct)",
                      str(exc.exception))

    def test_output_conflict(self):
        """Test a conflict between and output dirs and output file"""
        with self.assertRaises(ValueError) as exc:
            dtb_platdata.run_steps(['all'], None, False, 'out', ['cdir'], True)
        self.assertIn("Must specify either output or output_dirs, not both",
                      str(exc.exception))

    def test_output_dirs(self):
        """Test outputting files to a directory"""
        # Remove the directory so that files from other tests are not there
        tools._RemoveOutputDir()
        tools.PrepareOutputDir(None)

        # This should create the .dts and .dtb in the output directory
        dtb_file = get_dtb_file('dtoc_test_simple.dts')
        outdir = tools.GetOutputDir()
        fnames = glob.glob(outdir + '/*')
        self.assertEqual(2, len(fnames))

        dtb_platdata.run_steps(['all'], dtb_file, False, None, [outdir], True)
        fnames = glob.glob(outdir + '/*')
        self.assertEqual(4, len(fnames))

        leafs = set(os.path.basename(fname) for fname in fnames)
        self.assertEqual(
            {'dt-structs-gen.h', 'source.dts', 'dt-plat.c', 'source.dtb'},
            leafs)
