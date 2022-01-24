'''
Created on 13.02.2021

@author: michael
'''

import sys
import threading

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QApplication, QPushButton, QTableWidget, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTableWidgetItem, QAbstractItemView, \
    QComboBox, QRadioButton, QButtonGroup, QGroupBox, QSlider, QCheckBox
from injector import Injector, inject, singleton

from Asb.ScanConverter.Services import FormatConversionService, GraphicFileInfo, \
    JobDefinition, GRAYSCALE, BLACK_AND_WHITE, FLOYD_STEINBERG, THRESHOLD, \
    SAUVOLA, ModeChangeDefinition
from Asb.ScanConverter.Ocr.PdfService import PdfService
import traceback
from copy import deepcopy
from os.path import exists


TASK_CONVERT_JPEG = "Jpegs nach tif konvertieren"
TASK_COLLATE_TO_PDF = "Als pdf zusammenfassen"

@singleton
class TaskManager():
    

    @inject
    def __init__(self, pdf_service: PdfService, format_conversion_service: FormatConversionService):
        
        self.format_conversion_service = format_conversion_service
        self.pdf_service = pdf_service
        
        self.message_label = None
        
        self.unfinished_tasks = []
        self.finished_tasks = []
        self.worker_thread_running = False
    
    def add_task(self, job: JobDefinition):
        
        self.unfinished_tasks.append(job)
        self.message_function()
        if self.worker_thread_running:
            return
        thread = threading.Thread(target=self.run_jobs)
        thread.start()
            
    def run_job(self, job: JobDefinition):
        
        try:
            if job.task == TASK_CONVERT_JPEG:
                self.convert_to_tif(job)
            if job.task == TASK_COLLATE_TO_PDF:
                self.pdf_service.create_pdf_file(job)
        except Exception as e:
            # TODO: Show error somewhere
            print(e)
            print(traceback.format_exc())
        
    def convert_to_tif(self, job: JobDefinition):
        
        for info in job.fileinfos:
            img = self.format_conversion_service.load_image(info)
            img, info, job = self.format_conversion_service.perform_changes(img, info, job)
            if job.split:
                self.format_conversion_service.save_as_tif(self.format_conversion_service.split_image(img), info)
            else:
                self.format_conversion_service.save_as_tif((img,), info)
    
    def run_jobs(self):
        
        self.worker_thread_running = True
        
        while len(self.unfinished_tasks) > 0:
            
            self.run_job(self.unfinished_tasks[0])
            self.finished_tasks.append(self.unfinished_tasks[0])
            del(self.unfinished_tasks[0])
            self.message_function()
        
        self.worker_thread_running = False
    
    
class Window(QWidget):
    

    @inject
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.single_file_mode = False
        self.mode_change_active = True
        
        self.job_definition = JobDefinition()

        self.task_manager = task_manager
        self.createWidgets()
        self.task_manager.message_function = self.show_job_status
        self.show_job_status()
        self.setGeometry(100, 100, 300, 300)
        self.setWindowTitle("Scan-Kovertierer")
        self.fileinfos = []
        

    def show_job_status(self):
        
        total = len(self.task_manager.finished_tasks) + len(self.task_manager.unfinished_tasks)
        unfinished = len(self.task_manager.unfinished_tasks)
        self.task_label.setText("Unvollendete Aufgaben: %d Aufgaben ingesamt: %d" % (unfinished, total))

    def _get_file_button_layout(self):

        file_selection_button = QPushButton("Laden")
        file_up_button = QPushButton("Hoch")
        file_down_button = QPushButton("Runter")
        file_remove_button = QPushButton("Entfernen")
        file_selection_button.clicked.connect(self.add_files)
        file_up_button.clicked.connect(self.files_up)
        file_down_button.clicked.connect(self.files_down)
        file_remove_button.clicked.connect(self.remove_files)

        button_layout = QHBoxLayout()
        button_layout.addWidget(file_selection_button)
        button_layout.addWidget(file_up_button)
        button_layout.addWidget(file_down_button)
        button_layout.addWidget(file_remove_button)
        
        return button_layout
        
    def _get_file_list_widget(self):

        self.file_list = QTableWidget()
        self.file_list.setGeometry(400, 400, 600, 300)
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["Datei", "Modus", "Auflösung", "Format"])
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_list.itemClicked.connect(self._file_clicked)
        
        return self.file_list
    
    def _is_exactly_one_row_selected(self):

        indexes = self.file_list.selectionModel().selectedRows()
        return len(indexes) == 1

    def _get_first_selected_file_info(self):

        fileinfo = None
        for row_no in range(0, self.file_list.rowCount()):
            if self.file_list.item(row_no, 0).isSelected():
                if fileinfo is None:
                    fileinfo = self.fileinfos[row_no] 
                else:
                    raise Exception("More than one file selected!")
        
        if fileinfo is None:    
            raise Exception("No file selected!")
        
        return fileinfo

    def createWidgets(self):
        
        left_column = QVBoxLayout()
        left_column.addLayout(self._get_file_button_layout())
        left_column.addWidget(self._get_file_list_widget())

        right_column = QVBoxLayout()
        
        right_column.addWidget(QLabel("Aufgabe:"))
        self.task_select = QComboBox()
        self.task_select.addItem(TASK_COLLATE_TO_PDF)
        self.task_select.addItem(TASK_CONVERT_JPEG)
        right_column.addWidget(self.task_select)
        
        res_box = self._get_resolution_box()
        right_column.addWidget(res_box)
        
        rotate_box = self._get_rotate_box()
        right_column.addLayout(rotate_box)
        
        modus_box = self._get_modus_box()
        right_column.addWidget(modus_box)

        sort_box = self._get_sort_box()
        right_column.addWidget(sort_box)

        ocr_widget = self._get_ocr_widget()
        right_column.addWidget(ocr_widget)

        denoise_widget = self._get_denoise_widget()
        right_column.addWidget(denoise_widget)

        pdfa_widget = self._get_pdfa_widget()
        right_column.addWidget(pdfa_widget)

        run_button = QPushButton("Aufgabe ausführen")
        run_button.clicked.connect(self.add_task)
        right_column.addWidget(run_button)
        
        self.task_label = QLabel("Nicht initalisiert")
        right_column.addWidget(self.task_label)
        
        layout = QHBoxLayout()
        layout.addLayout(left_column)
        layout.addLayout(right_column)
        
        self.setLayout(layout)

    def _get_resolution_box(self):
        
        res_box = QGroupBox("Auflösungsänderung")
        res_layout = QVBoxLayout()
        res_layout_1 = QHBoxLayout()
        resolution_group = QButtonGroup(self)
        self.resolution_no = QRadioButton("keine", self)
        self.resolution_300 = QRadioButton("300 dpi", self)
        self.resolution_400 = QRadioButton("400 dpi", self)
        self.resolution_no.setChecked(True)
        res_layout_1.addWidget(self.resolution_no)
        res_layout_1.addWidget(self.resolution_300)
        res_layout_1.addWidget(self.resolution_400)
        resolution_group.addButton(self.resolution_no)
        resolution_group.addButton(self.resolution_300)
        resolution_group.addButton(self.resolution_400)
        res_layout.addLayout(res_layout_1)
        self.correct_res_only_checkbox = QCheckBox("Auflösung nur korrigieren", self)
        res_layout.addWidget(self.correct_res_only_checkbox)
        res_box.setLayout(res_layout)
        
        return res_box

    def _get_rotate_box(self):
        
        complete_box = QVBoxLayout()
                    
        rotate_box = QGroupBox("Drehen")
        rotate_layout = QHBoxLayout()
        rotate_group = QButtonGroup(self)
        self.rotate_0 = QRadioButton("0°", self)
        self.rotate_90 = QRadioButton("90°", self)
        self.rotate_180 = QRadioButton("180°", self)
        self.rotate_270 = QRadioButton("270°", self)
        self.rotate_auto = QRadioButton("auto", self)
        self.rotate_0.setChecked(True)
        rotate_layout.addWidget(self.rotate_0)
        rotate_layout.addWidget(self.rotate_90)
        rotate_layout.addWidget(self.rotate_180)
        rotate_layout.addWidget(self.rotate_270)
        rotate_layout.addWidget(self.rotate_auto)
        rotate_group.addButton(self.rotate_0)
        rotate_group.addButton(self.rotate_90)
        rotate_group.addButton(self.rotate_180)
        rotate_group.addButton(self.rotate_270)
        rotate_group.addButton(self.rotate_auto)
        rotate_box.setLayout(rotate_layout)
        complete_box.addWidget(rotate_box)

        self.rotate_alternating_checkbox = QCheckBox("alternierend")
        complete_box.addWidget(self.rotate_alternating_checkbox)
    
        return complete_box

    def _get_modus_box(self):
        
        self.modus_box = QGroupBox("Modusänderung")
        self.modus_layout = QVBoxLayout()
        
        modus_buttonlayout = QHBoxLayout()
        self.modus_group = QButtonGroup(self)
        self.modus_no = QRadioButton("Keine", self)
        self.modus_no.clicked.connect(self.toggle_bw_algo_activation)
        self.modus_gray = QRadioButton("Grau", self)
        self.modus_gray.clicked.connect(self.toggle_bw_algo_activation)
        self.modus_bw = QRadioButton("S/W", self)
        self.modus_bw.clicked.connect(self.toggle_bw_algo_activation)
        self.modus_no.setChecked(True)
        modus_buttonlayout.addWidget(self.modus_no)
        modus_buttonlayout.addWidget(self.modus_gray)
        modus_buttonlayout.addWidget(self.modus_bw)
        self.modus_group.addButton(self.modus_no)
        self.modus_group.addButton(self.modus_gray)
        self.modus_group.addButton(self.modus_bw)
        self.modus_layout.addLayout(modus_buttonlayout)
        
        self.bw_algo_select = QComboBox()
        self.bw_algo_select.addItem(SAUVOLA)
        self.bw_algo_select.addItem(FLOYD_STEINBERG)
        self.bw_algo_select.addItem(THRESHOLD)
        self.bw_algo_select.currentIndexChanged.connect(self.bw_algo_changed)
        self.modus_layout.addWidget(self.bw_algo_select)
        
        slider_box = QHBoxLayout()
        self.slider_value = QLabel("160")
        slider_box.addWidget(self.slider_value)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMaximum(255)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(20)
        self.threshold_slider.valueChanged.connect(self.slider_changed)
        self.threshold_slider.setValue(160)
        slider_box.addWidget(self.threshold_slider)
        self.modus_layout.addLayout(slider_box)
        
        self.toggle_bw_algo_activation()
        
        self.modus_box.setLayout(self.modus_layout)
        
        return self.modus_box

    # Here start the signal handler

    def toggle_bw_algo_activation(self):
        
        if self.modus_bw.isChecked():
            self.bw_algo_select.setEnabled(True)
            self.bw_algo_changed(None)
        else:
            self.bw_algo_select.setEnabled(False)
            self.threshold_slider.setEnabled(False)
            
        self._register_mode_change()
    
    def bw_algo_changed(self, value):
        
        if self.bw_algo_select.currentText() == THRESHOLD:
            self.threshold_slider.setEnabled(True)
        else:
            self.threshold_slider.setDisabled(True)
            
        self._register_mode_change()
        
    def slider_changed(self, value):
        
        self.slider_value.setText("%s" % value)
        
        self._register_mode_change()
    
    def _file_clicked(self, widgetItem):

        print("File clicked!")
        self.mode_change_active = False
        if self._is_exactly_one_row_selected():
            self.set_single_file_mode()
        else:
            self.restore_default_mode()
        self.mode_change_active = True
            
    def set_single_file_mode(self):
        
        self.single_file_mode = True
        self.modus_box.setStyleSheet("QGroupBox"
                                     "{"
                                     "background-color: red;"
                                     "}")
        
        mode_change_definition = self.job_definition.mode_change_definitions['default'] 
        selected_file_info = self._get_first_selected_file_info()
        if selected_file_info.filename in self.job_definition.mode_change_definitions:
            mode_change_definition = self.job_definition.mode_change_definitions[selected_file_info.filename]
            
        self.show_current_mode_change_definition(mode_change_definition)   
            
            
    def restore_default_mode(self):

        self.single_file_mode = False
        self.modus_box.setStyleSheet("QGroupBox"
                                     "{"
                                     "}")
        self.show_current_mode_change_definition(self.job_definition.mode_change_definitions['default'])   

    def _register_mode_change(self):
        
        
        if not self.mode_change_active:
            return
        
        current_mode_change = self.compile_mode_change()

        if self.single_file_mode:
            self.update_single_file_mode_change(current_mode_change)
        else:
            self.update_default_mode_change(current_mode_change)

    def update_single_file_mode_change(self, current_mode_change: ModeChangeDefinition):
        
        if not self._is_exactly_one_row_selected():
            raise Exception("We are not in single file mode!")
        
        selected_file = self._get_first_selected_file_info()
        default_mode_change = self.job_definition.mode_change_definitions['default']
        
        if selected_file.filename in self.job_definition.mode_change_definitions:
            if current_mode_change == default_mode_change:
                del self.job_definition.mode_change_definitions[selected_file.filename]
            else:
                self.job_definition.mode_change_definitions[selected_file.filename] = current_mode_change
            return
        
        if not default_mode_change == current_mode_change:
            self.job_definition.mode_change_definitions[selected_file.filename] = current_mode_change
            
    def update_default_mode_change(self, current_mode_change: ModeChangeDefinition):
        
        if self._is_exactly_one_row_selected():
            raise Exception("We are in single file mode!")

        self.job_definition.mode_change_definitions['default'] = current_mode_change
            

    def compile_mode_change(self):

        mode_change_definition = ModeChangeDefinition()
        mode_change_definition.modus_change = self._get_modus()
        mode_change_definition.binarization_algorithm = self.bw_algo_select.currentText()
        mode_change_definition.threshold_value = int(self.threshold_slider.value())
        return mode_change_definition

    def show_current_mode_change_definition(self, mode_change_definition: ModeChangeDefinition):
        
        self._set_modus(mode_change_definition.modus_change)
        self.threshold_slider.setValue(mode_change_definition.threshold_value)
        for idx in range(0, self.bw_algo_select.count()):
            if self.bw_algo_select.itemText(idx) == mode_change_definition.binarization_algorithm:
                self.bw_algo_select.setCurrentIndex(idx)

    def _get_denoise_widget(self):
        
        self.denoise_checkbox = QCheckBox("Flecken entfernen (sehr langsam)")
        return self.denoise_checkbox

    def _get_pdfa_widget(self):
        
        self.pdfa_checkbox = QCheckBox("Graphiken optimieren und PDF/A erstellen")
        self.pdfa_checkbox.setEnabled(self._ocrmypdf_available())
        return self.pdfa_checkbox

    def _ocrmypdf_available(self):
        '''
        This is a very crude check for ocrmypdf.
        TODO: Check for ocrmypdf somewhere in the executable path
        '''
        return exists("/usr/bin/ocrmypdf")

    def _get_ocr_widget(self):
        
        self.ocr_checkbox = QCheckBox("Texterkennung ausführen")
        return self.ocr_checkbox

    def _get_sort_box(self):
        
        sort_box = QGroupBox("Teilen und sortieren")
        sort_layout = QVBoxLayout()
        self.split_box = QCheckBox("Seiten teilen")
        self.split_box.clicked.connect(self.de_activate_splitting)
        sort_layout.addWidget(self.split_box)
        sort_group = QButtonGroup(self)
        self.sort_no = QRadioButton("Keine Sortierung", self)
        self.sort_first = QRadioButton("1. Seite ans Ende (Overheadscanner)", self)
        self.sort_sheets = QRadioButton("Nach Bögen (Einzugsscanner)", self)
        self.sort_no.setChecked(True)
        sort_layout.addWidget(self.sort_no)
        sort_layout.addWidget(self.sort_first)
        sort_layout.addWidget(self.sort_sheets)
        sort_group.addButton(self.sort_no)
        sort_group.addButton(self.sort_first)
        sort_group.addButton(self.sort_sheets)
        sort_box.setLayout(sort_layout)
        
        self.de_activate_splitting()
        
        return sort_box
    
    def de_activate_splitting(self):
        
        if self.split_box.isChecked():
            self.sort_no.setEnabled(True)
            self.sort_first.setEnabled(True)
            self.sort_sheets.setEnabled(True)
        else:
            self.sort_no.setEnabled(False)
            self.sort_first.setEnabled(False)
            self.sort_sheets.setEnabled(False)
    
    def add_task(self):
        
        job_definition = self.compile_job_definition()
        self.task_manager.add_task(job_definition)

    def append_fileinfo(self, fileinfo):
        
        self.fileinfos.append(fileinfo)
        self.file_list.setRowCount(len(self.fileinfos))
        self.display_line(len(self.fileinfos) - 1)
        
    def display_line(self, index):
        
        self.file_list.setItem(index, 0, QTableWidgetItem(self.fileinfos[index].filename))
        self.file_list.setItem(index, 1, QTableWidgetItem(self.fileinfos[index].mode))
        self.file_list.setItem(index, 2, QTableWidgetItem(self.fileinfos[index].resolution))
        self.file_list.setItem(index, 3, QTableWidgetItem(self.fileinfos[index].format))
        
    def files_up(self):
        
        selected_rows = []
        selection_model = self.file_list.selectionModel()
        for index in self.file_list.selectionModel().selectedRows():
            if index.row() == 0:
                continue
            selected_rows.append(index.row() - 1)
            self.flip_lines(index.row(), index.row() - 1)

        selection_model.clearSelection()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for row in selected_rows:
            self.file_list.selectRow(row)
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def files_down(self):
        
        selected_rows = []
        selection_model = self.file_list.selectionModel()
        indices = self.file_list.selectionModel().selectedRows()

        # Must delete in reverse order
        for index in reversed(sorted(indices)):
            if index.row() == len(self.fileinfos) - 1:
                continue
            selected_rows.append(index.row() + 1)
            self.flip_lines(index.row(), index.row() + 1)

        selection_model.clearSelection()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for row in selected_rows:
            self.file_list.selectRow(row)
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def remove_files(self):
        
        indices = self.file_list.selectionModel().selectedRows()

        # Must delete in reverse order
        for each_row in reversed(sorted(indices)):
            self.file_list.removeRow(each_row.row())
            del self.fileinfos[each_row.row()]
            
        self.restore_default_mode()
        
    def flip_lines(self, line1, line2):
        
        fileinfo1 = self.fileinfos[line1]
        self.fileinfos[line1] = self.fileinfos[line2]
        self.fileinfos[line2] = fileinfo1
        self.display_line(line1)
        self.display_line(line2)

    def add_files(self):
        
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Graphikdateien (*.jpg *.tif *.tiff *.gif *.png)")
        
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            for filename in filenames:
                self.append_fileinfo(GraphicFileInfo(filename))

    def compile_job_definition(self):

        selection_model = self.file_list.selectionModel()
        selection_model.clearSelection()        
        self._file_clicked(None)

        self.job_definition.task = self.task_select.currentText()
        self.job_definition.fileinfos = self.fileinfos.copy()
        if self.job_definition.task == TASK_COLLATE_TO_PDF:
            dialog = QFileDialog()
            dialog.setNameFilter("Pdf-Dateien (*.pdf)")
            selection = QFileDialog().getSaveFileName()
            self.job_definition.output_path = selection[0]

        self.job_definition.resolution_change = self._get_resolution()
        self.job_definition.correct_res_only = self.correct_res_only_checkbox.isChecked()
        self.job_definition.split = self.split_box.isChecked()
        self.job_definition.sort = self._get_sorting()
        if self.rotate_auto.isChecked():
            self.job_definition.rotation = 0
            self.job_definition.autorotation = True
        else:
            self.job_definition.rotation = self._get_rotation()
            self.job_definition.autorotation = False
            if self.rotate_alternating_checkbox.isChecked():
                self.job_definition.alternating_rotation = True
        
        self.job_definition.denoise = self.denoise_checkbox.isChecked()
        self.job_definition.pdfa = self.pdfa_checkbox.isChecked()
        self.job_definition.ocr = self.ocr_checkbox.isChecked()
        return deepcopy(self.job_definition)
    
    def _get_sorting(self):
        
        if self.sort_first.isChecked():
            return JobDefinition.SORT_FIRST_PAGE
        if self.sort_sheets.isChecked():
            return JobDefinition.SORT_SHEETS
        return None
    
    def _get_modus(self):
        
        if self.modus_gray.isChecked():
            return GRAYSCALE
        if self.modus_bw.isChecked():
            return BLACK_AND_WHITE
        return None
    
    def _set_modus(self, modus):
        
        if modus == GRAYSCALE:
            self.modus_gray.setChecked(True)
        elif modus == BLACK_AND_WHITE:
            self.modus_bw.setChecked(True)
        else:
            self.modus_no.setChecked(True)

    def _get_rotation(self):

        if self.rotate_0.isChecked():
            return 0
        if self.rotate_90.isChecked():
            return 90
        if self.rotate_180.isChecked():
            return 180
        if self.rotate_270.isChecked():
            return 270
    
    def _get_resolution(self):
        
        if self.resolution_300.isChecked():
            return 300
        if self.resolution_400.isChecked():
            return 400
        return None
                     
if __name__ == '__main__':
    app = QApplication(sys.argv)

    injector = Injector()
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
