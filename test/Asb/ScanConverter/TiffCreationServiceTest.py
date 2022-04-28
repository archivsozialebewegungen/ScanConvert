'''
Created on 26.04.2022

@author: michael
'''
import unittest
from os import path
from Asb.ScanConverter.ScanService import Project, ScanTransformationService,\
    SCAN_PROFILE_SINGLE_PAGES, OUTPUT_PROFILE_NO_MODE_CHANGE_400_DPI,\
    TiffCreationService
from Asb.ScanConverter.ImageOperations import ImageFileOperations


class TiffCreationServiceTest(unittest.TestCase):

    def setUp(self):
        
        img_dir = path.join(path.dirname(__file__), 'Images')
        
        self.file1 = path.join(img_dir, 'Image1.png')
        self.file2 = path.join(img_dir, 'Image2.png')
        
        self.img_ops = ImageFileOperations()
        self.scan_transformation_service = ScanTransformationService(self.img_ops)
        self.tiff_creation_service = TiffCreationService(self.img_ops, self.scan_transformation_service)
 
    def testSinglePages(self):
        
        project = Project()
        project.add_scan(self.scan_transformation_service.load_scan(self.file1))
        project.add_scan(self.scan_transformation_service.load_scan(self.file2))
        project.change_scan_profile(SCAN_PROFILE_SINGLE_PAGES)
        project.change_output_profile(OUTPUT_PROFILE_NO_MODE_CHANGE_400_DPI)
        self.tiff_creation_service.create_tifs(project, "/tmp/single_test")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()