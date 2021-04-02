'''
Created on 16.02.2021

@author: michael
'''
import os
import tempfile

from PIL import Image, ImageOps, ImageEnhance
from injector import singleton, inject
import numpy
import pytesseract

from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
from Asb.ScanConverter.ImageOperations import AltoPageLayout, \
    ImageFileOperations, MissingResolutionInfo, pil_to_ndarray
import re


Image.MAX_IMAGE_PIXELS = None

BLACK_AND_WHITE = "Schwarz-Weiß"
GRAYSCALE = "Graustufen"
COLOR = "Farbe"
COLOR_WITH_ALPHA = "Farbe mit Transparenz"
INDEX = "Indexiert"

FLOYD_STEINBERG = "Bilder optimal"
THRESHOLD = "Schwellwert"
SAUVOLA = "Text optimal"
MIXED = "Alles optimal (experimentell)"

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
        for key in self.info.keys():
            print(key)
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

class JobDefinition:
    
    SORT_FIRST_PAGE = "first_page"
    SORT_SHEETS = "sort sheets"
    def __init__(self):
        
        self.task = None
        self.fileinfos = []
        self.resolution_change = None
        self.modus_change = None
        self.binarization_algorithm = FLOYD_STEINBERG
        self.threshold_value = 127
        self.output_path = None
        self.split = False
        self.sort = None
        self.rotation = 0
        self.autorotation = False
        self.denoise = False
        self.denoise_threshold = 12
        self.connectivity = 4

@singleton
class FormatConversionService(object):
    '''
    classdocs
    '''
    
    @inject
    def __init__(self, image_detection_service: Detectron2ImageDetectionService,
                 image_file_operations: ImageFileOperations):
        
        self.image_detection_service = image_detection_service
        self.image_file_operations = image_file_operations

    def perform_changes(self, img: Image, fileinfo: GraphicFileInfo, params: JobDefinition):
        
        #img = self.enhance_contrast(img)
        img, fileinfo = self.change_resolution(img, fileinfo, params)
        img, fileinfo = self.change_mode(img, fileinfo, params)
        img, fileinfo = self.rotate(img, fileinfo, params)
        return img, fileinfo

    def load_image(self, fileinfo: GraphicFileInfo):
        
        return Image.open(fileinfo.filepath)
    
    def change_mode(self, img: Image, fileinfo: GraphicFileInfo, job_definition: JobDefinition):
        
        if job_definition.modus_change is None and not job_definition.denoise:
            return img, fileinfo
        
        if img.mode == BLACK_AND_WHITE:
            # The image is already BW, so no mode change may occur,
            # but perhaps we have to denoise
            if job_definition.denoise:
                return self.image_file_operations.denoise(img, job_definition.denoise_threshold, job_definition.connectivity), fileinfo
            else:
                return img, fileinfo
        
        # If we reach this, mode is either color or gray
        
        if img.mode != GRAYSCALE:
            # The image is some color image, so mode change must be to
            # gray or bw, this means we need at least convert to gray
            img = ImageOps.grayscale(img)
            fileinfo.rawmode = "L"
        
        # We now definitely have a gray image
        
        if job_definition.modus_change == BLACK_AND_WHITE:
            fileinfo.rawmode = "1"
            # Denoising, if requested, is a part of the binarization process
            return self.binarize(img, job_definition), fileinfo
        else:
            return img, fileinfo
    
    def rotate(self, img: Image, fileinfo: GraphicFileInfo, params: JobDefinition):
        
        if params.rotation == 0 and not params.autorotation:
            return img, fileinfo
        
        angle = params.rotation
        if params.autorotation:
            angle = self.image_file_operations.detect_rotation_angle(img)
            print("Angle is: %d" % angle)
        rotated = self.image_file_operations.rotate(img, angle)
        fileinfo.update(rotated)
        
        return rotated, fileinfo
    
    def change_resolution(self, img: Image, fileinfo: GraphicFileInfo, params: JobDefinition):
        
        if params.resolution_change is None:
            return img, fileinfo
        
        try:
            img = self.image_file_operations.change_resolution(img, params.resolution_change)
        except MissingResolutionInfo:
            return img, fileinfo
        
        fileinfo.info['dpi'] = (params.resolution_change, params.resolution_change)
        
        return img, fileinfo
        
    def binarize(self, img: Image, params: JobDefinition):
        
        if params.binarization_algorithm == FLOYD_STEINBERG:
            # Denoising does not make sense with floyd steinberg binarization
            return self.image_file_operations.binarization_floyd_steinberg(img)
        if params.binarization_algorithm == THRESHOLD:
            new_image = self.image_file_operations.binarization_fixed(img, params.threshold_value)
        if params.binarization_algorithm == SAUVOLA:
            new_image = self.image_file_operations.binarization_sauvola(img)
        if params.binarization_algorithm == MIXED:
            # Denoising occurs within mixed binarization if requested
            return self._binarization_mixed(img, params)
        
        if params.denoise:
            return self.image_file_operations.denoise(new_image, params.denoise_threshold, params.connectivity)
        else:
            return new_image

    def _binarization_mixed(self, img, job_definition: JobDefinition):
        
        text_background = self.image_file_operations.binarization_sauvola(img)
        photo_foreground = self.image_file_operations.binarization_floyd_steinberg(self._enhance_photo(img))
        drawings_foreground = self.image_file_operations.binarization_otsu(self._enhance_drawing(img))
        if job_definition.denoise:
            # Denoising does only make sense on the background and perhaps drawings
            # TODO: Applying masks should speed up the process
            text_background = self.image_file_operations.denoise(text_background,
                                          job_definition.denoise_threshold,
                                          job_definition.connectivity)
            # Denoising does not work very well even for drawings
            #drawings_foreground = self.image_file_operations.denoise(drawings_foreground,
            #                              job_definition.denoise_threshold,
            #                              job_definition.connectivity)
        (photo_masks, drawing_masks) = self.image_detection_service.getImageMasks(img)
        for mask in photo_masks:
            text_background.paste(photo_foreground, None, Image.fromarray(mask)) 
        for mask in drawing_masks:
            text_background.paste(drawings_foreground, None, Image.fromarray(mask)) 

        return text_background

    def _enhance_photo(self, img: Image) -> Image:
        
        return ImageEnhance.Contrast(img).enhance(1.3)
    
    def _enhance_drawing(self, img: Image) -> Image:
    
        return img
        #enhanced_img = ImageEnhance.Contrast(img).enhance(1.3)
        #return Image.fromarray(exposure.equalize_adapthist(pil_to_skimage(enhanced_img)))
    

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
            images[0].save(new_filepath, compression="tiff_lzw", dpi=fileinfo.info['dpi'])
        else:
            for i in range(1, len(images) + 1):
                new_filepath = "%s%0.3d.tif" % (filebase, i)
                images[i-1].save(new_filepath, compression="tiff_lzw", dpi=fileinfo.info['dpi'])

        
@singleton
class OCRService():

    @inject
    def __init__(self, image_file_operations: ImageFileOperations):
        
        self.image_file_operations = image_file_operations
        self.denoise_threshold = 1

    def extract_text(self, img: Image, language='deu'):
        
        if self.needs_more_contrast(img):
            img = self.image_file_operations.enhance_contrast(img)
        img = img.convert('L')
        img = self.image_file_operations.binarization_sauvola(img)
        self.image_file_operations.show_image(img)

        return self.post_process_text(pytesseract.image_to_string(img, lang=language))
    
    def post_process_text(self, text: str) -> str:
        
        return re.sub("(?<=\w)-\s+", '', text, flags=re.DOTALL)
    
    def needs_more_contrast(self, img: Image) -> bool:
        '''
        This is quite experimental. First we look for a text area
        in the image that has sufficient size.
        Then we calculate the mean and the standard deviation of the
        darkest pixel value (0-48) and put them into relation.
        If this value is smaller than 2 we assume that the values
        are spread out more and we need more contrast.
        
        Another possibility would be to normalize the histogram
        depending of the size of the text area and define a threshold
        for the standard deviation.
        '''
        
        page_layout = AltoPageLayout(img)
        coordinates = page_layout.get_big_text_block_coordinates()
        
        textblock = img.convert(mode='L').crop(coordinates)
        
        histogram = numpy.histogram(pil_to_ndarray(textblock), bins=256)
        mean = numpy.mean(histogram[0][:48])
        standard_deviation = numpy.std(histogram[0][:48])
        return standard_deviation / mean < 2

@singleton
class PdfService:
    
    @inject
    def __init__(self, format_conversion_service: FormatConversionService):
        
        self.format_conversion_service = format_conversion_service
        
        
    def create_pdf_file(self, job: JobDefinition):
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filenames = []
            for index in range(0, len(job.fileinfos)):
                fileinfo = job.fileinfos[index]
                img = self.format_conversion_service.load_image(fileinfo)
                img, fileinfo = self.format_conversion_service.perform_changes(img, fileinfo, job)
                if job.split:
                    images = self.format_conversion_service.split_image(img)
                else:
                    images = (img,)
                for subindex in range(0, len(images)):
                    filename = os.path.join(tmpdir, "%0.3d%0.3d.tif" % (index, subindex))
                    filenames.append(filename)
                    images[subindex].save(filename, compression="tiff_lzw", dpi=fileinfo.info['dpi'])

            filenames = self.sort_filenames(filenames, job)
            
            tiffoutput = os.path.join(tmpdir, "out.tif")
            pdfoutput = os.path.join(tmpdir, "out.pdf")
            cmd = "tiffcp %s %s" % (" ".join(filenames), tiffoutput)
            print(cmd)
            os.system(cmd)
            cmd = "tiff2pdf -z -o %s %s" % (pdfoutput, tiffoutput)
            print(cmd)
            os.system(cmd)
            cmd = "ocrmypdf -l deu %s %s" % (pdfoutput, job.output_path)
            print(cmd)
            os.system(cmd)

    def sort_filenames(self, filenames, params: JobDefinition):
        
            if params.sort == JobDefinition.SORT_FIRST_PAGE:
                first = filenames[0]
                del(filenames[0])
                filenames.append(first)
                return filenames
                
            if params.sort == JobDefinition.SORT_SHEETS:
                filenumbers = []
                for bogen in range(0, int(len(filenames) / 4)):
                    filenumbers.append(len(filenames) - (bogen * 2 + 1))
                    filenumbers.append(0 + bogen * 2)
                    filenumbers.append(1 + bogen * 2)
                    filenumbers.append(len(filenames) - (bogen * 2 + 2))
                new_filenames = [''] * len(filenames)
                for i in range(0, len(filenumbers)):
                    new_filenames[filenumbers[i]] = filenames[i]
                return new_filenames
    
            return filenames
