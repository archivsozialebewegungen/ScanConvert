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
        
    def testSentenceSplit(self):

        text = """Kurzer Satz. Noch ein Satz...
        Das kostet 3.45€.
        """
        sentences = self.post_processor.split_into_sentences(text)
        self.assertEqual(3, len(sentences))
        self.assertEqual("Kurzer Satz.", sentences[0])
        self.assertEqual("Noch ein Satz...", sentences[1])
        self.assertEqual("Das kostet 3.45€.", sentences[2])
        
        
    def testSpellcheckerFix(self):
        
        text = "Meine Oma fährt im Huhnerstall Motorrad."
        
        result = self.post_processor.fix_word_via_spellchecker_and_bert(text)
        self.assertEquals("Meine Oma fährt im Hühnerstall Motorrad.",
                          result)
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()