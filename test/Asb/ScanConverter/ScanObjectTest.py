'''
Created on 23.04.2022

@author: michael
'''
import unittest
from Asb.ScanConverter.ScanService import Scan


class ScanObjectTest(unittest.TestCase):


    def testHalfSizeExact(self):
        
        small_scan = Scan("some_file_name")
        small_scan.height = 100
        small_scan.width = 50
        
        large_scan = Scan("other_file_name")
        large_scan.height = 100
        large_scan.width = 100
        
        self.assertTrue(small_scan.is_half_page_of(large_scan), "Half size check does not work")

    def testHalfSizeApproximatelyI(self):
        
        small_scan = Scan("some_file_name")
        small_scan.height = 100
        small_scan.width = 50
        
        large_scan = Scan("other_file_name")
        large_scan.height = 102
        large_scan.width = 98
        
        self.assertTrue(small_scan.is_half_page_of(large_scan), "Half size check does not work")

    def testHalfSizeApproximatelyII(self):
        
        small_scan = Scan("some_file_name")
        small_scan.height = 102
        small_scan.width = 52
        
        large_scan = Scan("other_file_name")
        large_scan.height = 100
        large_scan.width = 100
        
        self.assertTrue(small_scan.is_half_page_of(large_scan), "Half size check does not work")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()