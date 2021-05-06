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

    def testRemoveHyphenation(self):

        text = """Frau Müller-
        Eisele, die mitt-
        wochs ins Büro kommt. 3 -
        1 = 2"""
        
        self.assertEqual('Frau Müller-Eisele, die mittwochs ins Büro kommt. 3 - 1 = 2',
                         self.post_processor.postprocess(text))
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()