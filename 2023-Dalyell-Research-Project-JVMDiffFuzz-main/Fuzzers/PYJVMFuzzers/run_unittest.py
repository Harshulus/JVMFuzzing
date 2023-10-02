#!/usr/bin/env python3
import unittest
from pyjvm.Machine import Machine
from pyjvm.jstdlib.StdlibLoader import load_stdlib_classes
import sys

class HiTest(unittest.TestCase):

    def test_main(self):
        """
        Tests the JVM on the instruction sequence given in the temp file
        """
        self.jvm = Machine()
        load_stdlib_classes(self.jvm)
        self.jvm.load_class_file('test.class')
        self.jvm.call_function('test/main')

if __name__ == '__main__':
    HiTest().test_main()
