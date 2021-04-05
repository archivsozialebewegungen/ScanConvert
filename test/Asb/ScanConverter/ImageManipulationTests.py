'''
Created on 04.04.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.ImageOperations import ImageFileOperations
import os
import tempfile
from Asb.ScanConverter.ImageTypeConversion import pil_to_ndarray
import numpy
from Asb.ScanConverter.DeveloperTools import DeveloperTools


class ImageManipulationTest(unittest.TestCase):


    def setUp(self):
        
        self.ops = ImageFileOperations()
        self.dev_tools = DeveloperTools()
        # This is a color, 600 dpi image
        self.color = self.ops.load_image(os.path.join("Images", "RoterStern2.jpg"))
        self.gray = self.ops.load_image(os.path.join("Images", "Image1.png"))
        self.images = (self.color, self.gray)

    def testManipulations(self):
        
        for op in (self.ops.enhance_contrast, 
                   self.ops.apply_dilation, 
                   self.ops.apply_erosion,
                   self.ops.binarization_fixed,
                   self.ops.binarization_floyd_steinberg,
                   self.ops.binarization_otsu,
                   self.ops.binarization_sauvola,
                   self.ops.convert_to_gray):
            for img in self.images:
                with self.subTest():
                    manipulated = op(img)
                    self.dev_tools.show_image(manipulated, title="%s" % op.__name__)

    def testSaveTif(self):
        '''
        Test that images are identical
        '''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "output.tif")
            self.ops.save_image(self.color, filename)
            loaded = self.ops.load_image(filename)
            self.assertEqual((600, 600), self.ops.get_resolution(loaded))
            original = pil_to_ndarray(self.color)
            copy = pil_to_ndarray(loaded)
            self.assertTrue(numpy.array_equal(original, copy))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()