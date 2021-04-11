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
from Asb.ScanConverter.Ocr.GoogleVision import GoogleVisionApiJsonReader
from Asb.ScanConverter.DeveloperTools import DeveloperTools
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
from Asb.ScanConverter.ImageStatistics import ImageStatistics


class OCRServiceTest(unittest.TestCase):



    def setUp(self):
        
        self.dev_tools = DeveloperTools()
        self.img_statistics = ImageStatistics()
        self.postprocessor = OcrPostprocessor()
        self.ocr_service = OcrRunner(OcrPreprocessor(ImageFileOperations(), self.img_statistics), self.postprocessor)
        self.scorer = OCRScorer()

    test_list = [
            {"imagefile": "Test-Grüne-000.jpg",
             "score": 0.98
            },
            {"imagefile": "B_Rep_057-01_00297_0005.jpg",
             "score": 0.28
             },
            {"imagefile": "B_Rep_057-01_00590_0014.tif",
             # Kann mit Sharpen filter auf 0.95 angehoben werden
             "score": 0.90
            },
            {"imagefile": "RoterStern2.jpg",
             # Kann mit Sharpen filter auf 0.51 angehoben werden
             "score": 0.48
            },
        ]

    def notest_remove_hyphenation(self):
        
        input = """Immer im Win-
        ter, wenn es schneit, kom-
        men - wenn niemand es sieht -
        Gnome aus dem Wald."""
        
        expected = """Immer im Winter, wenn es schneit, kommen - wenn niemand es sieht -
        Gnome aus dem Wald."""

        self.assertEqual(self.postprocessor.remove_hyphenation(input), expected)

    def testOCR(self):
        
        for params in self.test_list:
            print("Processing " + params["imagefile"])
            textfile_name = os.path.join("Images", "Results", params["imagefile"][:-4] + ".txt")
            google_vision_name = os.path.join("Images", "Results", params["imagefile"][:-4] + ".json")
            with self.subTest():
                if os.path.exists(textfile_name):
                    textfile = open(textfile_name, mode='r')
                    expected = textfile.read()
                    textfile.close()
                else:
                    expected = "Empty"
                    
                if os.path.exists(google_vision_name):
                    json_reader = GoogleVisionApiJsonReader(google_vision_name)
                else:
                    json_reader = None

                img = Image.open(os.path.join("Images", params["imagefile"]))

                if self.img_statistics.advice_more_contrast(img):
                    print("Image needs more contrast")
                else:
                    print("Image needs not more contrast")
                if self.img_statistics.advice_sharpening(img):
                    print("Sharpening may help")
                else:
                    print("Sharpening will not help")
                    
                self.dev_tools.print_statistics(img)
                computed = self.ocr_service.get_text(img)
                if not os.path.exists(textfile_name):
                    textfile = open(textfile_name,mode='w')
                    textfile.write(computed)
                    textfile.close()
        
                score = self.scorer.scoreResults(expected, computed)
                print(score)
                if os.path.exists(google_vision_name):
                    json_reader = GoogleVisionApiJsonReader(google_vision_name)
                    google_score = self.scorer.scoreResults(expected, json_reader.get_text())
                    print("Google vision score: %s" % google_score)

                alto_layout = AltoPageLayout(img)
                print("Tesseract confidentiality: %f" % alto_layout._get_confidence())

                self.assertTrue(score.score_value > params["score"], 
                            "Sorry, score for %s is only %f, should be more than %f." % 
                            (params["imagefile"], score.score_value, params["score"]))
            
            print("==================")
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()