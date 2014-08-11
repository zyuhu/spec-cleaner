#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import unittest
import os
import shutil
import tempfile
import difflib
import datetime
from mock import patch

from spec_cleaner import RpmSpecCleaner

class TestCompare(unittest.TestCase):
    """
    We run individual tests to verify the content compared to expected results
    """

    def setUp(self):
        """
        Declare global scope variables for further use.
        """

        self.input_dir = self._get_input_dir()
        self.fixtures_dir = self._get_fixtures_dir()
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_file_rerun = tempfile.NamedTemporaryFile()

    def tearDown(self):
        """
        Remove the tmp directory
        """
        shutil.rmtree(self.tmp_dir)

    def _difftext(self, lines1, lines2, junk=None):
        junk = junk or (' ', '\t')
        # result is a generator
        result = difflib.ndiff(lines1, lines2, charjunk=lambda x: x in junk)
        read = []
        for line in result:
            read.append(line)
            # lines that don't start with a ' ' are diff ones
            if not line.startswith(' '):
                self.fail(''.join(read + list(result)))

    def assertStreamEqual(self, stream1, stream2, junk=None):
        """compare two streams (using difflib and readlines())"""
        # if stream2 is stream2, readlines() on stream1 will also read lines
        # in stream2, so they'll appear different, although they're not
        if stream1 is stream2:
            return
        # make sure we compare from the beginning of the stream
        stream1.seek(0)
        stream2.seek(0)
        # ocmpare
        self._difftext(stream1.readlines(), stream2.readlines(), junk)

    def _get_input_dir(self):
        """
        Return path for input files used by tests
        """
        return os.path.join(os.getcwd(), 'tests/in/')

    def _get_fixtures_dir(self):
        """
        Return path for representative output specs
        """
        return os.path.join(os.getcwd(), 'tests/out/')

    def _obtain_list_of_tests(self):
        """
        Generate list of tests we are going to use according to what is on hdd
        """

        test_files = list()

        for spec in os.listdir(self.fixtures_dir):
            if spec.endswith(".spec"):
                test_files.append(spec)

        return test_files

    def _run_individual_test(self, infile, outfile):
        """
        Run the cleaner as specified and store the output for further comparison.
        """
        cleaner = RpmSpecCleaner(infile, outfile, True, False, False, 'vimdiff')
        cleaner.run()

    @patch('spec_cleaner.rpmcopyright.datetime')
    def test_input_files(self, datetime_mock):
        datetime_mock.datetime.now.return_value = (datetime.datetime(2013, 01, 01))
        for test in self._obtain_list_of_tests():
            infile = os.path.join(self.input_dir, test)
            compare = os.path.join(self.fixtures_dir, test)
            tmp_file = os.path.join(self.tmp_dir, test)

            # first try to generate cleaned content from messed up
            self._run_individual_test(infile, tmp_file)
            self.assertStreamEqual(open(compare), open(tmp_file))

            # second run it again while ensuring it didn't change
            self._run_individual_test(tmp_file, self.tmp_file_rerun.name)
            self.assertStreamEqual(open(compare), open (self.tmp_file_rerun.name))