'''
Created on 20.03.2021

@author: michael
'''
import unittest
from PIL import Image
from Asb.ScanConverter.Services import FormatConversionService, JobDefinition
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
import os
from Asb.ScanConverter.ImageOperations import ImageFileOperations,\
    AltoPageLayout
from Asb.ScanConverter.DeveloperTools import DeveloperTools


class IllustrationTextHandlingTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.image_operations = ImageFileOperations()
        self.developer_tools = DeveloperTools()
        self.illustration_detection_service = Detectron2ImageDetectionService()

    def testMixedBinarization(self):
        
        service = FormatConversionService(self.illustration_detection_service, ImageFileOperations())
        job_definition = JobDefinition()
        job_definition.denoise = True
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            bin_image = service._binarization_mixed(img, job_definition)
            self.developer_tools.show_image(bin_image, title="Mixed binarization")

    def testRemoveIllustrations(self):
        
        service = Detectron2ImageDetectionService()
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            meta_img = service.get_illustration_meta_image(img)
            self.developer_tools.show_image(meta_img.get_img_without_illustrations(), title="No illustrations")

    def testRemoveText(self):
        
        service = Detectron2ImageDetectionService()
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            meta_img = service.get_illustration_meta_image(img)
            self.developer_tools.show_image(meta_img.get_img_without_text(), title="No text")

    def testBinarizeTextOnly(self):
        
        service = Detectron2ImageDetectionService()
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            meta_img = service.get_illustration_meta_image(img)
            bin_image = self.image_operations.binarization_sauvola(meta_img.get_img_without_illustrations())
            for (x1, y1, illu) in meta_img.get_all_illustrations():
                bin_image.paste(illu, (x1, y1))
            self.developer_tools.show_image(bin_image, title="Only text binarization")

    def test_mask_text(self):
        
        for i in range(1,3):
            img = Image.open(os.path.join("Images", "Image%d.png" % i))
            img = img.convert('L')
            layout = AltoPageLayout(img)
            mask = layout.get_text_mask()
            self.developer_tools.show_image(mask, title="Text mask")
            print("Image width: %d. Image height: %d" % (img.width, img.height))
            print("Mask width: %d. Mask height: %d" % (mask.width, mask.height))
            masked_img = img.copy()
            masked_img.paste(255, (0,0,img.width, img.height), mask=mask)
            print("Mode: %s" % masked_img.mode)
            masked_img = self.image_operations.binarization_sauvola(masked_img)
            self.developer_tools.show_image(masked_img, title="Masked text")
        
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()