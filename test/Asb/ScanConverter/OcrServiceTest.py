'''
Created on 27.03.2021

@author: michael
'''
import os
import unittest

from PIL import Image

from Asb.ScanConverter.Ocr.OCR import OcrRunner, OcrPreprocessor,\
    OcrPostprocessor
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Ocr.Scoring import OCRScorer


class OCRServiceTest(unittest.TestCase):



    def setUp(self):
        
        self.postprocessor = OcrPostprocessor()
        self.ocr_service = OcrRunner(OcrPreprocessor(ImageFileOperations()), self.postprocessor)
        self.scorer = OCRScorer()

    test_list = [
            {"imagefile": "Test-Grüne-000.ppm",
             "textfile": "Test-Grüne-000.txt",
             "score": 0.98
            },
            {"imagefile": "B_Rep_057-01_00297_0005.jpg",
             "textfile": "B_Rep_057-01_00297_0005.txt",
             "score": 0.28
             },
            {"imagefile": "B_Rep_057-01_00590_0014.tif",
             "textfile": "B_Rep_057-01_00590_0014.txt",
             "score": 0.65
            },
            {"imagefile": "RoterStern2.jpg",
             "textfile": "RoterStern2.txt",
             "score": 0.48
            },
        ]

    def test_remove_hyphenation(self):
        
        input = """Immer im Win-
        ter, wenn es schneit, kom-
        men - wenn niemand es sieht -
        Gnome aus dem Wald."""
        
        expected = """Immer im Winter, wenn es schneit, kommen - wenn niemand es sieht -
        Gnome aus dem Wald."""

        self.assertEqual(self.postprocessor.remove_hyphenation(input), expected)

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
                computed = self.ocr_service.get_text(img)
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