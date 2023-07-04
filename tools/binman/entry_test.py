# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) 2016 Google, Inc
# Written by Simon Glass <sjg@chromium.org>
#
# Test for the Entry class

import collections
import os
import sys
import unittest

from binman import entry
from binman.etype.blob import Entry_blob
from dtoc import fdt
from dtoc import fdt_util
from patman import tools

class TestEntry(unittest.TestCase):
    def setUp(self):
        tools.prepare_output_dir(None)

    def tearDown(self):
        tools.finalise_output_dir()

    def GetNode(self):
        binman_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        fname = fdt_util.EnsureCompiled(
            os.path.join(binman_dir,('test/005_simple.dts')))
        dtb = fdt.FdtScan(fname)
        return dtb.GetNode('/binman/u-boot')

    def _ReloadEntry(self):
        global entry
        if entry:
            if sys.version_info[0] >= 3:
                import importlib
                importlib.reload(entry)
            else:
                reload(entry)
        else:
            from binman import entry

    def testEntryContents(self):
        """Test the Entry bass class"""
        from binman import entry
        base_entry = entry.Entry(None, None, None)
        self.assertEqual(True, base_entry.ObtainContents())

    def testUnknownEntry(self):
        """Test that unknown entry types are detected"""
        Node = collections.namedtuple('Node', ['name', 'path'])
        node = Node('invalid-name', 'invalid-path')
        with self.assertRaises(ValueError) as e:
            entry.Entry.Create(None, node, node.name)
        self.assertIn("Unknown entry type 'invalid-name' in node "
                      "'invalid-path'", str(e.exception))

    def testUniqueName(self):
        """Test Entry.GetUniqueName"""
        Node = collections.namedtuple('Node', ['name', 'parent'])
        base_node = Node('root', None)
        base_entry = entry.Entry(None, None, base_node)
        self.assertEqual('root', base_entry.GetUniqueName())
        sub_node = Node('subnode', base_node)
        sub_entry = entry.Entry(None, None, sub_node)
        self.assertEqual('root.subnode', sub_entry.GetUniqueName())

    def testGetDefaultFilename(self):
        """Trivial test for this base class function"""
        base_entry = entry.Entry(None, None, None)
        self.assertIsNone(base_entry.GetDefaultFilename())

    def testBlobFdt(self):
        """Test the GetFdtEtype() method of the blob-dtb entries"""
        base = entry.Entry.Create(None, self.GetNode(), 'blob-dtb')
        self.assertIsNone(base.GetFdtEtype())

        dtb = entry.Entry.Create(None, self.GetNode(), 'u-boot-dtb')
        self.assertEqual('u-boot-dtb', dtb.GetFdtEtype())

    def testWriteChildData(self):
        """Test the WriteChildData() method of the base class"""
        base = entry.Entry.Create(None, self.GetNode(), 'blob-dtb')
        self.assertTrue(base.WriteChildData(base))

    def testReadChildData(self):
        """Test the ReadChildData() method of the base class"""
        base = entry.Entry.Create(None, self.GetNode(), 'blob-dtb')
        self.assertIsNone(base.ReadChildData(base))

    def testExpandedEntry(self):
        """Test use of an expanded entry when available"""
        base = entry.Entry.Create(None, self.GetNode())
        self.assertEqual('u-boot', base.etype)

        expanded = entry.Entry.Create(None, self.GetNode(), expanded=True)
        self.assertEqual('u-boot-expanded', expanded.etype)

        with self.assertRaises(ValueError) as e:
            entry.Entry.Create(None, self.GetNode(), 'missing', expanded=True)
        self.assertIn("Unknown entry type 'missing' in node '/binman/u-boot'",
                      str(e.exception))

    def testMissingEtype(self):
        """Test use of a blob etype when the requested one is not available"""
        ent = entry.Entry.Create(None, self.GetNode(), 'missing',
                                 missing_etype=True)
        self.assertTrue(isinstance(ent, Entry_blob))
        self.assertEquals('missing', ent.etype)


if __name__ == "__main__":
    unittest.main()
