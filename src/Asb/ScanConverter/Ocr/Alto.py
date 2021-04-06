'''
Created on 05.04.2021

@author: michael
'''
from xml.dom.minidom import parseString, Element
import pytesseract
import numpy
from PIL import Image
import re

class ElementWrapper:
    
    def get_bounding_box(self):
        
        x1 = int(self.element.getAttribute("HPOS"))
        y1 = int(self.element.getAttribute("VPOS"))
        x2 = x1 + self.get_width()
        y2 = y1 + self.get_height()
        return x1, y1, x2, y2
    
    def get_width(self):
        
        return int(self.element.getAttribute("WIDTH"))

    def get_height(self):
        
        return int(self.element.getAttribute("HEIGHT"))
    

class LineObject(ElementWrapper):
    
    def __init__(self, lineElement: Element):
        
        self.element = lineElement
        
    def get_strings(self):
        
        elements = []
        for string_element in self.element.getElementsByTagName("String"):
            elements.append(StringObject(string_element))
            
        return elements

class StringObject(ElementWrapper):
    '''
    Helper class for string representations in the AltoPageLayout class.
    '''
    
    dotted_characters = {'i': 2, 'ä': 3, 'ö': 3, 'ü': 3, 'Ä': 3, 'Ö': 3, 'Ü': 3, '.': 1, '!': 2, ':': 2, ';': 2}

    def __init__(self, stringElement: Element):
        
        self.element = stringElement
    
    def is_string_with_dots(self):
        
        # Avoid strings with accented characters etc.
        empty_string = re.sub("[a-zA-ZäöüÄÖÜ.!:;]*", '', self.get_text())
        if len(empty_string) != 0:
            return False
        without_dotted = re.sub("[iäöüÄÖÜ.!:;]", '', self.get_text())
        if self.get_text() != without_dotted:
            return True
        return False
    
    def get_number_of_shapes(self):
        
        shapes = 0
        for character in self.get_text():
            if character in self.dotted_characters:
                shapes += self.dotted_characters[character]
            else:
                shapes += 1
        return shapes
        
    def get_text(self):
        
        return self.element.getAttribute("CONTENT")
    
class AltoPageLayout:
    '''
    This is a class to get information about an image using OCR.
    '''
    
    def __init__(self, img, language: str='deu'):

        self.img = img
        self.dom = parseString(pytesseract.image_to_alto_xml(img,lang=language).decode('utf-8'))
    
    def write_to_file(self, filename):

        file = open(filename, "w")
        self.dom.writexml(file, indent="   ")
        file.close()
    
    def get_all_strings(self) -> [StringObject]:

        strings = []
        for string in self.dom.getElementsByTagName("String"):
            strings.append(StringObject(string))
        return strings
        
    def get_all_lines(self) -> [LineObject]:

        lines = []
        for line in self.dom.getElementsByTagName("TextLine"):
            lines.append(LineObject(line))
        return lines

    def get_big_text_block_coordinates(self):
        
        block = self.get_big_text_block()
        x1 = int(block.getAttribute("HPOS"))
        y1 = int(block.getAttribute("VPOS"))
        x2 = x1 + int(block.getAttribute("WIDTH"))
        y2 = y1 + int(block.getAttribute("HEIGHT"))
        
        return x1, y1, x2, y2
    
    def get_median_text_height(self):
        
        heights = []
        for string in self.dom.getElementsByTagName("String"):
            heights.append(int(string.getAttribute("HEIGHT")))
        return numpy.median(heights)
        
    def get_layout(self):
        
        return self.dom.gmittelwertetElementsByTagName("Layout")[0]
    
    def get_first_page(self):
        
        return self.dom.getElementsByTagName("Page")[0]

    def get_big_text_block(self) -> Element:

        for i in range(0,10):
            for element in self.dom.getElementsByTagName("TextBlock"):
                width = int(element.getAttributeNode("WIDTH").value)
                height = int(element.getAttributeNode("HEIGHT").value)
                if width * height > 10000 * (10-i):
                    return element
        # Safety
        return self.dom.getElementsByTagName("TextBlock")[0]
    
    def get_text_mask(self):
        
        mask = numpy.ones((self.img.height, self.img.width), dtype=bool)
        for string in self.get_all_strings():
            x1, y1, x2, y2 = string.get_bounding_box()
            mask[y1:y2, x1:x2] = False
        return Image.fromarray(mask) 
