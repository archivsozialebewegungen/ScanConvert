'''
Created on 13.03.2021

@author: michael
'''
from PIL import Image
import unittest
import numpy
from Asb.ScanConverter.ImageDetection import OcropuyImageDetectionService
from Asb.ScanConverter.Services import FormatConversionService


class ImageDetectionTest(unittest.TestCase):


    def testGrayMask(self):
        
        img = Image.open("Image1.png")
        service = OcropuyImageDetectionService(FormatConversionService())
        (mask1, mask2) = service.getImageMask(img)
        mask1_img = Image.fromarray(mask1, "1")
        mask1_img.save("Image1mask1.png")
        mask2_img = Image.fromarray(mask2, "1")
        mask2_img.save("Image1mask2.png")
        ndarray = numpy.array(img, dtype=numpy.uint8)
        ndarray[mask1] = 0
        cut_image = Image.fromarray(ndarray, "L")
        cut_image.save("Image1cut1.png")
        ndarray = numpy.array(img, dtype=numpy.uint8)
        ndarray[mask2] = 0
        cut_image = Image.fromarray(ndarray, "L")
        cut_image.save("Image1cut2.png")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGrayMask']
    unittest.main()