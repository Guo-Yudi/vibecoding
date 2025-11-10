import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QListWidgetItem, QMessageBox, QProgressDialog
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen, QIcon, QFontMetrics, QTransform, QMouseEvent
)
from PyQt5.QtCore import Qt, QSettings, QPoint, QSize

from ui import Ui_MainWindow


class PhotoWatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Photo Watermark 2")
        self.setAcceptDrops(True)

        # Image and Watermark Attributes
        self.current_image_path = None
        self.original_pixmap = None
        self.modified_images = set()
        self.added_files = set()
        self.watermark_text = "你的水印"
        self.watermark_font = QFont("Arial", 20)
        self.watermark_color = QColor("white")
        self.watermark_opacity = 1.0
        self.watermark_position = "中"
        self.watermark_pos = QPoint(0, 0)
        self.watermark_position_mode = "预设位置"
        self.watermark_rotation = 0
        
        # Dragging
        self.dragging = False
        self.drag_start_position = QPoint()
        self.pixmap_offset = QPoint()
        self.pixmap_scale = 1.0

        # Settings and Output
        self.output_folder = ""
        self.settings = QSettings("VibeCoding", "PhotoWatermark2")

        self.connect_signals()
        self.load_settings()
        self.update_all_ui_from_settings()

    def connect_signals(self):
        self.ui.add_files_button.clicked.connect(self.add_files)
        self.ui.add_folder_button.clicked.connect(self.add_folder)
        self.ui.image_list_widget.currentItemChanged.connect(self.on_image_list_selection_changed)
        self.ui.watermark_text_input.textChanged.connect(self.on_watermark_text_changed)
        self.ui.font_button.clicked.connect(self.select_font)
        self.ui.color_button.clicked.connect(self.select_color)
        self.ui.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.ui.rotation_slider.valueChanged.connect(self.on_rotation_changed)

        self.ui.preset_pos_radio.toggled.connect(lambda checked: self.set_watermark_position_mode("preset") if checked else None)
        self.ui.manual_drag_radio.toggled.connect(lambda checked: self.set_watermark_position_mode("manual") if checked else None)

        self.ui.position_combo.currentTextChanged.connect(self.set_watermark_position)

        self.ui.select_folder_button.clicked.connect(self.select_output_folder)
        self.ui.export_button.clicked.connect(self.save_all_images)
        self.ui.save_template_button.clicked.connect(self.save_template)
        self.ui.load_template_button.clicked.connect(self.load_template)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg)")
        if files:
            for file_path in files:
                if file_path not in self.added_files:
                    self.added_files.add(file_path)
                    item = QListWidgetItem()

                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        thumbnail = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(thumbnail))
                    
                    display_text = os.path.basename(file_path)
                    if len(display_text) > 20:
                        display_text = display_text[:20] + "..."
                    
                    item.setText(display_text)
                    item.setToolTip(file_path)
                    item.setData(Qt.UserRole, file_path)
                    self.ui.image_list_widget.addItem(item)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            for root, _, files in os.walk(folder):
                for file_name in files:
                    if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file_name)
                        if file_path not in self.added_files:
                            self.added_files.add(file_path)
                            item = QListWidgetItem()

                            pixmap = QPixmap(file_path)
                            if not pixmap.isNull():
                                thumbnail = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                item.setIcon(QIcon(thumbnail))

                            display_text = os.path.basename(file_name)
                            if len(display_text) > 20:
                                display_text = display_text[:20] + "..."

                            item.setText(display_text)
                            item.setToolTip(file_path)
                            item.setData(Qt.UserRole, file_path)
                            self.ui.image_list_widget.addItem(item)

    def _mark_current_image_as_modified(self):
        if self.current_image_path:
            self.modified_images.add(self.current_image_path)

    def on_image_list_selection_changed(self):
        current_item = self.ui.image_list_widget.currentItem()
        if not current_item:
            self.current_image_path = None
            self.original_pixmap = None
            self.update_preview()
            return

        self.current_image_path = current_item.data(Qt.UserRole)
        self.original_pixmap = QPixmap(self.current_image_path)

        if self.original_pixmap.isNull():
            QMessageBox.warning(self, "错误", f"无法加载图片: {self.current_image_path}")
            self.current_image_path = None
            self.original_pixmap = None
        
        self.update_preview()

    def on_watermark_text_changed(self, text):
        self.watermark_text = text
        self.update_watermark()
        self._mark_current_image_as_modified()

    def on_opacity_changed(self, value):
        self.watermark_opacity = value / 255.0
        self.update_watermark()
        self._mark_current_image_as_modified()

    def on_rotation_changed(self, angle):
        self.watermark_rotation = angle
        self.update_watermark()
        self._mark_current_image_as_modified()

    def select_font(self):
        font, ok = QFontDialog.getFont(self.watermark_font, self)
        if ok:
            self.watermark_font = font
            self.update_watermark()
            self._mark_current_image_as_modified()

    def select_color(self):
        color = QColorDialog.getColor(self.watermark_color, self)
        if color.isValid():
            self.watermark_color = color
            self.update_watermark()
            self._mark_current_image_as_modified()

    def set_watermark_position(self, position_text):
        self.watermark_position = position_text
        self.update_watermark()
        self._mark_current_image_as_modified()

    def save_all_images(self):
        if self.ui.image_list_widget.count() == 0:
            QMessageBox.information(self, "提示", "没有需要保存的图片。")
            return

        if not self.output_folder:
            QMessageBox.warning(self, "提示", "请先选择输出文件夹。")
            return

        prefix = self.ui.prefix_input.text()
        suffix = self.ui.suffix_input.text()

        count = self.ui.image_list_widget.count()
        progress_dialog = QProgressDialog("正在保存图片...", "取消", 0, count, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()

        for i in range(count):
            progress_dialog.setValue(i)
            if progress_dialog.wasCanceled():
                break

            item = self.ui.image_list_widget.item(i)
            original_path = item.data(Qt.UserRole)

            pixmap = QPixmap(original_path)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            self.draw_watermark_on_pixmap(painter, pixmap)
            painter.end()

            base_name = os.path.basename(original_path)
            name, ext = os.path.splitext(base_name)
            new_name = f"{prefix}{name}{suffix}{ext}"
            new_path = os.path.join(self.output_folder, new_name)
            
            if not pixmap.save(new_path):
                 QMessageBox.warning(self, "保存失败", f"无法保存文件: {new_path}")

        progress_dialog.setValue(count)
        QMessageBox.information(self, "完成", "所有图片已成功保存。")

    def draw_watermark_on_pixmap(self, painter, pixmap):
        painter.setOpacity(self.watermark_opacity)
        font_metrics = QFontMetrics(self.watermark_font)
        text_width = font_metrics.width(self.watermark_text)
        text_height = font_metrics.height()

        if self.watermark_position_mode == "manual":
            x = self.watermark_pos.x()
            y = self.watermark_pos.y()
        else:
            positions = {
                "左上": (10, font_metrics.ascent() + 10),
                "右上": (pixmap.width() - text_width - 10, font_metrics.ascent() + 10),
                "左下": (10, pixmap.height() - font_metrics.descent() - 10),
                "右下": (pixmap.width() - text_width - 10, pixmap.height() - font_metrics.descent() - 10),
                "中": ((pixmap.width() - text_width) / 2, (pixmap.height() + text_height) / 2 - font_metrics.descent()),
                "中上": ((pixmap.width() - text_width) / 2, font_metrics.ascent() + 10),
                "左中": (10, (pixmap.height() + text_height) / 2 - font_metrics.descent()),
                "右中": (pixmap.width() - text_width - 10, (pixmap.height() + text_height) / 2 - font_metrics.descent()),
                "中下": ((pixmap.width() - text_width) / 2, pixmap.height() - font_metrics.descent() - 10)
            }
            x, y = positions.get(self.watermark_position, (10, 10)) # Default to top-left
            self.watermark_pos = QPoint(int(x), int(y))

        if self.watermark_rotation != 0:
            transform = QTransform()
            center_x = self.watermark_pos.x() + text_width / 2
            center_y = self.watermark_pos.y() - text_height / 2
            transform.translate(center_x, center_y)
            transform.rotate(self.watermark_rotation)
            transform.translate(-center_x, -center_y)
            painter.setTransform(transform)

        painter.setFont(self.watermark_font)
        painter.setPen(QPen(self.watermark_color))
        painter.drawText(self.watermark_pos, self.watermark_text)

    def update_watermark(self):
        self.update_preview()

    def update_preview(self):
        if not self.current_image_path or not self.original_pixmap:
            self.ui.image_preview_label.clear()
            return

        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_watermark_on_pixmap(painter, pixmap)

        painter.end()

        scaled_pixmap = pixmap.scaled(self.ui.image_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.image_preview_label.setPixmap(scaled_pixmap)

        label_size = self.ui.image_preview_label.size()
        scaled_size = scaled_pixmap.size()
        self.pixmap_offset = QPoint((label_size.width() - scaled_size.width()) // 2, (label_size.height() - scaled_size.height()) // 2)
        if scaled_size.width() > 0:
            self.pixmap_scale = self.original_pixmap.width() / scaled_size.width()
        else:
            self.pixmap_scale = 1.0

    def _get_original_pos(self, event_pos):
        if not self.original_pixmap or self.original_pixmap.isNull():
            return None

        label_pos = self.ui.image_preview_label.mapFromGlobal(self.mapToGlobal(event_pos))
        pixmap_pos = label_pos - self.pixmap_offset

        if not self.ui.image_preview_label.pixmap() or not self.ui.image_preview_label.pixmap().rect().contains(pixmap_pos):
            return None

        original_pos_x = pixmap_pos.x() * self.pixmap_scale
        original_pos_y = pixmap_pos.y() * self.pixmap_scale
        return QPoint(int(original_pos_x), int(original_pos_y))

    def mousePressEvent(self, event: QMouseEvent):
        if self.watermark_position_mode != "manual" or not self.current_image_path:
            return

        original_pos = self._get_original_pos(event.pos())
        if original_pos is None:
            return

        font_metrics = QFontMetrics(self.watermark_font)
        text_rect = font_metrics.boundingRect(self.watermark_text)
        text_rect.translate(self.watermark_pos)

        if text_rect.contains(original_pos):
            self.dragging = True
            self.drag_start_position = original_pos - self.watermark_pos
            self._mark_current_image_as_modified()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.dragging or self.watermark_position_mode != "manual":
            return

        original_pos = self._get_original_pos(event.pos())
        if original_pos is None:
            return

        self.watermark_pos = original_pos - self.drag_start_position
        self.update_preview()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.dragging:
            self.dragging = False
            self._mark_current_image_as_modified()

    def set_watermark_position_mode(self, mode):
        self.watermark_position_mode = "manual" if mode == "manual" else "preset"
        if self.watermark_position_mode == "manual":
            self.ui.position_combo.setEnabled(False)
        else:
            self.ui.position_combo.setEnabled(True)
        self.update_watermark()
        self._mark_current_image_as_modified()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.ui.output_folder_label.setText(folder)

    def update_all_ui_from_settings(self):
        self.ui.watermark_text_input.setText(self.watermark_text)
        self.ui.opacity_slider.setValue(int(self.watermark_opacity * 255))
        self.ui.rotation_slider.setValue(self.watermark_rotation)

        if self.watermark_position_mode == "preset":
            self.ui.preset_pos_radio.setChecked(True)
            self.ui.position_combo.setCurrentText(self.watermark_position)
            self.ui.position_combo.setEnabled(True)
        else:
            self.ui.manual_drag_radio.setChecked(True)
            self.ui.position_combo.setEnabled(False)

        if self.output_folder:
            self.ui.output_folder_label.setText(self.output_folder)
        
        prefix = self.settings.value("file_naming_prefix", "")
        suffix = self.settings.value("file_naming_suffix", "")
        self.ui.prefix_input.setText(prefix)
        self.ui.suffix_input.setText(suffix)
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
            settings = self.settings
        
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
            settings = self.settings

        self.watermark_text = settings.value("watermark_text", "请输入水印文本")
        self.watermark_font = settings.value("watermark_font", QFont("Arial", 30))
        self.watermark_color = settings.value("watermark_color", QColor("white"))
        self.watermark_opacity = float(settings.value("watermark_opacity", 0.5))
        
        pos_val = settings.value("watermark_position", "中")
        if not isinstance(pos_val, str):
            pos_val = "中"
        self.watermark_position = pos_val

        self.watermark_position_mode = settings.value("watermark_position_mode", "预设位置")
        self.watermark_pos = QPoint(
            int(settings.value("watermark_pos_x", 0)),
            int(settings.value("watermark_pos_y", 0))
        )
        self.watermark_rotation = int(settings.value("watermark_rotation", 0))
        self.output_folder = settings.value("output_folder", "")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = PhotoWatermarkApp()
    main_win.show()
    sys.exit(app.exec_())