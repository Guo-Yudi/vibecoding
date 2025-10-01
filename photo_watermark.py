import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QListWidgetItem, QMessageBox
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen, QIcon, QFontMetrics, QTransform, QMouseEvent
)
from PyQt5.QtCore import Qt, QSettings, QPoint, QSize
from PyQt5.QtWidgets import QFontDialog, QColorDialog

from ui import Ui_MainWindow


class PhotoWatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Photo Watermark 2")
        self.setAcceptDrops(True)

        self.original_pixmap = None
        self.watermark_text = "你的水印"
        self.watermark_font = QFont("Arial", 20)
        self.watermark_color = QColor("white")
        self.watermark_opacity = 1.0
        self.watermark_position = "中"
        self.watermark_pos = QPoint(0, 0)
        self.watermark_position_mode = "预设位置"
        self.watermark_rotation = 0
        self.dragging = False
        self.drag_start_position = QPoint()

        self.output_folder = ""
        self.settings = QSettings("VibeCoding", "PhotoWatermark2")

        self.connect_signals()
        self.load_settings()
        self.update_all_ui_from_settings()

    def connect_signals(self):
        self.ui.add_files_button.clicked.connect(self.add_files)
        self.ui.add_folder_button.clicked.connect(self.add_folder)
        self.ui.image_list_widget.currentItemChanged.connect(self.on_image_list_selection_changed)
        self.ui.watermark_text_input.textChanged.connect(self.update_watermark_text)
        self.ui.font_button.clicked.connect(self.choose_font)
        self.ui.color_button.clicked.connect(self.choose_color)
        self.ui.opacity_slider.valueChanged.connect(self.set_opacity)
        self.ui.rotation_slider.valueChanged.connect(self.set_rotation)
        self.ui.select_folder_button.clicked.connect(self.select_output_folder)
        self.ui.export_button.clicked.connect(self.export_all)
        self.ui.save_template_button.clicked.connect(self.save_template)
        self.ui.load_template_button.clicked.connect(self.load_template)

        self.ui.position_button_group.buttonClicked.connect(self.set_watermark_position)

        self.ui.prefix_input.textChanged.connect(self.update_file_naming_example)
        self.ui.suffix_input.textChanged.connect(self.update_file_naming_example)

        self.ui.preset_pos_radio.toggled.connect(
            lambda checked: self.set_watermark_position_mode("预设位置") if checked else None)
        self.ui.manual_drag_radio.toggled.connect(
            lambda checked: self.set_watermark_position_mode("手动拖拽") if checked else None)

    def add_file_to_list(self, file_path):
        icon = QIcon(file_path)
        base_name = os.path.basename(file_path)
        display_name = (base_name[:20] + '...') if len(base_name) > 20 else base_name
        item = QListWidgetItem(icon, display_name)
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(base_name)
        self.ui.image_list_widget.addItem(item)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "图片文件 (*.png *.xpm *.jpg *.bmp *.tiff)")
        if files:
            list_was_empty = self.ui.image_list_widget.count() == 0
            for file in files:
                self.add_file_to_list(file)
            if list_was_empty and self.ui.image_list_widget.count() > 0:
                self.ui.image_list_widget.setCurrentRow(0)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            list_was_empty = self.ui.image_list_widget.count() == 0
            files_added = False
            for file_name in os.listdir(folder):
                if file_name.lower().endswith(('.png', '.xpm', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    self.add_file_to_list(os.path.join(folder, file_name))
                    files_added = True
            if list_was_empty and files_added:
                self.ui.image_list_widget.setCurrentRow(0)

    def on_image_list_selection_changed(self):
        selected_items = self.ui.image_list_widget.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        self.current_image_path = item.data(Qt.UserRole)
        self.original_pixmap = QPixmap(self.current_image_path)

        # Reset watermark settings to default when a new image is selected
        self.ui.watermark_text_input.setText("你的水印")
        self.watermark_text = "你的水印"
        self.watermark_position = "中"
        # Find the radio button for "中" and set it
        for button in self.ui.position_button_group.buttons():
            if button.text() == "中":
                button.setChecked(True)
                break
        self.watermark_font = QFont()  # Reset to default font
        self.watermark_font.setPointSize(36) # Set default font size
        self.watermark_color = QColor("white")
        self.watermark_opacity = 1.0
        self.watermark_rotation = 0
        self.ui.opacity_slider.setValue(255)
        self.ui.rotation_slider.setValue(0)

        if self.original_pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法加载图片。")
            self.current_image_path = None
            self.original_pixmap = None
            self.ui.image_preview_label.setText("无法加载图片")
        
        self.update_preview()

    def update_preview(self):
        if self.original_pixmap is None:
            return

        # Create a temporary pixmap for drawing
        temp_pixmap = self.original_pixmap.copy()
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw watermark
        painter.setOpacity(self.watermark_opacity)
        font_metrics = QFontMetrics(self.watermark_font)
        text_width = font_metrics.width(self.watermark_text)
        text_height = font_metrics.height()

        # Position
        if self.watermark_position_mode == "手动拖拽":
            x = self.watermark_pos.x()
            y = self.watermark_pos.y()
        else:
            if self.watermark_position == "左上":
                x = 10
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "右上":
                x = temp_pixmap.width() - text_width - 10
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "左下":
                x = 10
                y = temp_pixmap.height() - font_metrics.descent() - 10
            elif self.watermark_position == "右下":
                x = temp_pixmap.width() - text_width - 10
                y = temp_pixmap.height() - font_metrics.descent() - 10
            elif self.watermark_position == "中":
                x = (temp_pixmap.width() - text_width) / 2
                y = (temp_pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "中上":
                x = (temp_pixmap.width() - text_width) / 2
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "左中":
                x = 10
                y = (temp_pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "右中":
                x = temp_pixmap.width() - text_width - 10
                y = (temp_pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "中下":
                x = (temp_pixmap.width() - text_width) / 2
                y = temp_pixmap.height() - font_metrics.descent() - 10
            self.watermark_pos = QPoint(int(x), int(y))

        # Rotation
        if self.watermark_rotation != 0:
            transform = QTransform()
            # Create a stable rotation center
            center_x = x + text_width / 2
            center_y = y - text_height / 2
            transform.translate(center_x, center_y)
            transform.rotate(self.watermark_rotation)
            transform.translate(-center_x, -center_y)
            painter.setTransform(transform)

        painter.setFont(self.watermark_font)
        painter.setPen(QPen(self.watermark_color))
        painter.drawText(int(x), int(y), self.watermark_text)
        painter.end()

        # Scale pixmap for preview
        pixmap = temp_pixmap.scaled(self.ui.image_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Calculate scale and offset for coordinate transformation
        label_size = self.ui.image_preview_label.size()
        scaled_size = pixmap.size()
        self.pixmap_offset = QPoint((label_size.width() - scaled_size.width()) // 2, (label_size.height() - scaled_size.height()) // 2)
        if scaled_size.width() > 0:
            self.pixmap_scale = self.original_pixmap.width() / scaled_size.width()
        else:
            self.pixmap_scale = 1.0

        self.ui.image_preview_label.setPixmap(pixmap)

    def _get_original_pos(self, event_pos):
        if not self.original_pixmap or self.original_pixmap.isNull():
            return None

        label_pos = event_pos - self.ui.image_preview_label.pos()
        pixmap_pos = label_pos - self.pixmap_offset

        scaled_pixmap_rect = self.ui.image_preview_label.pixmap().rect()
        if not scaled_pixmap_rect.contains(pixmap_pos):
            return None

        original_pos_x = pixmap_pos.x() * self.pixmap_scale
        original_pos_y = pixmap_pos.y() * self.pixmap_scale
        
        return QPoint(int(original_pos_x), int(original_pos_y))

    def mousePressEvent(self, event: QMouseEvent):
        if self.watermark_position_mode != "手动拖拽":
            return

        original_pos = self._get_original_pos(event.pos())
        if original_pos is None:
            return

        font_metrics = QFontMetrics(self.watermark_font)
        # Create a rect for the text based on its baseline position
        text_rect = font_metrics.boundingRect(self.watermark_text)
        text_rect.translate(self.watermark_pos)

        if text_rect.contains(original_pos):
            self.dragging = True
            self.drag_start_position = original_pos - self.watermark_pos

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.dragging or self.watermark_position_mode != "手动拖拽":
            return

        original_pos = self._get_original_pos(event.pos())
        if original_pos is None:
            return 

        new_watermark_pos = original_pos - self.drag_start_position

        font_metrics = QFontMetrics(self.watermark_font)
        text_width = font_metrics.width(self.watermark_text)
        ascent = font_metrics.ascent()
        descent = font_metrics.descent()
        
        max_x = self.original_pixmap.width() - text_width
        max_y = self.original_pixmap.height() - descent

        new_watermark_pos.setX(max(0, min(new_watermark_pos.x(), max_x)))
        new_watermark_pos.setY(max(ascent, min(new_watermark_pos.y(), max_y)))

        self.watermark_pos = new_watermark_pos
        self.update_preview()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False

    def set_watermark_position_mode(self, text):
        self.watermark_position_mode = text
        self.update_preview()

    def set_watermark_position(self, button):
        self.watermark_position = button.text()
        self.update_preview()

    def update_watermark_text(self, text):
        self.watermark_text = text
        self.update_preview()

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.watermark_font, self)
        if ok:
            self.watermark_font = font
            self.update_preview()

    def choose_color(self):
        color = QColorDialog.getColor(self.watermark_color, self)
        if color.isValid():
            self.watermark_color = color
            self.update_preview()

    def set_opacity(self, value):
        self.watermark_opacity = value / 255.0
        self.update_preview()

    def set_rotation(self, value):
        self.watermark_rotation = value
        self.update_preview()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.ui.output_folder_label.setText(folder)

    def update_file_naming_example(self):
        prefix = self.ui.prefix_input.text()
        suffix = self.ui.suffix_input.text()
        self.file_naming_example = f"{prefix}文件名{suffix}.jpg"
        self.ui.naming_example_label.setText(self.file_naming_example)

    def export_all(self):
        if not self.output_folder:
            QMessageBox.warning(self, "警告", "请先选择输出文件夹。")
            return

        count = self.ui.image_list_widget.count()
        if count == 0:
            QMessageBox.information(self, "提示", "没有需要处理的图片。")
            return

        for i in range(count):
            item = self.ui.image_list_widget.item(i)
            self.export_image(item.data(Qt.UserRole))

        QMessageBox.information(self, "完成", f"{count} 张图片已成功导出。")

    def export_image(self, image_path):
        pixmap = QPixmap(image_path)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply watermark logic, same as in update_preview
        painter.setOpacity(self.watermark_opacity)
        font_metrics = QFontMetrics(self.watermark_font)
        text_width = font_metrics.width(self.watermark_text)
        text_height = font_metrics.height()

        # Position
        if self.watermark_position_mode == "手动拖拽":
            x = self.watermark_pos.x()
            y = self.watermark_pos.y()
        else:
            if self.watermark_position == "左上":
                x = 10
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "右上":
                x = pixmap.width() - text_width - 10
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "左下":
                x = 10
                y = pixmap.height() - font_metrics.descent() - 10
            elif self.watermark_position == "右下":
                x = pixmap.width() - text_width - 10
                y = pixmap.height() - font_metrics.descent() - 10
            elif self.watermark_position == "中":
                x = (pixmap.width() - text_width) / 2
                y = (pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "中上":
                x = (pixmap.width() - text_width) / 2
                y = font_metrics.ascent() + 10
            elif self.watermark_position == "左中":
                x = 10
                y = (pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "右中":
                x = pixmap.width() - text_width - 10
                y = (pixmap.height() + text_height) / 2 - font_metrics.descent()
            elif self.watermark_position == "中下":
                x = (pixmap.width() - text_width) / 2
                y = pixmap.height() - font_metrics.descent() - 10
            else: # Fallback
                x = 10
                y = 10

        if self.watermark_rotation != 0:
            transform = QTransform()
            center_x = x + text_width / 2
            center_y = y - text_height / 2
            transform.translate(center_x, center_y)
            transform.rotate(self.watermark_rotation)
            transform.translate(-center_x, -center_y)
            painter.setTransform(transform)

        painter.setFont(self.watermark_font)
        painter.setPen(QPen(self.watermark_color))
        painter.drawText(int(x), int(y), self.watermark_text)
        painter.end()

        # Save the file
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)
        prefix = self.ui.prefix_input.text()
        suffix = self.ui.suffix_input.text()
        new_name = f"{prefix}{name}{suffix}{ext}"
        save_path = os.path.join(self.output_folder, new_name)

        # Handle file name conflicts
        i = 1
        while os.path.exists(save_path):
            new_name = f"{prefix}{name}{suffix}({i}){ext}"
            save_path = os.path.join(self.output_folder, new_name)
            i += 1

        pixmap.save(save_path)

    def update_all_ui_from_settings(self):
        self.ui.watermark_text_input.setText(self.watermark_text)
        self.ui.opacity_slider.setValue(int(self.watermark_opacity * 255))
        self.ui.rotation_slider.setValue(self.watermark_rotation)

        if self.watermark_position_mode == "预设位置":
            self.ui.preset_pos_radio.setChecked(True)
            for button in self.ui.position_button_group.buttons():
                if button.text() == self.watermark_position:
                    button.setChecked(True)
                    break
        else:
            self.ui.manual_drag_radio.setChecked(True)

        if self.output_folder:
            self.ui.output_folder_label.setText(self.output_folder)
        
        prefix = self.settings.value("file_naming_prefix", "")
        suffix = self.settings.value("file_naming_suffix", "")
        self.ui.prefix_input.setText(prefix)
        self.ui.suffix_input.setText(suffix)
        self.update_file_naming_example()
        self.update_preview()

    def save_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存模板", "", "模板文件 (*.ini)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            self.save_settings(settings)

    def load_template(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载模板", "", "模板文件 (*.ini)")
        if file_path:
            settings = QSettings(file_path, QSettings.IniFormat)
            self.load_settings(settings)
            self.update_all_ui_from_settings()

    def save_settings(self, settings=None):
        if settings is None:
            settings = QSettings("MySoft", "PhotoWatermark2")
        
        settings.setValue("watermark_text", self.watermark_text)
        settings.setValue("watermark_font", self.watermark_font)
        settings.setValue("watermark_color", self.watermark_color)
        settings.setValue("watermark_opacity", self.watermark_opacity)
        settings.setValue("watermark_position", self.watermark_position)
        settings.setValue("watermark_position_mode", self.watermark_position_mode)
        settings.setValue("watermark_pos_x", self.watermark_pos.x())
        settings.setValue("watermark_pos_y", self.watermark_pos.y())
        settings.setValue("watermark_rotation", self.watermark_rotation)
        settings.setValue("output_folder", self.output_folder)
        settings.setValue("file_naming_prefix", self.ui.prefix_input.text())
        settings.setValue("file_naming_suffix", self.ui.suffix_input.text())

    def load_settings(self, settings=None):
        if settings is None:
            settings = QSettings("MySoft", "PhotoWatermark2")

        self.watermark_text = settings.value("watermark_text", "请输入水印文本")
        self.watermark_font = settings.value("watermark_font", QFont("Arial", 30))
        self.watermark_color = settings.value("watermark_color", QColor("white"))
        self.watermark_opacity = float(settings.value("watermark_opacity", 0.5))
        self.watermark_position = settings.value("watermark_position", "中")
        self.watermark_position_mode = settings.value("watermark_position_mode", "预设位置")
        self.watermark_pos = QPoint(
            int(settings.value("watermark_pos_x", 0)),
            int(settings.value("watermark_pos_y", 0))
        )
        self.watermark_rotation = int(settings.value("watermark_rotation", 0))
        self.output_folder = settings.value("output_folder", "")
        # Note: file_naming_prefix and file_naming_suffix are loaded in update_all_ui_from_settings

    def closeEvent(self, event):
        self.save_settings()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = PhotoWatermarkApp()
    main_win.show()
    sys.exit(app.exec_())