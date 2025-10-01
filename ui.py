from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QTabWidget, QLineEdit, QSlider, QButtonGroup, QRadioButton, QGridLayout
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
        self.settings_tabs = QTabWidget()
        
        # Watermark settings tab
        watermark_tab = QWidget()
        watermark_layout = QVBoxLayout(watermark_tab)
        self.settings_tabs.addTab(watermark_tab, "水印")
        
        # Text watermark settings
        watermark_layout.addWidget(QLabel("文字水印"))
        self.watermark_text_input = QLineEdit("你的水印")
        watermark_layout.addWidget(self.watermark_text_input)
        
        self.font_button = QPushButton("选择字体")
        watermark_layout.addWidget(self.font_button)
        
        self.color_button = QPushButton("选择颜色")
        watermark_layout.addWidget(self.color_button)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        watermark_layout.addWidget(QLabel("不透明度"))
        watermark_layout.addWidget(self.opacity_slider)

        # Image watermark (placeholder)
        watermark_layout.addWidget(QLabel("图片水印 (未实现)"))
        
        # Layout settings tab
        layout_tab = QWidget()
        layout_layout = QVBoxLayout(layout_tab)
        self.settings_tabs.addTab(layout_tab, "布局")

        # Position Mode
        layout_layout.addWidget(QLabel("位置模式"))
        self.preset_pos_radio = QRadioButton("预设位置")
        self.manual_drag_radio = QRadioButton("手动拖拽")
        layout_layout.addWidget(self.preset_pos_radio)
        layout_layout.addWidget(self.manual_drag_radio)

        # Position grid
        layout_layout.addWidget(QLabel("位置"))
        self.position_button_group = QButtonGroup(MainWindow)
        position_grid = QGridLayout()
        positions = ["左上", "中上", "右上", 
                     "左中", "中", "右中",
                     "左下", "中下", "右下"]
        for i, pos in enumerate(positions):
            btn = QPushButton(pos)
            btn.setCheckable(True)
            self.position_button_group.addButton(btn, i)
            position_grid.addWidget(btn, i // 3, i % 3)
        layout_layout.addLayout(position_grid)

        # Rotation
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        layout_layout.addWidget(QLabel("旋转"))
        layout_layout.addWidget(self.rotation_slider)

        # Export settings tab
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        self.settings_tabs.addTab(export_tab, "导出")

        export_layout.addWidget(QLabel("输出文件夹"))
        self.output_folder_label = QLabel("未选择")
        export_layout.addWidget(self.output_folder_label)
        self.select_folder_button = QPushButton("选择文件夹")
        export_layout.addWidget(self.select_folder_button)

        export_layout.addWidget(QLabel("文件命名"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("前缀")
        export_layout.addWidget(self.prefix_input)
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("后缀")
        export_layout.addWidget(self.suffix_input)
        self.naming_example_label = QLabel("示例: 前缀文件名后缀.jpg")
        export_layout.addWidget(self.naming_example_label)

        self.export_button = QPushButton("全部导出")
        export_layout.addWidget(self.export_button)

        # Config management
        config_layout = QHBoxLayout()
        self.save_template_button = QPushButton("保存模板")
        self.load_template_button = QPushButton("加载模板")
        config_layout.addWidget(self.save_template_button)
        config_layout.addWidget(self.load_template_button)
        right_panel.addLayout(config_layout)

        right_panel.addWidget(self.settings_tabs)

        # Add panels to main layout
        main_layout.addLayout(left_panel)
        main_layout.addLayout(center_panel, 1)
        main_layout.addLayout(right_panel)