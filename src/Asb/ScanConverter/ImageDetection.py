'''
Created on 13.03.2021

@author: michael
'''
from PIL import Image
import numpy
import layoutparser
from Asb.ScanConverter.ImageOperations import pil_to_cv2image
       
class Detectron2ImageDetectionService(object):
    
    DRAWING = "drawing"
    PHOTO = "photo"
    
    models = {'Prima': {'config': 'lp://PrimaLayout/mask_rcnn_R_50_FPN_3x/config',
                        'label_map': {1:"TextRegion", 2:"ImageRegion", 3:"TableRegion", 4:"MathsRegion", 5:"SeparatorRegion", 6:"OtherRegion"},
                        'image_labels': ('ImageRegion',) 
                        },
              'PubLayNet1': {'config': 'lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                             'label_map': {0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
                             'image_labels': ('Figure',)},
              'PubLayNet2': {'config': 'lp://PubLayNet/mask_rcnn_R_50_FPN_3x/config',
                             'label_map': {0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
                             'image_labels': ('Figure',)},
              'PubLayNet3': {'config': 'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
                             'label_map': {0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
                             'image_labels': ('Figure',)},
              'NewspaperNavigator': {'config': 'lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config',
                             'label_map': {0: "Photograph", 1: "Illustration", 2: "Map", 3: "Comics/Cartoon", 4: "Editorial Cartoon", 5: "Headline", 6: "Advertisement"},
                             'image_labels': ('Photograph', 'Illustration', 'Map', 'Comics/Cartoon')}
            }

    def __init__(self, model='PubLayNet3'):

        self.config_path =  self.models[model]['config']
        self.label_map = self.models[model]['label_map']
        self.image_labels = self.models[model]['image_labels']
        self.score_threshold = 0.7
        self.counter = 0
        
    def getImageMasks(self, img: Image):

        cv2_image = pil_to_cv2image(img)
        model = layoutparser.Detectron2LayoutModel(
            config_path = self.config_path, # In model catalog
            label_map   = self.label_map, # In model`label_map`
            #extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8] # Optional
        )
        layout = model.detect(cv2_image)
        photos = []
        drawings = []
        for element in layout:
            if element.type in self.image_labels and element.score > self.score_threshold:
                mask = numpy.zeros((img.height,img.width), dtype=bool)
                mask[int(element.block.y_1):int(element.block.y_2), int(element.block.x_1):int(element.block.x_2)] = True
                if self.detectType(cv2_image[int(element.block.y_1):int(element.block.y_2),
                                             int(element.block.x_1):int(element.block.x_2)]) == self.PHOTO:
                    photos.append(mask)
                else:
                    drawings.append(mask)
            
        return (photos, drawings)
    
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
