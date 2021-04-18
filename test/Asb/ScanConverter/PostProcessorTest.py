'''
Created on 17.04.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Ocr.OCR import OcrPostprocessor


class PostProcessorTest(unittest.TestCase):


    def setUp(self):
        
        self.post_processor = OcrPostprocessor()


    def tearDown(self):
        pass

    def testPreprocessText(self):

        text = """Dies-ist ein, mit  
        Satzzeichen gespickter Text!
        """
        
        self.assertEqual('Dies - ist ein , mit Satzzeichen gespickter Text ! ',
                         self.post_processor.preprocess_text(text))
        
        
        
    def testSpellcheckerFix(self):
        
        text = "Meine Oma fährt im Huhnerstall Motorrad."
        
        self.assertEquals("Meine Oma fährt im Hühnerstall Motorrad.",
                          self.post_processor.fix_word_via_spellchecker_and_bert(text))
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()