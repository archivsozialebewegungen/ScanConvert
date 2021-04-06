'''
Created on 27.03.2021

@author: michael
'''
import unittest
from Asb.ScanConverter.Ocr.Scoring import OCRScorer


class ScorerTest(unittest.TestCase):


    def testScorer(self):
        
        expected = "Dies ist ein Text, der auch auch Kommata und Ümlaute enthält"
        computed = "Dles ist ein Text, der auch Konnnata und Ümlaufe enthält"
        scorer = OCRScorer()
        score = scorer.scoreResults(expected, computed)
        self.assertEqual(4, len(score.not_found_words))
        self.assertEqual(7, len(score.found_words))
        self.assertEqual(3, len(score.false_found_words))
        
        sum_not_found = len("Dies") + len("auch") + len("Kommata") + len("Ümlaute") 
        sum_found = len("ist") + len("ein") + len("Text") + len("der") + len("auch") + len("und") + len("enthält") 
        
        self.assertEqual(sum_found / (sum_found + sum_not_found), score.score_value)
        self.assertEqual("Score is 0.551020. Words found: 7. Words not found: 4.", "%s" % score)
        score.verbose = True
        self.assertEqual("""Score is 0.551020
Found: ist (1 times)
Found: ein (1 times)
Found: Text (1 times)
Found: der (1 times)
Found: auch (1 times)
Found: und (1 times)
Found: enthält (1 times)
Not found: Dies (1 times missing)
Not found: auch (1 times missing)
Not found: Kommata (1 times missing)
Not found: Ümlaute (1 times missing)
Found instead: Dles (1 times)
Found instead: Konnnata (1 times)
Found instead: Ümlaufe (1 times)""", "%s" % score)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()