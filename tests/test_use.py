'''
Created on 8 sep. 2016

@author: Ruud
'''
import unittest
import os
import sys
import time
import logging
import configparser
import datetime

import xdrlib2
from fs.opener import fsopendir
from fs.mountfs import MountFS

logging.basicConfig(filename='test_use.log', level=logging.DEBUG)

ini_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'xdr.ini'))

cp = configparser.ConfigParser()
with open(ini_file) as f:
    cp.read_file(f)
    
real_fs = fsopendir('mount://' + ini_file)
    
grammar = cp['files']['grammar']
parser = cp['files']['parser']
grammar_path = '/grammar/' + grammar
parser_path = '/parser/' + parser

# example_path = os.path.abspath(os.path.join(xdrlib2_path, '..', 'etc', 'example.xdr'))


class TestParser(unittest.TestCase):
    def setUp(self):
        self.assertNotIn('example', sys.modules)
        g_fs = fsopendir('mem://')
        p_fs = fsopendir('mem://')
        self.fs = MountFS()
        self.fs.mountdir('grammar', g_fs)
        self.fs.mountdir('parser', p_fs)
        
        for path in (grammar_path, parser_path):
            with real_fs.open(path) as source:
                with self.fs.open(path, 'w') as destination:
                    destination.write(source.read())
    
    def tearDown(self):
        if 'example' in sys.modules:
            del sys.modules['example']
            
    def test_parser_is_generated_when_it_does_not_exist(self):
        self.fs.remove(parser_path)
        self.assertFalse(self.fs.exists(parser_path))
        p = xdrlib2.use('example', fs=self.fs)
        self.assertTrue(self.fs.exists(parser_path))
        with real_fs.open(parser_path) as original:
            with self.fs.open(parser_path) as generated:
                for (orig_line, generated_line) in zip(original.readlines(), generated.readlines()):
                    if not orig_line.startswith('__version__'):
                        self.assertEqual(orig_line, generated_line)
                            
    def test_parser_is_regenerated_when_grammar_is_newer(self):
        grammar_time = self.fs.getinfo(grammar_path)['modified_time']
        parser_mtime = self.fs.getinfo(parser_path)['modified_time']
        # Artifically make the parser file an hour older than the grammar file
        self.fs.settimes(parser_path, modified_time=grammar_time - datetime.timedelta(hours=1))
        new_parser_mtime = self.fs.getinfo(parser_path)['modified_time']
        self.assertLess(new_parser_mtime, parser_mtime)
        start_time = datetime.datetime.now()
        self.assertLess(new_parser_mtime, start_time - datetime.timedelta(hours=1))
        p = xdrlib2.use('example', fs=self.fs)
        finish_time = datetime.datetime.now()
        generated_time = self.fs.getinfo(parser_path)['modified_time']
        self.assertGreater(generated_time, start_time)
        self.assertLess(generated_time, finish_time)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()