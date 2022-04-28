'''
Created on 23.04.2022

@author: michael
'''
import unittest
from Asb.ScanConverter.ScanService import Scan, Project, SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD,\
SCAN_PROFILE_DOUBLE_PAGES_FEEDER


class PageObjectTest(unittest.TestCase):


    def create_single_page_scan(self):
        
        scan = Scan("some file name")
        scan.height = 100
        scan.width = 50
        return scan

    def create_double_page_scan(self):
        
        scan = Scan("some file name")
        scan.height = 103
        scan.width = 103
        return scan

    def testSimpleOrdering(self):
        
        project = Project()
        project.add_scan(self.create_single_page_scan())
        project.add_scan(self.create_single_page_scan())
        project.add_scan(self.create_single_page_scan())
        project.add_scan(self.create_single_page_scan())
        project.add_scan(self.create_single_page_scan())
        
        self.assertEqual(5, len(project.scans))
        self.assertEqual((4,), project.scans[3].page_nos)

    def testOverheadOrderingOnlyDoublePages(self):
        
        project = Project()
        project.change_scan_profile(SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD)
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        
        self.assertEqual(5, len(project.scans))
        self.assertEqual((1,2), project.scans[0].page_nos)
        self.assertEqual((7,8), project.scans[3].page_nos)

    def testOverheadOrderingWithSinglePages(self):
        
        project = Project()
        project.change_scan_profile(SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD)
        project.add_scan(self.create_single_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_single_page_scan())
        
        self.assertEqual(5, len(project.scans))
        self.assertEqual((1,), project.scans[0].page_nos)
        self.assertEqual((8,), project.scans[4].page_nos)

    def testSheetOrdering(self):
        
        project = Project()
        project.change_scan_profile(SCAN_PROFILE_DOUBLE_PAGES_FEEDER)
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        project.add_scan(self.create_double_page_scan())
        
        self.assertEqual(6, len(project.scans))
        self.assertEqual((12,1), project.scans[0].page_nos)
        self.assertEqual((2,11), project.scans[1].page_nos)
        self.assertEqual((10,3), project.scans[2].page_nos)
        self.assertEqual((4,9), project.scans[3].page_nos)
        self.assertEqual((8,5), project.scans[4].page_nos)
        self.assertEqual((6,7), project.scans[5].page_nos)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()