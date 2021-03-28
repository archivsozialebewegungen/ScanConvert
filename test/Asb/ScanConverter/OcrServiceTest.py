'''
Created on 27.03.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Services import OCRService, ImageFileOperations
from PIL import Image
import os
from Asb.ScanConverter.Scoring import OCRScorer



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
             "score": 0.42
             },
            {"imagefile": "B_Rep_057-01_00590_0014.tif",
             "textfile": "B_Rep_057-01_00590_0014.txt",
             "score": 0.93
            },
        ]
    
    def testOCR(self):
        
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