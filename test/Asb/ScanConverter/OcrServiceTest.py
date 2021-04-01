'''
Created on 27.03.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Services import OCRService, ImageFileOperations
from PIL import Image
import os
from Asb.ScanConverter.Scoring import OCRScorer
import numpy



class OCRServiceTest(unittest.TestCase):



    def setUp(self):
        
        self.ocr_service = OCRService(ImageFileOperations())
        self.scorer = OCRScorer()

    test_list = [
            {"imagefile": "Test-Grüne-000.ppm",
             "textfile": "Test-Grüne-000.txt",
             "score": 0.98
            },
            {"imagefile": "B_Rep_057-01_00297_0005.jpg",
             "textfile": "B_Rep_057-01_00297_0005.txt",
             "score": 0.43
             },
            {"imagefile": "B_Rep_057-01_00590_0014.tif",
             "textfile": "B_Rep_057-01_00590_0014.txt",
             "score": 0.93
            },
        ]

    def testErosion(self):
        
        textfile_name = os.path.join("Images", self.test_list[2]["textfile"])
        textfile = open(textfile_name, mode='r')
        expected = textfile.read()
        textfile.close()
        img = Image.open(os.path.join("Images", self.test_list[2]["imagefile"]))

        for x in range(1,6):
            for y in range(1,6):
                self.ocr_service.image_file_operations.erosion_kernel = numpy.ones((x, y), 'uint8')

                computed = self.ocr_service.extract_text(img)
                score = self.scorer.scoreResults(expected, computed)
                print("X: %d. Y: %d. Score: %s" % (x, y, score))
    
    def notestOCR(self):
        
        for params in self.test_list:
            textfile_name = os.path.join("Images", params["textfile"])
            with self.subTest():
                if os.path.exists(textfile_name):
                    textfile = open(textfile_name, mode='r')
                    expected = textfile.read()
                    textfile.close()
                else:
                    expected = "Empty"

                img = Image.open(os.path.join("Images", params["imagefile"]))
                computed = self.ocr_service.extract_text(img)
                if not os.path.exists(textfile_name):
                    textfile = open(textfile_name,mode='w')
                    textfile.write(computed)
                    textfile.close()
        
                score = self.scorer.scoreResults(expected, computed)
                print(score)
                self.assertTrue(score.score_value > params["score"], 
                            "Sorry, score for %s is only %f, should be more than %f." % 
                            (params["imagefile"], score.score_value, params["score"]))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()