'''
Created on 16.02.2021

@author: michael
'''
from PIL import Image, ImageOps
import os
from injector import singleton, inject
from Asb.ScanConverter.ImageOperations import ImageFileOperations,\
    MissingResolutionInfo
from Asb.ScanConverter.Ocr.Denoiser import DenoiseService

Image.MAX_IMAGE_PIXELS = None

BLACK_AND_WHITE = "Schwarz-Weiß"
GRAYSCALE = "Graustufen"
COLOR = "Farbe"
COLOR_WITH_ALPHA = "Farbe mit Transparenz"
INDEX = "Indexiert"

FLOYD_STEINBERG = "Nur Bilder"
OTSU = "Text und Bilder"
THRESHOLD = "Schwellwert"
SAUVOLA = "Text optimal"

class GraphicFileInfo:
    
    modes = {"1": BLACK_AND_WHITE, "L": GRAYSCALE, "RGB": COLOR,
             "RGBA": COLOR_WITH_ALPHA, "P": INDEX}
    
    def __init__(self, filepath):
        
        self.filepath = filepath
        img = Image.open(filepath)
        self.format = type(img).__name__.replace('ImageFile', '')
        self.rawmode = img.mode
        self.width = img.width
        self.height = img.height
        self.info = img.info
        img.close()
    
    def update(self, img: Image):

        self.rawmode = img.mode
        self.width = img.width
        self.height = img.height
        
    def _get_resolution(self):
        
        if "dpi" in self.info:
            dpi = self.info['dpi']
            if dpi[0] == 1:
                return "Unbekannt"
            if dpi[0] == dpi[1]:
                return "%s" % dpi[0]
            else:
                return "%sx%s" % dpi
        return "Unbekannt"
    
    def _get_filename(self):
        
        return os.path.basename(self.filepath)
    
    def _get_mode(self):
        
        if self.rawmode in self.modes:
            return self.modes[self.rawmode]
        
        return "Unbekannt (%s)" % self.rawmode
    
    resolution = property(_get_resolution)
    filename = property(_get_filename)
    mode = property(_get_mode)

class ModeChangeDefinition:
    
    def __init__(self):
        self.modus_change = None
        self.binarization_algorithm = SAUVOLA
        self.threshold_value = 127
        
    def __eq__(self, other):
        
        return self.modus_change == other.modus_change and \
            self.binarization_algorithm == other.binarization_algorithm and \
            self.threshold_value == other.threshold_value

class JobDefinition:
    
    SORT_FIRST_PAGE = "first_page"
    SORT_SHEETS = "sort sheets"
    def __init__(self):

        self.mode_change_definitions = {}
        self.mode_change_definitions['default'] = ModeChangeDefinition()        
        self.task = None
        self.fileinfos = []
        self.resolution_change = None
        self.correct_res_only = False
        self.denoise = False
        self.output_path = None
        
        self.split = False
        self.sort = None
        
        self.rotation = 0
        self.last_rotation = None
        self.autorotation = False
        self.alternating_rotation = False

        self.pdfa = False
        
        self.ocr = False

@singleton
class FormatConversionService(object):
    '''
    classdocs
    '''
    
    alternations = {0: 180, 180: 0, 90: 270, 270:90}
    
    @inject
    def __init__(self, image_file_operations: ImageFileOperations,
                 denoiser: DenoiseService):
        
        self.image_file_operations = image_file_operations
        self.denoiser = denoiser

    def perform_changes(self, img: Image, fileinfo: GraphicFileInfo, jobDefinition: JobDefinition):
        
        #img = self.enhance_contrast(img)
        img, fileinfo = self.change_resolution(img, fileinfo, jobDefinition)
        img, fileinfo = self.change_mode(img, fileinfo, jobDefinition)
        img, fileinfo, jobDefinition = self.rotate(img, fileinfo, jobDefinition)
        return img, fileinfo, jobDefinition

    def load_image(self, fileinfo: GraphicFileInfo):
        
        return Image.open(fileinfo.filepath)
    
    def change_mode(self, img: Image, fileinfo: GraphicFileInfo, job_definition: JobDefinition):

        if fileinfo.filename in job_definition.mode_change_definitions:
            mode_change_definition = job_definition.mode_change_definitions[fileinfo.filename]
        else:
            mode_change_definition = job_definition.mode_change_definitions['default']
        
        if mode_change_definition.modus_change is None and not job_definition.denoise:
            return img, fileinfo
        
        if img.mode == BLACK_AND_WHITE:
            # The image is already BW, so no mode change may occur,
            # but perhaps we have to denoise
            if job_definition.denoise:
                return self.denoiser.denoise(img), fileinfo
            else:
                return img, fileinfo
        
        # If we reach this, mode is either color or gray
        
        if img.mode != GRAYSCALE:
            # The image is some color image, so mode change must be to
            # gray or bw, this means we need at least convert to gray
            img = ImageOps.grayscale(img)
            fileinfo.rawmode = "L"
        
        # We now definitely have a gray image
        
        if mode_change_definition.modus_change == BLACK_AND_WHITE:
            fileinfo.rawmode = "1"
            img = self.binarize(img, mode_change_definition)
            if job_definition.denoise:
                img = self.denoiser.denoise(img)
        
        return img, fileinfo
    
    def rotate(self, img: Image, fileinfo: GraphicFileInfo, job_definition: JobDefinition):
        
        if job_definition.rotation == 0 and not job_definition.autorotation:
            return img, fileinfo, job_definition
        
        angle = job_definition.rotation
        if job_definition.autorotation:
            angle = self.image_file_operations.detect_rotation_angle(img)
        if job_definition.alternating_rotation:
            if job_definition.last_rotation is not None:
                angle = self.alternations[job_definition.last_rotation]
            job_definition.last_rotation = angle
        rotated = self.image_file_operations.rotate(img, angle)
        fileinfo.update(rotated)
        
        return rotated, fileinfo, job_definition
    
    def change_resolution(self, img: Image, fileinfo: GraphicFileInfo, job_definition: JobDefinition):
        
        if job_definition.resolution_change is None:
            return img, fileinfo
        
        if job_definition.correct_res_only:
            img = self.image_file_operations.set_resolution(img, job_definition.resolution_change)
        else:    
            try:
                img = self.image_file_operations.change_resolution(img, job_definition.resolution_change)
            except MissingResolutionInfo:
                return img, fileinfo
        
        fileinfo.info['dpi'] = (job_definition.resolution_change, job_definition.resolution_change)
        
        return img, fileinfo
        
    def binarize(self, img: Image, mode_change_definition: ModeChangeDefinition):
        
        if mode_change_definition.binarization_algorithm == FLOYD_STEINBERG:
            # Denoising does not make sense with floyd steinberg binarization
            return self.image_file_operations.binarization_floyd_steinberg(img)
        if mode_change_definition.binarization_algorithm == THRESHOLD:
            return self.image_file_operations.binarization_fixed(img, mode_change_definition.threshold_value)
        if mode_change_definition.binarization_algorithm == OTSU:
            return self.image_file_operations.binarization_otsu(img)
        if mode_change_definition.binarization_algorithm == SAUVOLA:
            return self.image_file_operations.binarization_sauvola(img)

    def split_image(self, img: Image):
        
        width, height = img.size
        img1 = img.crop((0,0,int(width/2), height))
        img2 = img.crop((int(width/2)+1,0,width, height))
        return (img1, img2)

    def save_as_tif(self, images: [Image], fileinfo: GraphicFileInfo):
        
        if fileinfo.format == 'Tiff':
            return
        filebase, file_extension = os.path.splitext(fileinfo.filepath)
        if len(images) == 1:
            new_filepath = filebase + '.tif'
            self.image_file_operations.save_image(images[0], new_filepath)
            #images[0].save(new_filepath, compression="tiff_lzw", dpi=fileinfo.info['dpi'])
        else:
            for i in range(1, len(images) + 1):
                new_filepath = "%s%0.3d.tif" % (filebase, i)
                self.image_file_operations.save_image(images[i-1], new_filepath)
