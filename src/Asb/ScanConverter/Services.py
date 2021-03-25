'''
Created on 16.02.2021

@author: michael
'''
from injector import singleton, inject
import os
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import re
from Asb.ScanConverter.ImageDetection import Detectron2ImageDetectionService
import numpy
from skimage.filters.thresholding import threshold_sauvola, threshold_otsu
import cv2
import tempfile
from PIL.ImageOps import autocontrast
from skimage.filters.rank.generic import enhance_contrast
from skimage import exposure
from Asb.ScanConverter.Tools import pil_to_skimage, skimage_to_pil,\
    pil_to_ndarray, pil_to_cv2image, cv2image_to_pil
from skimage.filters.rank._percentile import enhance_contrast_percentile

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
    def __init__(self, image_detection_service: Detectron2ImageDetectionService):
        
        self.image_detection_service = image_detection_service

    def perform_changes(self, img: Image, fileinfo: GraphicFileInfo, params: JobDefinition):
        
        #img = self.enhance_contrast(img)
        img, fileinfo = self.change_resolution(img, fileinfo, params)
        img, fileinfo = self.change_mode(img, fileinfo, params)
        img, fileinfo = self.rotate(img, fileinfo, params)
        return img, fileinfo

    def load_image(self, fileinfo: GraphicFileInfo):
        
        return Image.open(fileinfo.filepath)
    
    def enhance_contrast(self, img: Image) -> Image:
        
        #-----Reading the image-----------------------------------------------------
        cv2_img = pil_to_cv2image(img)
        #-----Converting image to LAB Color model----------------------------------- 
        lab= cv2.cvtColor(cv2_img, cv2.COLOR_BGR2LAB)
        #-----Splitting the LAB image to different channels-------------------------
        l, a, b = cv2.split(lab)
        #-----Applying CLAHE to L-channel-------------------------------------------
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        #-----Merge the CLAHE enhanced L-channel with the a and b channel-----------
        limg = cv2.merge((cl,a,b))
        #-----Converting image from LAB Color model to RGB model--------------------
        return Image.fromarray(cv2.cvtColor(limg, cv2.COLOR_LAB2RGB))

    def change_mode(self, img: Image, fileinfo: GraphicFileInfo, job_definition: JobDefinition):
        
        if job_definition.modus_change is None and not job_definition.denoise:
            return img, fileinfo
        
        if img.mode == BLACK_AND_WHITE:
            # The image is already BW, so no mode change may occur,
            # but perhaps we have to denoise
            if job_definition.denoise:
                return self.denoise(img, job_definition.denoise_threshold, job_definition.connectivity), fileinfo
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
            angle = self._detect_rotation_angle(img)
            print("Angle is: %d" % angle)
        rotated = img.rotate(angle, expand=True)
        fileinfo.update(rotated)
        
        return rotated, fileinfo
    
    def _detect_rotation_angle(self, img: Image):
        
        info = pytesseract.image_to_osd(img).replace("\n", " ")
        matcher = re.match('.*Orientation in degrees:\s*(\d+).*', info)
        if matcher is not None:
            return int(matcher.group(1))
        else:
            raise(Exception("RE is not working"))
    
    def change_resolution(self, img: Image, fileinfo: GraphicFileInfo, params: JobDefinition):
        
        if params.resolution_change is None:
            return img, fileinfo
        
        if not 'dpi' in img.info:
            return img, fileinfo
        
        current_xres, current_yres = img.info['dpi']
        if current_xres == 1 or current_yres == 1:
            return img, fileinfo
        
        if current_xres == params.resolution_change and current_yres == params.resolution_change:
            return img, fileinfo
        
        current_width, current_height = img.size

        new_width = int(current_width * params.resolution_change / current_xres)
        new_height = int(current_height * params.resolution_change / current_yres)
        
        new_size = (new_width, new_height)
        
        fileinfo.info['dpi'] = (params.resolution_change, params.resolution_change)
        
        return img.resize(new_size), fileinfo
        
    def binarize(self, img: Image, params: JobDefinition):
        
        if params.binarization_algorithm == FLOYD_STEINBERG:
            # Denoising does not make sense with floyd steinberg binarization
            return self._binarization_floyd_steinberg(img)
        if params.binarization_algorithm == THRESHOLD:
            new_image = self._binarization_fixed(img, params.threshold_value)
        if params.binarization_algorithm == SAUVOLA:
            new_image = self._binarization_sauvola(img)
        if params.binarization_algorithm == MIXED:
            # Denoising occurs within mixed binarization if requested
            return self._binarization_mixed(img, params)
        
        if params.denoise:
            return self.denoise(new_image, params.denoise_threshold, params.connectivity)
        else:
            return new_image

    def _binarization_floyd_steinberg(self, img):
        
        # Default for PIL images convert is Floyd/Steinberg
        return img.convert("1")

    def _binarization_fixed(self, img, threshold=127):

        return img.point(lambda v: 1 if v > threshold else 0, "1")

    def _binarization_otsu(self, img):

        in_array = numpy.array(img)
        mask = threshold_otsu(in_array)
        out_array = in_array > mask
        return Image.fromarray(out_array)
    
    def _binarization_sauvola(self, img, window_size=41):

        in_array = numpy.array(img)
        mask = threshold_sauvola(in_array, window_size=window_size)
        out_array = in_array > mask
        return Image.fromarray(out_array)

    def _binarization_mixed(self, img, job_definition: JobDefinition):
        
        text_background = self._binarization_sauvola(img)
        photo_foreground = self._binarization_floyd_steinberg(self._enhance_photo(img))
        drawings_foreground = self._binarization_otsu(self._enhance_drawing(img))
        if job_definition.denoise:
            # Denoising does only make sense on the background and perhaps drawings
            # TODO: Applying masks should speed up the process
            text_background = self.denoise(text_background,
                                          job_definition.denoise_threshold,
                                          job_definition.connectivity)
            # Denoising does not work very well even for drawings
            #drawings_foreground = self.denoise(drawings_foreground,
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
    
    def denoise(self, img: Image, threshold, connectivity):
        
        if img.mode != "1":
            return img

        inverted = ImageOps.invert(img.convert("RGB"))
        
        ndarray = numpy.array(inverted.convert("1"), dtype=numpy.uint8)

        print("Connectivity is %d" % connectivity)
        no_of_components, labels, stats, centroids = cv2.connectedComponentsWithStats(ndarray, connectivity=connectivity)
        sizes = stats[:, cv2.CC_STAT_AREA];
        print("Found %d components" % no_of_components)

        bw_new = numpy.ones((ndarray.shape), dtype=numpy.bool)
        big_components = 0
        for shape_identifier in range(1, no_of_components):
            if sizes[shape_identifier] > threshold:
                big_components += 1
                bw_new[labels == shape_identifier] = 0
        print("Removed %d components" % (no_of_components - big_components))
        return Image.fromarray(bw_new)

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
