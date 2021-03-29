'''
Created on 13.03.2021

@author: michael
'''
from PIL import Image
import unittest
import numpy
import os.path
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
from Asb.ScanConverter.Services import ImageFileOperations


class ImageDetectionTest(unittest.TestCase):

    def setUp(self):
        
        self.image_file_operations = ImageFileOperations()
        self.img = (Image.open(os.path.join("Images", "Image1.png")), Image.open(os.path.join("Images", "Image2.png")))
        self.correct_mask = (numpy.zeros((self.img[0].height, self.img[0].width), dtype=bool),
                             numpy.zeros((self.img[1].height, self.img[1].width), dtype=bool))
        self.correct_mask[0][1560:2885, 1274:2295] = True
        self.correct_mask[0][922:1680, 475:925] = True
        self.correct_mask[1][348:1032, 1376:2408] = True
        self.correct_mask[1][1868:2472, 1368:2404] = True

    def notestVerifyMasks(self):

        for i in range(0, len(self.img)):
            bw_img = self.image_file_operations.binarization_sauvola(self.img[i])
            image = numpy.array(bw_img, dtype=numpy.bool)
            image[self.correct_mask[i]] = 1
            Image.fromarray(image).save("masked%d.png" % i)

    def testDetectron2ImageDetection(self):

        for image in range(0, len(self.img)):
            # for model in ('PubLayNet3',):
            for model in (Detectron2ImageDetectionService.models.keys()):
                service = Detectron2ImageDetectionService(model=model)
                masks_by_type = service.getImageMasks(self.img[image])
                f_score = self.calculate_fscore(image, masks_by_type)
                print("F-Score for image %d and model %s: %f" % (image, model, f_score))

    def calculate_fscore(self, image, masks_by_type):

        bw_img = self.image_file_operations.binarization_sauvola(self.img[image])
        
        # Wir entfernen alles ausser den Bildern und wenden
        # dann die berechneten Masken an. Was dann noch übrig
        # bleibt sind die nicht gefundenen pixel, d.h. die
        # false negatives
        
        image_without_text = numpy.array(bw_img, dtype=numpy.bool)
        image_without_text[numpy.invert(self.correct_mask[image])] = 1
        histogram = numpy.histogram(image_without_text, bins=2)
        all_positives = histogram[0][0]
        for type_array in masks_by_type:
            for mask in type_array:
                image_without_text[mask] = 1
        histogram = numpy.histogram(image_without_text, bins=2)
        false_negatives = histogram[0][0]
        found_positives = all_positives - false_negatives
        recall = found_positives / all_positives
        
        # Wir entfernen die Bilder, und berechnen die Pixel,
        # die dann noch stehen bleiben. Danach wenden wir die
        # Masken an und berechnen, wie viele Pixel zusätzlich
        # entfernt wurden, das sind die false_positives 
        
        image_without_pictures = numpy.array(bw_img, dtype=numpy.bool)
        image_without_pictures[self.correct_mask[image]] = 1
        histogram = numpy.histogram(image_without_pictures, bins=2)
        pixels_remaining = histogram[0][0]
        for type_array in masks_by_type:
            for mask in type_array:
                image_without_pictures[mask] = 1
        histogram = numpy.histogram(image_without_pictures, bins=2)
        false_positives = pixels_remaining - histogram[0][0]
        precision = found_positives / (found_positives + false_positives)
        f_score = 2 * (precision * recall / (precision + recall))
        return f_score


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testGrayMask']
    unittest.main()
