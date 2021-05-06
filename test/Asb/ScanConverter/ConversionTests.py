'''
Created on 04.04.2021

@author: michael
'''
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.ImageTypeConversion import \
    pil_to_ndarray, ndarray_to_pil, \
    pil_to_native_cv2image, native_cv2image_to_pil, pil_to_rgb_cv2image, \
    rgb_cv2image_to_pil
from PIL import ImageChops
import os
import unittest

class ConversionTest(unittest.TestCase):


    def setUp(self):
        
        self.ops = ImageFileOperations()
        # This is a color, 600 dpi image
        self.color = self.ops.load_image(os.path.join("Images", "RoterStern2.jpg"))
        self.gray = self.ops.load_image(os.path.join("Images", "Image1.png"))
        self.bw = self.ops.binarization_sauvola(self.gray)
        
        self.images = ((self.color, 600), (self.gray, 300), (self.bw, 300))


    def testToNumpyAndBack(self):
        
        for img in self.images:
            with self.subTest():
                ndarray = pil_to_ndarray(img[0])
                copy = ndarray_to_pil(ndarray, (img[1], img[1]))
                diff = ImageChops.difference(img[0], copy)
                self.assertFalse(diff.getbbox())
                self.assertEqual((img[1], img[1]), self.ops.get_resolution(copy))
    
    def testToNativeCV2AndBack(self):
        
        for img in self.images:
            with self.subTest():
                cv2img = pil_to_native_cv2image(img[0])
                copy = native_cv2image_to_pil(cv2img, (img[1], img[1]))
                diff = ImageChops.difference(img[0], copy)
                self.assertFalse(diff.getbbox())
                self.assertEqual((img[1], img[1]), self.ops.get_resolution(copy))

    def testToRGBCV2AndBack(self):
        
        for img in self.images:
            with self.subTest():
                cv2img = pil_to_rgb_cv2image(img[0])
                copy = rgb_cv2image_to_pil(cv2img, (img[1], img[1]))
                diff = ImageChops.difference(img[0], copy)
                self.assertFalse(diff.getbbox())
        self.assertEqual((img[1], img[1]), self.ops.get_resolution(copy))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()