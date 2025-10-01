from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QSlider, QLineEdit, QGridLayout, QRadioButton, QButtonGroup, QComboBox)
from PyQt5.QtCore import Qt, QSize

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setGeometry(100, 100, 1200, 800)

        self.main_widget = QWidget()
        MainWindow.setCentralWidget(self.main_widget)
        main_layout = QHBoxLayout(self.main_widget)

        # Left panel for image list
        left_panel = QVBoxLayout()
        self.image_list_widget = QListWidget()
        self.image_list_widget.setFixedWidth(350)
        self.image_list_widget.setIconSize(QSize(80, 80))
        left_panel.addWidget(self.image_list_widget)
        
        import_buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("添加文件")
        self.add_folder_button = QPushButton("添加文件夹")
        import_buttons_layout.addWidget(self.add_files_button)
        import_buttons_layout.addWidget(self.add_folder_button)
        left_panel.addLayout(import_buttons_layout)

        # Center panel for image preview
        center_panel = QVBoxLayout()
        self.image_preview_label = QLabel("请拖放图片到此处，或使用按钮添加文件。")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setMinimumSize(600, 400)
        self.image_preview_label.setStyleSheet("border: 1px solid black;")
        center_panel.addWidget(self.image_preview_label)

        # Right panel for settings
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20) # Set spacing for the main right panel layout

        # Watermark and Layout Settings
        watermark_layout_group = QWidget()
        watermark_layout = QVBoxLayout(watermark_layout_group)
        watermark_layout.setAlignment(Qt.AlignTop)
        watermark_layout.setSpacing(10) # Set spacing for items within the group

        # Text watermark settings
        label_watermark_content = QLabel("水印内容")
        label_watermark_content.setStyleSheet("font-weight: bold;")
        watermark_layout.addWidget(label_watermark_content)
        self.watermark_text_input = QLineEdit("你的水印")
        self.watermark_text_input.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                padding: 8px;
            }
        """)
        watermark_layout.addWidget(self.watermark_text_input)

        font_color_layout = QHBoxLayout()
        self.font_button = QPushButton("选择字体")
        self.color_button = QPushButton("选择颜色")
        font_color_layout.addWidget(self.font_button)
        font_color_layout.addWidget(self.color_button)
        watermark_layout.addLayout(font_color_layout)

        # Layout settings
        label_layout_style = QLabel("布局与样式")
        label_layout_style.setStyleSheet("font-weight: bold; margin-top: 10px;")
        watermark_layout.addWidget(label_layout_style)
        
        # Position Mode
        pos_mode_layout = QHBoxLayout()
        self.preset_pos_radio = QRadioButton("预设位置")
        self.manual_drag_radio = QRadioButton("手动拖拽")
        self.preset_pos_radio.setChecked(True)
        pos_mode_layout.addWidget(self.preset_pos_radio)
        pos_mode_layout.addWidget(self.manual_drag_radio)
        watermark_layout.addLayout(pos_mode_layout)

        # Position dropdown
        self.position_combo = QComboBox()
        positions = ["左上", "中上", "右上",
                     "左中", "中", "右中",
                     "左下", "中下", "右下"]
        self.position_combo.addItems(positions)
        watermark_layout.addWidget(self.position_combo)

        # Opacity
        watermark_layout.addWidget(QLabel("不透明度"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(255)
        watermark_layout.addWidget(self.opacity_slider)

        # Rotation
        watermark_layout.addWidget(QLabel("旋转"))
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        watermark_layout.addWidget(self.rotation_slider)

        right_panel.addWidget(watermark_layout_group)

        # Export settings
        export_group = QWidget()
        export_layout = QVBoxLayout(export_group)
        export_layout.setAlignment(Qt.AlignTop)
        export_layout.setSpacing(10) # Set spacing for items within the group

        label_export_settings = QLabel("导出设置")
        label_export_settings.setStyleSheet("font-weight: bold;")
        export_layout.addWidget(label_export_settings)
        self.output_folder_label = QLabel("未选择输出文件夹")
        export_layout.addWidget(self.output_folder_label)
        self.select_folder_button = QPushButton("选择文件夹")
        export_layout.addWidget(self.select_folder_button)

        export_layout.addWidget(QLabel("文件命名"))
        naming_layout = QHBoxLayout()
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("前缀")
        naming_layout.addWidget(self.prefix_input)
        naming_layout.addWidget(QLabel("文件名"))
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("后缀")
        naming_layout.addWidget(self.suffix_input)
        naming_layout.addWidget(QLabel(".jpg"))
        export_layout.addLayout(naming_layout)

        self.export_button = QPushButton("全部导出")
        export_layout.addWidget(self.export_button)
        
        right_panel.addWidget(export_group)

        # Config management
        config_layout = QHBoxLayout()
        self.save_template_button = QPushButton("保存模板")
        self.load_template_button = QPushButton("加载模板")
        config_layout.addWidget(self.save_template_button)
        config_layout.addWidget(self.load_template_button)
        right_panel.addLayout(config_layout)

        # Add panels to main layout
        main_layout.addLayout(left_panel)
        main_layout.addLayout(center_panel, 1)
        main_layout.addLayout(right_panel)