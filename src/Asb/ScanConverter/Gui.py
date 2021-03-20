'''
Created on 13.02.2021

@author: michael
'''

from PyQt5.QtWidgets import QLabel, QApplication, QPushButton, QTableWidget, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QTableWidgetItem, QAbstractItemView,\
    QComboBox, QRadioButton, QButtonGroup, QGroupBox, QSlider, QCheckBox
import sys
import threading
from injector import Injector, inject, singleton
from Asb.ScanConverter.Services import FormatConversionService, GraphicFileInfo,\
    JobDefinition, GRAYSCALE, BLACK_AND_WHITE, FLOYD_STEINBERG, THRESHOLD,\
    SAUVOLA, MIXED, PdfService
from PyQt5.QtCore import Qt

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
        
        if job.task == TASK_CONVERT_JPEG:
            self.convert_to_tif(job)
        if job.task == TASK_COLLATE_TO_PDF:
            self.pdf_service.create_pdf_file(job)
        
    def convert_to_tif(self, job: JobDefinition):
        
        for info in job.fileinfos:
            img = self.format_conversion_service.load_image(info)
            img, info = self.format_conversion_service.perform_changes(img, info, job)
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
        self.task_manager = task_manager
        self.createWidgets()
        self.task_manager.message_function = self.show_job_status
        self.show_job_status()
        self.setGeometry(400, 400, 300, 300)
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
        self.file_list.setGeometry(400, 400, 300, 300)
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["Datei", "Modus", "Auflösung", "Format"])
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        return self.file_list

    def createWidgets(self):
        
        left_column = QVBoxLayout()
        left_column.addLayout(self._get_file_button_layout())
        left_column.addWidget(self._get_file_list_widget())

        right_column = QVBoxLayout()
        
        right_column.addWidget(QLabel("Aufgabe:"))
        self.task_select = QComboBox()
        self.task_select.addItem(TASK_CONVERT_JPEG)
        self.task_select.addItem(TASK_COLLATE_TO_PDF)
        right_column.addWidget(self.task_select)
        
        res_box = self._get_resolution_box()
        right_column.addWidget(res_box)
        
        rotate_box = self._get_rotate_box()
        right_column.addWidget(rotate_box)
        
        modus_box = self._get_modus_box()
        right_column.addWidget(modus_box)

        sort_box = self._get_sort_box()
        right_column.addWidget(sort_box)

        denoise_box = self._get_denoise_box()
        right_column.addWidget(denoise_box)

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
        res_layout = QHBoxLayout()
        resolution_group = QButtonGroup(self)
        self.resolution_no = QRadioButton("keine", self)
        self.resolution_300 = QRadioButton("300 dpi", self)
        self.resolution_400 = QRadioButton("400 dpi", self)
        self.resolution_no.setChecked(True)
        res_layout.addWidget(self.resolution_no)
        res_layout.addWidget(self.resolution_300)
        res_layout.addWidget(self.resolution_400)
        resolution_group.addButton(self.resolution_no)
        resolution_group.addButton(self.resolution_300)
        resolution_group.addButton(self.resolution_400)
        res_box.setLayout(res_layout)
        
        return res_box

    def _get_rotate_box(self):
                    
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
    
        return rotate_box

    def _get_modus_box(self):
        
        modus_box = QGroupBox("Modusänderung")
        modus_layout = QVBoxLayout()
        
        modus_buttonlayout = QHBoxLayout()
        modus_group = QButtonGroup(self)
        self.modus_no = QRadioButton("Keine", self)
        self.modus_no.clicked.connect(self.de_activate_bw_algo)
        self.modus_gray = QRadioButton("Grau", self)
        self.modus_gray.clicked.connect(self.de_activate_bw_algo)
        self.modus_bw = QRadioButton("S/W", self)
        self.modus_bw.clicked.connect(self.de_activate_bw_algo)
        self.modus_no.setChecked(True)
        modus_buttonlayout.addWidget(self.modus_no)
        modus_buttonlayout.addWidget(self.modus_gray)
        modus_buttonlayout.addWidget(self.modus_bw)
        modus_group.addButton(self.modus_no)
        modus_group.addButton(self.modus_gray)
        modus_group.addButton(self.modus_bw)
        modus_layout.addLayout(modus_buttonlayout)
        
        self.bw_algo_select = QComboBox()
        self.bw_algo_select.addItem(SAUVOLA)
        self.bw_algo_select.addItem(FLOYD_STEINBERG)
        self.bw_algo_select.addItem(THRESHOLD)
        self.bw_algo_select.addItem(MIXED)
        self.bw_algo_select.currentIndexChanged.connect(self.bw_algo_changed)
        modus_layout.addWidget(self.bw_algo_select)
        
        slider_box = QHBoxLayout()
        self.slider_value = QLabel("127")
        slider_box.addWidget(self.slider_value)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setValue(127)
        self.threshold_slider.setMaximum(255)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(20)
        self.threshold_slider.valueChanged.connect(lambda value: self.slider_value.setText("%s" % value))
        slider_box.addWidget(self.threshold_slider)
        modus_layout.addLayout(slider_box)
        
        self.de_activate_bw_algo()
        
        modus_box.setLayout(modus_layout)
        
        return modus_box

    def de_activate_bw_algo(self):
        
        if self.modus_bw.isChecked():
            self.bw_algo_select.setEnabled(True)
            self.bw_algo_changed(None)
        else:
            self.bw_algo_select.setEnabled(False)
            self.threshold_slider.setEnabled(False)
    
    def bw_algo_changed(self, value):
        
        if self.bw_algo_select.currentText() == THRESHOLD:
            self.threshold_slider.setEnabled(True)
        else:
            self.threshold_slider.setDisabled(True)

    def _get_denoise_box(self):
        
        denoise_box = QGroupBox("Flecken entfernen")
        denoise_layout = QVBoxLayout()
        
        self.denoise_checkbox = QCheckBox("Flecken entfernen (sehr langsam)")
        self.denoise_checkbox.clicked.connect(self.de_activate_denoise)
        denoise_layout.addWidget(self.denoise_checkbox)
        
        density_buttonlayout = QHBoxLayout()
        self.density_group = QButtonGroup(self)
        self.density_4 = QRadioButton("Kleinere Zusammenhänge", self)
        self.density_8 = QRadioButton("Größere Zusammenhänge", self)
        self.density_4.setChecked(True)
        density_buttonlayout.addWidget(self.density_4)
        density_buttonlayout.addWidget(self.density_8)
        self.density_group.addButton(self.density_8)
        self.density_group.addButton(self.density_4)
        denoise_layout.addLayout(density_buttonlayout)

        slider_box = QHBoxLayout()
        self.denoise_slider_value = QLabel("12")
        slider_box.addWidget(self.denoise_slider_value)
        self.denoise_slider = QSlider(Qt.Horizontal)
        self.denoise_slider.setValue(12)
        self.denoise_slider.setMaximum(50)
        self.denoise_slider.setMinimum(0)
        self.denoise_slider.setSingleStep(1)
        self.denoise_slider.setTickPosition(QSlider.TicksBelow)
        self.denoise_slider.setTickInterval(5)
        self.denoise_slider.valueChanged.connect(lambda value: self.denoise_slider_value.setText("%s" % value))
        slider_box.addWidget(self.denoise_slider)
        denoise_layout.addLayout(slider_box)
        
        self.de_activate_denoise()

        denoise_box.setLayout(denoise_layout)
        
        return denoise_box

    def de_activate_denoise(self):
        
        if self.denoise_checkbox.isChecked():
            self.denoise_slider.setEnabled(True)
            self.density_8.setEnabled(True)
            self.density_4.setEnabled(True)
        else:
            self.denoise_slider.setEnabled(False)
            self.density_8.setEnabled(False)
            self.density_4.setEnabled(False)

    def _get_sort_box(self):
        
        sort_box = QGroupBox("Teilen und sortieren")
        sort_layout = QVBoxLayout()
        self.split_box = QCheckBox("Seiten teilen")
        self.split_box.clicked.connect(self.de_activate_splitting)
        sort_layout.addWidget(self.split_box)
        sort_group = QButtonGroup(self)
        self.sort_no = QRadioButton("Keine Sortierung", self)
        self.sort_first = QRadioButton("1. Seite as Ende (Overheadscanner)", self)
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
        
        selection_model = self.file_list.selectionModel()
        for index in self.file_list.selectionModel().selectedRows():
            if index.row() == 0:
                continue
            self.flip_lines(index.row(), index.row() - 1)
        selection_model.clearSelection()
    
    def files_down(self):
        
        selection_model = self.file_list.selectionModel()
        for index in self.file_list.selectionModel().selectedRows():
            if index.row() == len(self.fileinfos) - 1:
                continue
            self.flip_lines(index.row(), index.row() + 1)
        selection_model.clearSelection()

    def remove_files(self):
        
        indices = self.file_list.selectionModel().selectedRows()

        # Must delete in reverse order
        for each_row in reversed(sorted(indices)):
            self.file_list.removeRow(each_row.row())
            del self.fileinfos[each_row.row()]
        
    def flip_lines(self, line1, line2):
        
        fileinfo1 = self.fileinfos[line1]
        self.fileinfos[line1] = self.fileinfos[line2]
        self.fileinfos[line2] = fileinfo1
        self.display_line(line1)
        self.display_line(line2)

    def add_files(self):
        
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Graphikdateien (*.jpg *.tif *.gif *.png)")
        
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            for filename in filenames:
                self.append_fileinfo(GraphicFileInfo(filename))

    def compile_job_definition(self):
        
        params = JobDefinition()
        params.task = self.task_select.currentText()
        params.fileinfos = self.fileinfos.copy()
        if params.task == TASK_COLLATE_TO_PDF:
            dialog = QFileDialog()
            dialog.setNameFilter("Pdf-Dateien (*.pdf)")
            selection = QFileDialog().getSaveFileName()
            params.output_path = selection[0]

        params.resolution_change = self._get_resolution()
        params.modus_change = self._get_modus()
        params.binarization_algorithm = self.bw_algo_select.currentText()
        params.threshold_value = int(self.threshold_slider.value())
        params.split = self.split_box.isChecked()
        params.sort = self._get_sorting()
        if self.rotate_auto.isChecked():
            params.rotation = 0
            params.autorotation = True
        else:
            params.rotation = self._get_rotation()
            params.autorotation = False
        params.denoise = self.denoise_checkbox.isChecked()
        params.denoise_threshold = self.denoise_slider.value()
        params.connectivity = 4
        if self.density_8.isChecked():
            params.connectivity = 8
        else:
            params.connectivity = 4
        return params
    
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
