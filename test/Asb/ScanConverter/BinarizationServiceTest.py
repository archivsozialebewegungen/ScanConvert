'''
Created on 20.03.2021

@author: michael
'''
import unittest
from PIL import Image
from Asb.ScanConverter.Services import FormatConversionService, JobDefinition
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
import os
from Asb.ScanConverter.ImageOperations import ImageFileOperations


class BinarizationServiceTest(unittest.TestCase):


    def testMixedBinarization(self):
        
        service = FormatConversionService(Detectron2ImageDetectionService(), ImageFileOperations())
        job_definition = JobDefinition()
        job_definition.denoise = True
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            bin_image = service._binarization_mixed(img, job_definition)
            bin_image.save(os.path.join("/tmp", "Image%d.bin.png" % i))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()