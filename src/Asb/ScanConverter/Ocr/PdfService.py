'''
Created on 05.04.2021

@author: michael
'''

from os.path import basename

from reportlab.pdfgen.canvas import Canvas

from Asb.ScanConverter.ImageOperations import ImageFileOperations
from Asb.ScanConverter.Services import JobDefinition, FormatConversionService
from Asb.ScanConverter.Ocr.OCR import OcrRunner
from Asb.ScanConverter.Ocr.Alto import AltoPageLayout
import re

from lxml import etree, html
from injector import singleton, inject
from reportlab.lib.utils import ImageReader
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile
from posix import system

INVISIBLE = 3

@singleton
class PdfService:
    
    @inject
    def __init__(self,
                 format_conversion_service: FormatConversionService, 
                 image_operations: ImageFileOperations,
                 ocr_runner: OcrRunner):
        
        self.format_conversion_service = format_conversion_service
        self.image_ops = image_operations
        self.ocr_runner = ocr_runner
    
    def create_pdf_file(self, job: JobDefinition):
        
        image_infos = job.fileinfos
   
        pdf = Canvas(job.output_path, pageCompression=1)
        pdf.setCreator('Scan-Convert')
        pdf.setTitle(basename(job.output_path))
        dpi = 300

        images = self.collect_and_convert_images(image_infos, job)
        images = self.sort_images(images, job.sort)
        
        for image in images:
            if image is None:
                continue
            width_in_dots, height_in_dots = image.size

            try:
                dpi = image.info['dpi'][0]
            except KeyError:
                pass
            
            page_width = width_in_dots * 72 / dpi
            page_height = height_in_dots * 72 / dpi
            
            pdf.setPageSize((width_in_dots * inch / dpi, height_in_dots * inch / dpi))

            img_stream = io.BytesIO()
            image.save(img_stream, format='png')
            img_stream.seek(0)
            img_reader = ImageReader(img_stream)
            pdf.drawImage(img_reader, 0, 0, width=page_width, height=page_height)
            
            if job.ocr:
                #alto_layout = self.ocr_runner.get_alto_layout(img)
                # TODO: Configure language
                hocr_layout = self.ocr_runner.get_hocr(image)
                self.add_text_layer_from_hocr(pdf, hocr_layout, page_height, dpi)

            pdf.showPage()
        
        pdf.save()
        
        if job.pdfa:
            self._convert_to_pdfa(job)
    
    def _convert_to_pdfa(self, job: JobDefinition):
        
        # It is much too complicated to use the code of ocrmypdf directly
        # because of real ugly dependencies. So it is much more easy to
        # check if ocrmypdf is installed and use it from the command line.
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpfile = "%s/output.pdf" % tmpdirname
            system("ocrmypdf --skip-text %s %s" % (job.output_path, tmpfile))
            system("mv %s %s" % (tmpfile, job.output_path))
    
    def collect_and_convert_images(self, infos, job: JobDefinition):

        images = []        
        for image_info in infos:
            img = self.image_ops.load_image(image_info.filepath)

            converted_img, image_info, job = self.format_conversion_service.perform_changes(img, image_info, job)
            
            if job.split: 
                page_images = self.image_ops.split_image(converted_img)
            else:
                page_images = (converted_img, )

            for image in page_images:
                images.append(image)
        
        return images
        
    def sort_images(self, images, sorting):
        
        if sorting is None:
            return images
        if sorting is JobDefinition.SORT_FIRST_PAGE:
            return self.sort_images_first_page(images)
        if sorting is JobDefinition.SORT_SHEETS:
            return self.sort_images_sheets(images)
        
        raise Exception("Unknown sorting request")
    
    def sort_images_first_page(self, images):
        
        first = images[0]
        del(images[0])
        images.append(first)
        return images
    
    def sort_images_sheets(self, images):
        
        filenumbers = []
        for bogen in range(0, int(len(images) / 4)):
            filenumbers.append(len(images) - (bogen * 2 + 1))
            filenumbers.append(0 + bogen * 2)
            filenumbers.append(1 + bogen * 2)
            filenumbers.append(len(images) - (bogen * 2 + 2))
        
        sorted_images = [None] * len(images)
        for i in range(0, len(filenumbers)):
            sorted_images[filenumbers[i]] = images[i]
            
        return sorted_images

    def add_text_layer_from_alto(self, pdf: Canvas, alto_layout: AltoPageLayout, page_height: int, dpi: int):
        """Draw an invisible text layer for OCR data"""
        
        for line in alto_layout.get_all_lines():
            
            line_bbox = line.get_bounding_box()
            
            for string in line.get_strings():
                
                rawtext = string.get_text()
                if rawtext == '':
                    continue
                string_text_width = pdf.stringWidth(rawtext, 'Times-Roman', 8)
                if string_text_width <= 0:
                    continue
                
                string_bbox = string.get_bounding_box()
                
                text = pdf.beginText()
                text.setTextRenderMode(INVISIBLE)
                text.setFont('Times-Roman', 8)
                text.setTextOrigin(string_bbox[0] * 72 / dpi, page_height - (line_bbox[3] * 72 / dpi))
                string_bbox_width = string.get_width() * 72 / dpi
                text.setHorizScale(100.0 * string_bbox_width / string_text_width)
                text.textLine(rawtext)
                pdf.drawText(text)

    def add_text_layer_from_hocr(self, pdf, hocr_layout, height, dpi):
        '''
        This terrible code is lifted from https://github.com/ocropus/hocr-tools
        The result is better, because we have baseline information in hocr, which
        is missing in alto.
        '''

        p1 = re.compile(r'bbox((\s+\d+){4})')
        p2 = re.compile(r'baseline((\s+[\d\.\-]+){2})')
        hocr = etree.fromstring(hocr_layout, html.XHTMLParser())
        for line in hocr.xpath('//*[@class="ocr_line"]'):
            bbox_line = p1.search(line.attrib['title']).group(1).split()
            try:
                baseline = p2.search(line.attrib['title']).group(1).split()
            except AttributeError:
                baseline = [0, 0]
            bbox_line = [float(i) for i in bbox_line]
            baseline = [float(i) for i in baseline]
            xpath_elements = './/*[@class="ocrx_word"]'
            if (not (line.xpath('boolean(' + xpath_elements + ')'))):
                # if there are no words elements present,
                # we switch to lines as elements
                xpath_elements = '.'
            for word in line.xpath(xpath_elements):
                rawtext = word.text_content().strip()
                if rawtext == '':
                    continue
                text_width = pdf.stringWidth(rawtext, 'Times-Roman', 8)
                if text_width <= 0:
                    continue
                bbox_text = p1.search(word.attrib['title']).group(1).split()
                bbox_text = [float(i) for i in bbox_text]
                baseline_absolute = self.polyval(baseline,
                        (bbox_text[0] + bbox_text[2]) / 2 - bbox_line[0]) + bbox_line[3]
                text = pdf.beginText()
                text.setTextRenderMode(3)  # double invisible
                text.setFont('Times-Roman', 8)
                text.setTextOrigin(bbox_text[0] * 72 / dpi, height - baseline_absolute * 72 / dpi)
                bbox_text_width = (bbox_text[2] - bbox_text[0]) * 72 / dpi
                text.setHorizScale(100.0 * bbox_text_width / text_width)
                text.textLine(rawtext)
                pdf.drawText(text)


    def polyval(self, poly, x):
        '''
        WTF? Polyval? Really? "poly" is a tuple, decribed in the documentation
        this way: The two numbers for the baseline are the slope (1st number) and
        constant term (2nd number) of a linear equation describing the baseline
        relative to the bottom left corner of the bounding box
        '''
        return x * poly[0] + poly[1]
