'''
Created on 27.03.2021

@author: michael
'''
import re


class ScoreResult:
    
    def __init__(self):
        
        self.found = {}
        self.not_found = {}
        self.false_found = {}
    
    def __str__(self):
        
        display = "Score is %f" % self.score_value
        for word in self.found.keys():
            display += "\nFound: %s (%d times)" % (word, self.found[word])
        for word in self.not_found.keys():
            display += "\nNot found: %s (%d times missing)" % (word, self.not_found[word])
        for word in self.false_found.keys():
            display += "\nFound instead: %s (%d times)" % (word, self.false_found[word])
        return display

    def _get_score_value(self):
        
        sum_not_found = 0
        for word in self.not_found:
            sum_not_found += self.not_found[word]
        sum_found = 0
        for word in self.found:
            sum_found += self.found[word]
        
        return sum_found / (sum_found + sum_not_found)
        
    score_value = property(_get_score_value)
    
class OCRScorer:
    
    def scoreResults(self, expected, computed):
        
        expected_word_list = self._create_word_list(expected)
        computed_word_list = self._create_word_list(computed)
        
        found = 0
        expected = 0
        score = ScoreResult()
        for word in expected_word_list.keys():
            expected += expected_word_list[word]
            if word in computed_word_list:
                if computed_word_list[word] > expected_word_list[word]:
                    print("Found more instances (%d instead of %d) of »%s« than expected!" % (computed_word_list[word],
                                                                                            expected_word_list[word],
                                                                                            word))
                if computed_word_list[word] < expected_word_list[word]:
                    score.not_found[word] = expected_word_list[word] - computed_word_list[word]
                    score.found[word] = computed_word_list[word]
                else:
                    score.found[word] = computed_word_list[word] 
            else:
                score.not_found[word] = expected_word_list[word]

        for word in computed_word_list.keys():
            if word in expected_word_list:
                if computed_word_list[word] > expected_word_list[word]:
                    score.false_found[word] = computed_word_list[word] - expected_word_list[word]
            else:
                score.false_found[word] = computed_word_list[word]

        return score
        
    def _create_word_list(self, text):
        
        list = {}
        for word in re.split('\W+', text):
            if len(word) == 0:
                continue
            if word in list:
                list[word] += 1
            else:
                list[word] = 1
        return list
        
        
        