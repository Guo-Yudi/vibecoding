import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QColorDialog, QFontDialog
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QPoint, QSettings

from ui import Ui_MainWindow

class PhotoWatermarkApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("照片水印工具 2")
        self.setAcceptDrops(True)

        self.current_pixmap = None
        self.watermark_text = "你的水印"
        self.watermark_font = QFont("Arial", 20)
        self.watermark_color = QColor("white")
        self.watermark_opacity = 1.0
        self.watermark_position = QPoint(10, 30)
        self.watermark_rotation = 0
        self.dragging = False
        self.drag_start_position = QPoint(0, 0)

        self.output_folder = ""
        self.settings = QSettings("VibeCoding", "PhotoWatermark2")

        self.connect_signals()
        self.load_settings()

    def connect_signals(self):
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.image_list_widget.currentItemChanged.connect(self.on_image_selected)
        self.text_input.textChanged.connect(self.update_watermark_text)
        self.font_button.clicked.connect(self.choose_font)
        self.color_button.clicked.connect(self.choose_color)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        self.rotation_slider.valueChanged.connect(self.update_rotation)
        self.select_output_button.clicked.connect(self.select_output_folder)
        self.export_button.clicked.connect(self.export_images)
        self.save_template_button.clicked.connect(self.save_template)
        self.load_template_button.clicked.connect(self.load_template)

        for pos, btn in self.pos_buttons.items():
            btn.clicked.connect(lambda checked, p=pos: self.set_watermark_position(p))

        # Mouse events for dragging
        self.preview_label.mousePressEvent = self.mouse_press_event
        self.preview_label.mouseMoveEvent = self.mouse_move_event
        self.preview_label.mouseReleaseEvent = self.mouse_release_event

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "图片文件 (*.png *.xpm *.jpg *.bmp *.tiff)")
        if files:
            self.image_list_widget.addItems(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            for f in os.listdir(folder):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    self.image_list_widget.addItem(os.path.join(folder, f))

    def on_image_selected(self, item):
        self.current_pixmap = QPixmap(item.text())
        self.update_preview()

    def update_preview(self):
        if not self.current_pixmap:
            return

        pixmap = self.current_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Apply transformations
        transform = painter.transform()
        transform.translate(self.watermark_position.x(), self.watermark_position.y())
        transform.rotate(self.watermark_rotation)
        painter.setTransform(transform)

        # Set watermark properties
        painter.setFont(self.watermark_font)
        color = QColor(self.watermark_color)
        color.setAlphaF(self.watermark_opacity)
        painter.setPen(color)
        
        # Draw text
        rect = painter.fontMetrics().boundingRect(self.watermark_text)
        painter.drawText(-rect.x(), -rect.y(), self.watermark_text)
        painter.end()
        
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_watermark_text(self, text):
        self.watermark_text = text
        self.update_preview()

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.watermark_font, self, "选择字体")
        if ok:
            self.watermark_font = font
            self.update_preview()

    def choose_color(self):
        color = QColorDialog.getColor(self.watermark_color, self, "选择颜色")
        if color.isValid():
            self.watermark_color = color
            self.update_preview()
            
    def update_opacity(self, value):
        self.watermark_opacity = value / 100.0
        self.update_preview()

    def set_watermark_position(self, position_key):
        if not self.current_pixmap:
            return

        scaled_pixmap = self.current_pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap_width = scaled_pixmap.width()
        pixmap_height = scaled_pixmap.height()
        
        font_metrics = QFontMetrics(self.watermark_font)
        text_rect = font_metrics.boundingRect(self.watermark_text)
        text_width = text_rect.width()
        text_height = text_rect.height()

        x, y = 0, 0

        # Vertical position
        if '上' in position_key:
            y = text_height
        elif '下' in position_key:
            y = pixmap_height - text_height
        elif '中' in position_key or position_key == '中':
            y = (pixmap_height + text_height) // 2

        # Horizontal position
        if '左' in position_key:
            x = 0
        elif '右' in position_key:
            x = pixmap_width - text_width
        elif '中' in position_key or position_key == '中':
            x = (pixmap_width - text_width) // 2

        self.watermark_position = QPoint(x, y)
        self.update_preview()

    def update_rotation(self, angle):
        self.watermark_rotation = angle
        self.update_preview()

    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos() - self.watermark_position

    def mouse_move_event(self, event):
        if self.dragging:
            self.watermark_position = event.pos() - self.drag_start_position
            self.update_preview()

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(folder)

    def export_images(self):
        if not self.output_folder:
            # You might want to show a message to the user
            print("请先选择输出文件夹。")
            return

        prefix = self.naming_prefix_input.text()
        suffix = self.naming_suffix_input.text()

        for i in range(self.image_list_widget.count()):
            item_path = self.image_list_widget.item(i).text()
            original_pixmap = QPixmap(item_path)
            
            # Create a pixmap with watermark
            pixmap = original_pixmap.copy()
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            transform = painter.transform()
            transform.translate(self.watermark_position.x(), self.watermark_position.y())
            transform.rotate(self.watermark_rotation)
            painter.setTransform(transform)
            painter.setFont(self.watermark_font)
            color = QColor(self.watermark_color)
            color.setAlphaF(self.watermark_opacity)
            painter.setPen(color)
            rect = painter.fontMetrics().boundingRect(self.watermark_text)
            painter.drawText(-rect.x(), -rect.y(), self.watermark_text)
            painter.end()

            # Save the file
            base_name = os.path.basename(item_path)
            name, ext = os.path.splitext(base_name)
            new_name = f"{prefix}{name}{suffix}{ext}"
            save_path = os.path.join(self.output_folder, new_name)
            pixmap.save(save_path)

    def save_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存模板", "", "配置文件 (*.ini)")
        if file_path:
            template_settings = QSettings(file_path, QSettings.IniFormat)
            self.write_settings(template_settings)

    def load_template(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载模板", "", "配置文件 (*.ini)")
        if file_path:
            template_settings = QSettings(file_path, QSettings.IniFormat)
            self.read_settings(template_settings)

    def write_settings(self, settings_obj):
        settings_obj.setValue("watermark_text", self.watermark_text)
        settings_obj.setValue("watermark_font", self.watermark_font)
        settings_obj.setValue("watermark_color", self.watermark_color)
        settings_obj.setValue("watermark_opacity", self.watermark_opacity)
        settings_obj.setValue("watermark_position", self.watermark_position)
        settings_obj.setValue("watermark_rotation", self.watermark_rotation)

    def read_settings(self, settings_obj):
        self.watermark_text = settings_obj.value("watermark_text", "你的水印")
        self.watermark_font = settings_obj.value("watermark_font", QFont("Arial", 20))
        self.watermark_color = settings_obj.value("watermark_color", QColor("white"))
        self.watermark_opacity = float(settings_obj.value("watermark_opacity", 1.0))
        self.watermark_position = settings_obj.value("watermark_position", QPoint(10, 30))
        self.watermark_rotation = int(settings_obj.value("watermark_rotation", 0))
        self.update_ui_from_settings()

    def load_settings(self):
        self.read_settings(self.settings)

    def closeEvent(self, event):
        self.write_settings(self.settings)
        event.accept()

    def update_ui_from_settings(self):
        self.text_input.setText(self.watermark_text)
        # Sliders and other UI elements would be updated here
        self.update_preview()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            files_to_add = []
            for url in event.mimeData().urls():
                file_path = str(url.toLocalFile())
                if os.path.isfile(file_path):
                    if file_path.lower().endswith(('.png', '.xpm', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        files_to_add.append(file_path)
                elif os.path.isdir(file_path):
                    for f in os.listdir(file_path):
                        full_path = os.path.join(file_path, f)
                        if os.path.isfile(full_path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                            files_to_add.append(full_path)

            if files_to_add:
                self.image_list_widget.addItems(files_to_add)
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = PhotoWatermarkApp()
    main_win.show()
    sys.exit(app.exec_())