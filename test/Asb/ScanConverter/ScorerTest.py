'''
Created on 27.03.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Scoring import OCRScorer


class ScorerTest(unittest.TestCase):


    def testScorer(self):
        
        expected = "Dies ist ein Text, der auch auch Kommata und Ümlaute enthält"
        computed = "Dles ist ein Text, der auch Konnnata und Ümlaufe enthält"
        scorer = OCRScorer()
        self.assertEqual(7/11, scorer.scoreResults(expected, computed))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()