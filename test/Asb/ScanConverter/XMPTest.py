'''
Created on 13.05.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Ocr.PdfService import XMPMetadata


class TestXMP(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testXMP(self):
        
        metadata = XMPMetadata("test2.pdf")
        metadata.add_subject("Kernkraftwerk (Wyhl)", gnd="108657589X")
        metadata.write_changes()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()