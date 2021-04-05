'''
Created on 13.03.2021

@author: michael
'''
from PIL import Image
import layoutparser
import numpy

from Asb.ScanConverter.ImageTypeConversion import pil_to_native_cv2image
from layoutparser.models.catalog import MODEL_CATALOG, CONFIG_CATALOG


class IllustrationMetaImage:
    
    def __init__(self, img: Image, photo_coordinates, drawing_coordinates):
        
        self.img = img
        self.photo_coordinates = photo_coordinates
        self.drawing_coordinates = drawing_coordinates
        
    def number_of_illustrations(self):
        
        return len(self.photo_coordinates) + len(self.drawing_coordinates)

    def get_illustration_mask(self):
        
        mask = numpy.zeros((self.img.height, self.img.width), dtype=bool)
        for coordinate in self.photo_coordinates + self.drawing_coordinates:
            mask[coordinate['y1']:coordinate['y2'], coordinate['x1']:coordinate['x2']] = True
        
        return Image.fromarray(mask)

    def get_text_mask(self):
        
        mask = numpy.ones((self.img.height, self.img.width), dtype=bool)
        for coordinate in self.photo_coordinates + self.drawing_coordinates:
            mask[coordinate['y1']:coordinate['y2'], coordinate['x1']:coordinate['x2']] = False
        
        return Image.fromarray(mask)

    def get_photos(self):
        
        return self._get_illustrations(self.photo_coordinates)
    
    def get_drawings(self):
        
        return self._get_illustrations(self.drawing_coordinates)
    
    def get_all_illustrations(self):
        
        return self._get_illustrations(self.photo_coordinates + self.drawing_coordinates)

    def _get_illustrations(self, coordinates):
        
        illustrations = []
        for c in coordinates:
            illustrations.append((c['x1'], c['y1'], self.img.crop((c['x1'], c['y1'], c['x2'], c['y2']))))
        return illustrations

    def get_img_without_illustrations(self):
        
        img_copy = self.img.copy()
        img_copy.paste(255, mask=self.get_illustration_mask())
        return img_copy

    def get_img_without_text(self):
        
        img_copy = self.img.copy()
        img_copy.paste(255, mask=self.get_text_mask())
        return img_copy

class Detectron2ImageDetectionService(object):
    
    DRAWING = "drawing"
    PHOTO = "photo"
    
    labels = {'PrimaLayout': {1:"TextRegion", 2:"ImageRegion", 3:"TableRegion", 4:"MathsRegion", 5:"SeparatorRegion", 6:"OtherRegion"},
              'PubLayNet': {0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
              'NewspaperNavigator': {0: "Photograph", 1: "Illustration", 2: "Map", 3: "Comics/Cartoon", 4: "Editorial Cartoon", 5: "Headline", 6: "Advertisement"},
              'HJDataset': {1:"Page Frame", 2:"Row", 3:"Title Region", 4:"Text Region", 5:"Title", 6:"Subtitle", 7:"Other"}
              }

    def __init__(self, training_set="PubLayNet", model='faster_rcnn_R_50_FPN_3x'):

        self.training_set = training_set
        self.config_path =  CONFIG_CATALOG[training_set][model]
        self.image_labels = ('ImageRegion', 'Figure', 'Photograph', 'Illustration', 'Map', 'Comics/Cartoon', 'Editorial Cartoon', 'Other')
        self.score_threshold = 0.7
        self.counter = 0
        
    def get_illustration_meta_image(self, img):

        cv2_image = pil_to_native_cv2image(img.convert("RGB"))
        model = layoutparser.Detectron2LayoutModel(
            config_path = self.config_path, # In model catalog
            label_map   = self.labels[self.training_set], # In model`label_map`
            #extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8] # Optional
        )
        layout = model.detect(cv2_image)
        photo_coordinates = []
        drawing_coordinates = []
        for element in layout:
            if element.type in self.image_labels and element.score > self.score_threshold:
                coordinate = {'x1': int(element.block.x_1),
                              'y1': int(element.block.y_1),
                              'x2': int(element.block.x_2) + 1,
                              'y2': int(element.block.y_2) + 1}
                if self.detectType(cv2_image[int(element.block.y_1):int(element.block.y_2),
                                             int(element.block.x_1):int(element.block.x_2)]) == self.PHOTO:
                    photo_coordinates.append(coordinate)
                else:
                    drawing_coordinates.append(coordinate)
            
        return IllustrationMetaImage(img, photo_coordinates, drawing_coordinates)
        
    def detectType(self, ndarray):
        
        histogram = numpy.histogram(ndarray, bins=3)
        #print(histogram)
        if histogram[0][1] == 0:
            return self.DRAWING
        ratio =  (histogram[0][0] + histogram[0][2]) / histogram[0][1]
        if ratio > 10:
            return self.DRAWING
        else:
            return self.PHOTO 
