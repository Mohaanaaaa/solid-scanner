# gui.py
import sys
import os
import cv2
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, 
    QLabel, QHBoxLayout, QInputDialog, QLineEdit,
    QComboBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Import core logic from main.py.
from main import create_pdf, ASSETS_FOLDER, OUTPUT_FOLDER

# Configure logging
LOG_FILE = 'scanning_log.txt'
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')


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
        
        # 1. Live image viewer
        self.image_label = QLabel("Live image viewer through scanners")
        self.image_label.setStyleSheet("border: 2px solid black; background-color: #f0f0f0;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(780, 400)
        main_layout.addWidget(self.image_label)
        
        # 2. Status label
        self.status_label = QLabel("Ready to start a new booklet. Capture the first page.")
        self.status_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        # 3. Horizontal layout for controls
        controls_layout = QHBoxLayout()
        
        # Dropdown for Subject Code
        subject_label = QLabel("Subject Code:")
        controls_layout.addWidget(subject_label)
        
        self.subject_combo = QComboBox()
        self.subject_combo.addItems(["81", "82", "83", "84", "85"])  # Example subject codes
        self.subject_combo.setFixedSize(80, 30)
        controls_layout.addWidget(self.subject_combo)
        
        # Add stretch to push buttons to the right
        controls_layout.addStretch(1)
        
        # "Click to capture" button
        self.capture_button = QPushButton("Click to capture")
        self.capture_button.setFixedSize(150, 40)
        self.capture_button.clicked.connect(self.capture_page)
        controls_layout.addWidget(self.capture_button)
        
        # "Finish to PDF" button
        self.finish_button = QPushButton("Finish to PDF")
        self.finish_button.setFixedSize(150, 40)
        self.finish_button.clicked.connect(self.finish_to_pdf)
        controls_layout.addWidget(self.finish_button)
        
        main_layout.addLayout(controls_layout)
        
        self.setLayout(main_layout)

    def update_live_viewer(self):
        if self.mock_image_index < len(self.mock_image_paths):
            image_path = self.mock_image_paths[self.mock_image_index]
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("Live Capture Mode: Ready to capture new pages.")
            
    def capture_page(self):
        if self.mock_image_index < len(self.mock_image_paths):
            page_path = self.mock_image_paths[self.mock_image_index]
            self.current_booklet_images.append(page_path)
            self.mock_image_index += 1
            self.status_label.setText(f"Page {len(self.current_booklet_images)} captured. Ready for the next page.")
            self.update_live_viewer()
        else:
            self.current_booklet_images.append(None)
            self.status_label.setText(f"Page {len(self.current_booklet_images)} captured. Ready for the next page.")
            self.image_label.setText("Live Capture Mode: New page captured.")
            
    def finish_to_pdf(self):
        if not self.current_booklet_images:
            self.status_label.setText("No pages captured. Please capture at least one page.")
            logging.warning("GUI: User attempted to finish with no pages captured.")
            return

        self.status_label.setText("Processing booklet. Awaiting PDF name...")
        QApplication.processEvents()
        
        reg_number, ok_pressed = QInputDialog.getText(
            self, 
            "Enter PDF Name", 
            "Please enter the Registration Number:", 
            QLineEdit.Normal
        )
        
        if ok_pressed and reg_number:
            subject_code = self.subject_combo.currentText()
            final_pdf_name = f"{reg_number}_{subject_code}"
            
            self.status_label.setText(f"Creating PDF with name: {final_pdf_name}...")
            QApplication.processEvents()
            
            actual_images = [img for img in self.current_booklet_images if img is not None]

            if not actual_images:
                self.status_label.setText("FAILURE: No valid images were captured.")
                logging.error("GUI: No valid images found to create PDF.")
                self.current_booklet_images.clear()
                self.mock_image_index = 0
                self.update_live_viewer()
                return

            pdf_path = create_pdf(actual_images, final_pdf_name)
            
            if pdf_path:
                self.status_label.setText(f"SUCCESS: PDF saved as {os.path.basename(pdf_path)}. Ready for a new booklet.")
                logging.info(f"GUI SUCCESS: Booklet processed. PDF saved to {pdf_path}")
                self.current_booklet_images.clear()
                self.mock_image_index = 0
                self.update_live_viewer()
            else:
                self.status_label.setText(f"FAILURE: PDF creation failed.")
                logging.error(f"GUI FAILURE: PDF creation failed for name {final_pdf_name}.")
        else:
            self.status_label.setText("PDF creation cancelled.")
            logging.info("GUI: PDF creation cancelled by user.")
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScannerApp()
    ex.show()
    sys.exit(app.exec_())