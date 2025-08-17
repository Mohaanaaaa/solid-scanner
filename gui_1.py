# gui.py
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import cv2
import os

# Import the core logic from our main.py file.
# This ensures we don't duplicate code and keep the logic separate.
from main import mock_scanner, extract_reg_number, create_pdf, ASSETS_FOLDER, OUTPUT_FOLDER

class ScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Booklet Scanner Automation Tool")
        self.setGeometry(100, 100, 800, 600)
        
        self.current_booklet_images = []
        self.mock_image_paths = sorted([os.path.join(ASSETS_FOLDER, f) for f in os.listdir(ASSETS_FOLDER) if f.endswith(('jpg', 'png'))])
        self.mock_image_index = 0
        
        self.initUI()
        self.update_live_viewer()

    def initUI(self):
        main_layout = QVBoxLayout()
        
        # Live image viewer
        self.image_label = QLabel("Live image viewer through scanners")
        self.image_label.setStyleSheet("border: 2px solid black; background-color: #f0f0f0;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(780, 400)
        main_layout.addWidget(self.image_label)
        
        # Status label for user feedback
        self.status_label = QLabel("Ready to start a new booklet. Capture the first page.")
        self.status_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        
        self.capture_button = QPushButton("Click to capture")
        self.capture_button.setFixedSize(150, 40)
        self.capture_button.clicked.connect(self.capture_page)
        button_layout.addWidget(self.capture_button)
        
        self.finish_button = QPushButton("Finish to PDF")
        self.finish_button.setFixedSize(150, 40)
        self.finish_button.clicked.connect(self.finish_to_pdf)
        button_layout.addWidget(self.finish_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

    def update_live_viewer(self):
        if self.mock_image_index < len(self.mock_image_paths):
            image_path = self.mock_image_paths[self.mock_image_index]
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("Please add more images to the 'assets' folder.")
            self.capture_button.setEnabled(False)

    def capture_page(self):
        if self.mock_image_index < len(self.mock_image_paths):
            page_path = self.mock_image_paths[self.mock_image_index]
            self.current_booklet_images.append(page_path)
            self.mock_image_index += 1
            self.status_label.setText(f"Page {len(self.current_booklet_images)} captured. Ready for the next page.")
            self.update_live_viewer()
        else:
            self.status_label.setText("No more images to capture in the assets folder.")
            
    def finish_to_pdf(self):
        if not self.current_booklet_images:
            self.status_label.setText("No pages captured. Please capture at least one page.")
            return

        self.status_label.setText("Processing booklet to PDF...")
        QApplication.processEvents()

        first_page_path = self.current_booklet_images[0]
        
        # We now check the return value of extract_reg_number
        first_page_image = cv2.imread(first_page_path)
        reg_number = extract_reg_number(first_page_image)
        
        if reg_number:
            self.status_label.setText(f"Extracted Reg No: {reg_number}. Creating PDF...")
            QApplication.processEvents()
            
            # We now check the return value of create_pdf
            pdf_path = create_pdf(self.current_booklet_images, reg_number)
            
            if pdf_path:
                self.status_label.setText(f"SUCCESS: PDF saved as {os.path.basename(pdf_path)}. Ready for a new booklet.")
                self.current_booklet_images.clear()
                self.mock_image_index = 0
                self.update_live_viewer()
            else:
                self.status_label.setText(f"FAILURE: PDF creation failed for Reg No. {reg_number}.")
        else:
            self.status_label.setText("FAILURE: OCR failed. Check the `processed_reg_num.png` file in the output folder and ensure the `REG_NUM_ROI` in main.py is correct.")
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScannerApp()
    ex.show()
    sys.exit(app.exec_())