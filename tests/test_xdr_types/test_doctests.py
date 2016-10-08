'''
Created on 8 okt. 2016

@author: Ruud
'''
import unittest
import doctest
import xdrlib2.xdr_types

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(xdrlib2.xdr_types))
    return tests



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()