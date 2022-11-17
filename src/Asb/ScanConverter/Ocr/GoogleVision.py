'''
Created on 09.04.2021

@author: michael
'''
import json

class GoogleVisionApiJsonReader:
    
    def __init__(self, file_path):
        
        with open(file_path) as json_file:
            self.data = json.load(json_file)
            
    def get_text(self):
        
        text = ""
        separator = ""
        for annotation in self.data["textAnnotations"]:
            text += separator + annotation['description']
            separator = " "
        return text