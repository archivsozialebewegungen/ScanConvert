'''
Created on 20.04.2022

@author: michael
'''
from PIL.Image import Image
from Asb.ScanConverter.ImageOperations import ImageFileOperations
from injector import inject, singleton
import os
import numpy

# Modes
BW = "black and white"
BW_OTSU = "black and white with otsu"
BW_THRESHOLD = "black and with with threshold"
BW_FLOYD_STEINBERG = "black and with with floyd steinberg algorightm"
GRAYSCALE = "grayscale"
COLOR = "color"
COLOR_WITH_ALPHA = "color with alpha"
INDEX = "Indexierte Farben"
KEEP_MODE = "keep mode"

SCAN_PROFILE_SINGLE_PAGES = "single pages"
SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD = "double pages overhead"
SCAN_PROFILE_DOUBLE_PAGES_FEEDER = "double pages feeder"

OUTPUT_PROFILE_BW_OTSU_300_DPI = "pdf bw text 300 dpi"
OUTPUT_PROFILE_BW_THRESHOLD_300_DPI = "pdf mixed text 300 dpi"
OUTPUT_PROFILE_NO_MODE_CHANGE_400_DPI = "tiff 400 dpi"

PDF = "pdf"
TIFF = "tiff"

class Transformation(object):
    '''
    This class represents the transformations,
    that should be performed on a scan.
    It is just an information container without
    any methods, just with properties.
    
    If properties are None, then their values
    are supposed to inherited from a default
    transformation object. This should be
    set as parent.
    '''

    alternations = {0: 180, 90: 270, 180: 0, 270: 90}

    def __init__(self, parent = None):
        
        self.parent = parent
        self._target_resolution = None
        self._target_mode = None
        self._threshold = None
        self._rotation = None
        self._alternating_rotation = None
        
    def _get_target_resolution(self) -> int:
        
        if self._target_resolution is None:
            return self.parent._target_resolution
        return self._target_resolution
    
    def _set_target_resolution(self, value: int):
        
        self._target_resolution = value
        
    def _get_target_mode(self) -> str:
        
        if self._target_mode is None:
            return self.parent._target_mode
        return self._target_mode
    
    def _set_target_mode(self, value: str):
        
        self._target_mode = value

    def _get_threshold(self) -> int:
        
        if self._threshold is None:
            return self.parent._threshold
        return self._threshold
    
    def _set_threshold(self, value: int):
        
        self._threshold = value
        
    def _get_rotation(self) -> int:
        
        if self._rotation is None:
            return self.parent._rotation
        return self._rotation
    
    def _set_rotation(self, value: int):
        
        self._rotation = value
        
    def _get_alternating_rotation(self) -> bool:
        
        if self._alternation_rotation is None:
            return self.parent._alternating_rotation
        return self._alternating_rotation
    
    def _set_alternating_rotation(self, value: bool):
        
        self._alternating_rotation = value
    
    # Properties depending on selected output    
    target_resolution = property(_get_target_resolution, _set_target_resolution) 
    target_mode = property(_get_target_mode, _set_target_mode) 
    threshold = property(_get_threshold, _set_threshold) 
    
    # Properties depending on scan type
    rotation = property(_get_rotation, _set_rotation) 
    alternating_rotation = property(_get_alternating_rotation, _set_alternating_rotation) 

class Scan(object):
    '''
    This class represents just the scan on the disk.
    It contains all possible informations including
    information on images, but probably in the future
    also of text blocks. And it contains the page
    numbers that scan represents. In practice this
    might be one page for a simple scan and two
    pages for a doube page scan that needs to be
    split.
    '''
    modes = {"1": BW, "L": GRAYSCALE, "RGB": COLOR,
             "RGBA": COLOR_WITH_ALPHA, "P": INDEX}

    def __init__(self, qualified_file_name: str):
        '''
        Constructor
        '''
        self.qualified_file_name = qualified_file_name
        
        self.format = None
        self.rawmode = None
        self.width = None
        self.height = None
        self.info = None
        
        self.embedded_images_parameters = []
        
        self.page_nos = []
        
    def get_image_mask(self):
        
        mask = numpy.zeros((self.height, self.width), dtype=bool)
        for image_region in self.embedded_images_parameters:
            mask[image_region.y:image_region.y + image_region.height, 
                 image_region.x:image_region.x + image_region.width] = True
        
        return Image.fromarray(mask)

    def get_text_mask(self):
        
        mask = numpy.ones((self.height, self.width), dtype=bool)
        for image_region in self.embedded_images_parameters:
            mask[image_region.y:image_region.y + image_region.height, 
                 image_region.x:image_region.x + image_region.width] = False
        
        return Image.fromarray(mask)

    def has_images(self):
        
        return self.embedded_images_parameters > 0

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
    
    def _get_size(self) -> float:
        
        return self.width * self.height * 1.0
    
    def _get_mode(self) -> str:
        
        if self.rawmode in self.modes:
            return self.modes[self.rawmode]
        
        return "Unbekannt (%s)" % self.rawmode
    
    def is_half_page_of(self, scan) -> bool:
        
        ratio = scan.size / self.size
        return abs(ratio - 2) < 0.2
            
    resolution = property(_get_resolution)
    filename = property(_get_filename)
    mode = property(_get_mode)
    size = property(_get_size)

class Project(object):
    
    def __init__(self):
        
        self.default_transformation = Transformation()
        self.alternative_transformation = {}
        self.scans = []
        self.page_cache = {}
        self.scan_profile = SCAN_PROFILE_SINGLE_PAGES
        self.no_of_pages = 0
        
    def add_scan(self, scan: Scan):
        
        self.scans.append(scan)
        self._set_page_information(self.scan_profile)
    
    def change_scan_profile(self, scan_profile: str):
        
        self._set_page_information(scan_profile)
        
    def change_output_profile(self, output_profile: str):
        
        if output_profile == OUTPUT_PROFILE_NO_MODE_CHANGE_400_DPI:
            self._set_output_profile_tiff_400()
        elif output_profile == OUTPUT_PROFILE_BW_OTSU_300_DPI:
            self._set_output_profile_bw_otsu_300()
        elif output_profile == OUTPUT_PROFILE_BW_THRESHOLD_300_DPI:
            self._set_output_profile_bw_threshold_300()
        else:
            raise Exception("Unknown output profile")
    
    def _set_page_information(self, scan_profile: str):
        
        if scan_profile == SCAN_PROFILE_SINGLE_PAGES:
            self._set_page_information_single_pages()
        elif scan_profile == SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD:
            self._set_page_information_double_page_sequence()
        elif scan_profile == SCAN_PROFILE_DOUBLE_PAGES_FEEDER:
            self._set_page_information_double_page_feeder()
        else:
            raise Exception("Unknown scan profile")

    def _set_output_profile_tiff_400(self):
        
        self.default_transformation.target_resolution = 400
        self.default_transformation.target_mode = KEEP_MODE
        self.default_transformation.threshold = 160
    
    def _set_output_profile_bw_otsu_300(self):
        
        self.default_transformation.target_resolution = 300
        self.default_transformation.target_mode = BW_OTSU
        self.default_transformation.threshold = 160
    
    def _set_output_profile_bw_threshold_300(self):
        
        self.default_transformation.target_resolution = 300
        self.default_transformation.target_mode = BW_THRESHOLD
        self.default_transformation.threshold = 160
        
    def _set_page_information_single_pages(self):

        self.scan_profile = SCAN_PROFILE_SINGLE_PAGES
        self.default_transformation.rotation = 0
        self.default_transformation.alternating_rotation = False
        
        page_counter = 0
        for scan in self.scans:
            page_counter += 1
            scan.page_nos = (page_counter,)
            
        self.no_of_pages = page_counter

    def _set_page_information_double_page_sequence(self):
        
        self.scan_profile = SCAN_PROFILE_DOUBLE_PAGES_OVERHEAD
        self.default_transformation.rotation = 0
        self.default_transformation.alternating_rotation = False
        
        self.no_of_pages = 0
        
        no_of_scans = len(self.scans)
        
        if no_of_scans == 0:
            return
        
        # Edge case - we split without reordering because
        # we have no clue it reordering is necessary
        if no_of_scans == 1:
            self.scans[0].page_nos = (1,2)
            self.no_of_pages = 2
            return

        # Determine the largest scan size so we can
        # check if we have a single or a double page scan        
        largest_scan = self.scans[0]
        for scan in self.scans:
            if scan.size > largest_scan.size:
                largest_scan = scan

        page_counter = 1
        for scan_idx in range(0, no_of_scans):
            
            if self.scans[scan_idx].is_half_page_of(largest_scan):
                # Single page scan (normally front or back cover)
                self.scans[scan_idx].page_nos = (page_counter,)
                self.no_of_pages += 1
                page_counter += 1
            else:
                # Double page scan (two pages on one scan)
                self.scans[scan_idx].page_nos = (page_counter, page_counter + 1)
                self.no_of_pages += 2
                page_counter += 2
                
    def _set_page_information_double_page_feeder(self):
        
        self.scan_profile = SCAN_PROFILE_DOUBLE_PAGES_FEEDER
        self.default_transformation.rotation = 270
        self.default_transformation.alternating_rotation = True
        
        no_of_scans = len(self.scans)
        
        if no_of_scans % 2 != 0:
            # We need sheets completely with
            # front and back side, i.e. four pages
            return
        
        page_numbers = []
        for sheet_no in range(0, int(no_of_scans / 2)):
            page_numbers.append(no_of_scans * 2 - (sheet_no * 2))
            page_numbers.append(1 + sheet_no * 2)
            page_numbers.append(2 + sheet_no * 2)
            page_numbers.append(no_of_scans * 2 - (sheet_no * 2 + 1))

        page_no_idx = 0
        self.no_of_pages = 0
        for scan in self.scans:
            scan.page_nos = (page_numbers[page_no_idx], page_numbers[page_no_idx+1])
            page_no_idx += 2
            self.no_of_pages += 2

@singleton
class ScanTransformationService(object):
    
    @inject
    def __init__(self, image_operations: ImageFileOperations):
        
        self.ops = image_operations
        
    def load_scan(self, qualified_file_name):

        scan = Scan(qualified_file_name)
        scan_img = self.ops.load_image(qualified_file_name)
        scan.format = type(scan_img).__name__.replace('ImageFile', '')
        scan.rawmode = scan_img.mode
        scan.width = scan_img.width
        scan.height = scan_img.height
        scan.info = scan_img.info
        scan_img.close()
        
        return scan
    
    def get_page(self, page_no: int, project: Project) -> Image:
        
        if page_no in project.page_cache:
            result = project.page_cache[page_no]
            del(project.page_cache[page_no])
            return result
        
        for scan in project.scans:
            if page_no in scan.page_nos:
                if scan.qualified_file_name in project.alternative_transformation:
                    transformation = project.alternative_transformation[scan.qualified_file_name]
                else:
                    transformation = project.default_transformation
                pages = self._extract_pages(scan, transformation, page_no)    
                for counter in range(0, len(scan.page_nos)):
                    if scan.page_nos[counter] == page_no:
                        result = pages[counter]
                    else:
                        project.page_cache[scan.page_nos[counter]] = pages[counter]
                return result
    
    def _extract_pages(self, scan: Scan, transformation: Transformation, page_no: int) -> Image:
        
        img = self.ops.load_image(scan.qualified_file_name)
        img = self._change_mode(img, scan.mode, transformation.target_mode, transformation.threshold)
        if scan.resolution != transformation.target_resolution:
            img = self._change_resolution(img, transformation.target_resolution)
        if transformation.rotation != 0:
            img = self._rotate(img, transformation.rotation)
        
        if len(scan.page_nos) == 1:
            return (img,)
        
        return self._split(img)

    def _change_mode(self, img: Image, scan_mode: str, target_mode: str, threshold: str):
        
        # Handle no mode change or color target mode
        
        if target_mode == KEEP_MODE or target_mode == COLOR or target_mode == COLOR_WITH_ALPHA:
            # Nothing to do
            return img
        
        # Handle grayscale target mode
        if target_mode == GRAYSCALE and scan_mode == COLOR or scan_mode == COLOR_WITH_ALPHA:
            return self.ops.convert_to_gray(img)
        else:
            return img
        
        # Handle bw target mode
        
        # First step: make sure we have a grayscale img
        if scan_mode == COLOR or scan_mode == COLOR_WITH_ALPHA:
            img = self.ops.convert_to_gray(img)
        
        if target_mode == BW_OTSU:
            
            return self.ops.binarization_otsu(img)
        
        if target_mode == BW_THRESHOLD:
            
            return self.ops.binarization_fixed(img, threshold)
        
        raise Exception("Target mode '%s' not yet implemented" % target_mode)

    def _change_resolution(self, img: Image, new_resolution: int):
        
        return self.ops.change_resolution(img, new_resolution)
    
    def _rotate(self, img: Image, angle: int):
        
        return self.ops.rotate(img, angle)

@singleton    
class TiffCreationService():
    
    @inject
    def __init__(self, img_ops: ImageFileOperations, scan_transformation_service: ScanTransformationService):
        
        self.ops = img_ops
        self.scan_transformation_service = scan_transformation_service
        
    def create_tifs(self, project: Project, file_base: str):
        
        file_template = file_base + "_%1.0d.tif"
        if project.no_of_pages > 10:
            file_template = file_base + "_%2.0d.tif"
        if project.no_of_pages > 100:
            file_template = file_base + "_%3.0d.tif"
        if project.no_of_pages > 1000:
            file_template = file_base + "_%4.0d.tif"
            
        for page_no in range(1, project.no_of_pages + 1):
            img = self.scan_transformation_service.get_page(page_no, project)
            self.ops.save_image(img, file_template % page_no)
        