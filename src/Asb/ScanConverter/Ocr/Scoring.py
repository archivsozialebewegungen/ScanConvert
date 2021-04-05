'''
Created on 27.03.2021

@author: michael
'''
import re


class ScoreResult:
    
    def __init__(self, verbose=False):
        
        self.found_words = {}
        self.not_found_words = {}
        self.false_found_words = {}
        self.verbose=verbose
    
    def __str__(self):
        
        display = "Score is %f" % self.score_value
        if self.verbose:
            for word in self.found.keys():
                display += "\nFound: %s (%d times)" % (word, self.found[word])
            for word in self.not_found.keys():
                display += "\nNot found: %s (%d times missing)" % (word, self.not_found[word])
            for word in self.false_found.keys():
                display += "\nFound instead: %s (%d times)" % (word, self.false_found[word])
        else:
            display += ". Words found: %d. Words not found: %d." % (len(self.found), len(self.not_found))
        return display

    def _get_score_value(self):
        
        sum_not_found = 0
        for word in self.not_found_words:
            sum_not_found += self.not_found_words[word] * len(word)
        sum_found = 0
        for word in self.found_words:
            sum_found += self.found_words[word] * len(word)
        return sum_found / (sum_found + sum_not_found)
        
    score_value = property(_get_score_value)
    
class OCRScorer:
    
    def scoreResults(self, expected, computed):
        
        expected_word_list = self._create_word_list(expected)
        computed_word_list = self._create_word_list(computed)
        
        score = ScoreResult()
        for word in expected_word_list.keys():
            if word in computed_word_list:
                if computed_word_list[word] < expected_word_list[word]:
                    # Not all occurences found
                    score.not_found_words[word] = expected_word_list[word] - computed_word_list[word]
                    score.found_words[word] = computed_word_list[word]
                elif computed_word_list[word] > expected_word_list[word]:
                    # More than the existing occurencies found
                    score.found_words = expected_word_list[word]
                    score.false_found_words = computed_word_list[word] - expected_word_list[word]
                else:
                    # Exactly found what was expected
                    score.found_words[word] = computed_word_list[word] 
            else:
                # None found
                score.not_found_words[word] = expected_word_list[word]

        for word in computed_word_list.keys():
            if word in expected_word_list:
                continue # Already processed in first loop
            else:
                score.false_found_words[word] = computed_word_list[word]

        return score
        
    def _create_word_list(self, text):
        
        wordlist = {}
        for word in re.split('\W+', text):
            if len(word) == 0:
                continue
            if word in wordlist:
                wordlist[word] += 1
            else:
                wordlist[word] = 1
        return wordlist
        
        
        