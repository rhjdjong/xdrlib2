'''
Created on 11 okt. 2016

@author: Ruud
'''
import unittest
import xdrlib2 as xdr

class Test(unittest.TestCase):
    def setUp(self):
        self.optional_integer_type = xdr.Optional(xdr.Int32)
    

    def test_present_optional_value_encoding(self):
        x = self.optional_integer_type(3)
        y = self.optional_integer_type()
        for encoded_value in (x.encode(),
                              self.optional_integer_type.encode(x),
                              self.optional_integer_type.encode(3),
                              x.__class__.encode(x),
                              x.__class__.encode(3),
                              y.__class__.encode(x),
                              y.__class__.encode(3)):
            with self.subTest(encoded_value=encoded_value):
                self.assertEqual(encoded_value, xdr.TRUE.encode() + xdr.Int32(3).encode())  # @UndefinedVariable

    def test_absent_optional_value_encoding(self):
        x = self.optional_integer_type(3)
        y = self.optional_integer_type()
        for encoded_value in (y.encode(),
                              self.optional_integer_type.encode(y),
                              self.optional_integer_type.encode(None),
                              x.__class__.encode(y),
                              x.__class__.encode(None),
                              y.__class__.encode(y),
                              y.__class__.encode(None)):
            with self.subTest(encoded_value=encoded_value):
                self.assertEqual(encoded_value, xdr.FALSE.encode())  # @UndefinedVariable

    def test_present_value_decoding(self):
        encoded_value = xdr.TRUE.encode() + xdr.Int32(3).encode()  # @UndefinedVariable
        for obj in (self.optional_integer_type, # direct instantiation
                    self.optional_integer_type(3), # through a present value
                    self.optional_integer_type(3).__class__, # through the class of a present value
                    self.optional_integer_type(None), # through an absent value
                    self.optional_integer_type(None).__class__): # through the class of an absent value
            with self.subTest(obj=obj):
                y = obj.decode(encoded_value)
                self.assertEqual(y, 3)
                self.assertIsInstance(y, xdr.Int32)
                self.assertIsInstance(y, self.optional_integer_type)
                self.assertIsInstance(y, xdr.Optional)
        
    def test_absent_value_decoding(self):
        encoded_value = xdr.FALSE.encode()  # @UndefinedVariable
        for obj in (self.optional_integer_type, # direct instantiation
                    self.optional_integer_type(3), # through a present value
                    self.optional_integer_type(3).__class__, # through the class of a present value
                    self.optional_integer_type(None), # through an absent value
                    self.optional_integer_type(None).__class__): # through the class of an absent value
            with self.subTest(obj=obj):
                y = obj.decode(encoded_value)
                self.assertEqual(y, None)
                self.assertNotIsInstance(y, xdr.Int32)
                self.assertIsInstance(y, xdr.Void)
                self.assertIsInstance(y, self.optional_integer_type)
                self.assertIsInstance(y, xdr.Optional)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()