'''
Created on 12 okt. 2016

@author: Ruud
'''
import unittest

import xdrlib2 as xdr


class FixedLengthOpaque(xdr.FixedOpaque):
    size = 5

class VarLengthOpaque(xdr.VarOpaque):
    size = 5
    
class TestString(xdr.String):
    size = 5
    
subclass_map = {xdr.FixedOpaque: FixedLengthOpaque,
                xdr.VarOpaque: VarLengthOpaque,
                xdr.String: TestString
                }


class TestInstantiation(unittest.TestCase):
    
    def test_instantiation_from_bytes(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(byte_str)
                self.assertIsInstance(blob, basecls)
                self.assertIsInstance(blob, bytearray)
                self.assertEqual(blob, byte_str)

    def test_instantiation_from_integers(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        int_list = [0, 255,0xab, 0xcd, 1]
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(int_list)
                self.assertIsInstance(blob, basecls)
                self.assertIsInstance(blob, bytearray)
                self.assertEqual(blob, byte_str)

    def test_instantiation_with_default_value(self):
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                if basecls is xdr.FixedOpaque:
                    self.assertEqual(subcls(), b'\0\0\0\0\0')
                else:
                    self.assertEqual(subcls(), b'')
        
    def test_instantiation_requries_correctly_sized_arguments(self):
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
#             for byte_str in (b'123', b'1234567890'):
            with self.subTest(basecls=basecls):
                if basecls is xdr.FixedOpaque:
                    self.assertRaises(ValueError, subcls, b'123')
                self.assertRaises(ValueError, subcls, b'1234567890')

    
class TestClassConstruction(unittest.TestCase):
    
    def test_class_construction_through_typedef(self):
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = basecls.typedef(size=5)
            with self.subTest(basecls=basecls):
                self.assertTrue(issubclass(subcls, basecls))
                self.assertTrue(basecls in subcls.__mro__)
    
    def test_class_construction_with_size_0(self):
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = basecls.typedef(size=0)
            with self.subTest(basecls=basecls):
                blob = subcls(())
                self.assertIsInstance(blob, bytearray)
                self.assertIsInstance(blob, subcls)
                self.assertEqual(blob, b'')

class TestItemReplacement(unittest.TestCase):

    def test_item_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(byte_str)
                blob[2] = 0
                self.assertEqual(blob, b'\0\xff\0\xcd\x01')

    def test_slice_replacement(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(byte_str)
                blob[2:4] = b'\0\0'
                self.assertEqual(blob, b'\0\xff\0\0\x01')

    def test_size_change_is_allowed_for_variable_arrays(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        for basecls in (xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(byte_str)
                del blob[2]
                blob[1:4] = b'\0'
                blob.append(3)
                blob.extend(b'no')
                self.assertEqual(blob, b'\0\0\x03no')
                del blob[1:]
                blob += b'yes'
                self.assertEqual(blob, b'\0yes')
        
    def test_incorrect_size_change_fails(self):
        byte_str = b'\0\xff\xab\xcd\x01'
        for basecls in (xdr.FixedOpaque, xdr.VarOpaque, xdr.String):
            subcls = subclass_map[basecls]
            with self.subTest(basecls=basecls):
                blob = subcls(byte_str)
                with self.assertRaises(ValueError):
                    blob += b'no way'
                if basecls is xdr.FixedOpaque:
                    with self.assertRaises(ValueError):
                        del blob[2]
                    with self.assertRaises(ValueError):
                        blob[2:4] = b'\0'
                    self.assertRaises(ValueError, blob.append, 3)
                    self.assertRaises(ValueError, blob.extend, b'no')

       



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()