'''
Created on 20.03.2021

@author: michael
'''
import unittest
from PIL import Image
from Asb.ScanConverter.Services import FormatConversionService, JobDefinition
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService


class BinarizationServiceTest(unittest.TestCase):


    def testMixedBinarization(self):
        
        service = FormatConversionService(Detectron2ImageDetectionService())
        job_definition = JobDefinition()
        job_definition.denoise = True
        for i in range(1,3):
            img = Image.open("Image%d.png" % i)
            bin_image = service._binarization_mixed(img, job_definition)
            bin_image.save("Image%d.bin.png" % i)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()