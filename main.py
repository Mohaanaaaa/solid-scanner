import pytesseract
import cv2
import os
from PIL import Image
import numpy as np
import logging
import datetime

# ====================================================================
# CONFIGURATION
# ====================================================================

# Specify the path to the Tesseract executable. 
# You may need to change this if Tesseract is not in your system's PATH.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Define the folder paths
ASSETS_FOLDER = 'assets/'
OUTPUT_FOLDER = 'output/'
LOG_FILE = 'scanning_log.txt'

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# DEFINE THE REGION OF INTEREST (ROI) FOR THE REGISTRATION NUMBER
# You MUST update these coordinates to match the location of the handwritten number
# on your first page image (Screenshot (8).png).
# Format: (x, y, width, height)
REG_NUM_ROI = (60, 140, 280, 40)
#REG_NUM_ROI = (10, 150, 216, 40)
# Placeholder, you must change this!

# ====================================================================
# CORE FUNCTIONS
# ====================================================================

def mock_scanner(image_path):
    """
    This function simulates a scanner by reading an image from a file.
    In a real application, this would be replaced by code that
    interfaces with a real scanner using libraries like python-twain.
    """
    if not os.path.exists(image_path):
        print(f"Error: Mock scanner failed to find image at {image_path}")
        return None
    
    print(f"Mock scanner: Capturing image from {image_path}")
    return cv2.imread(image_path)

def preprocess_image_for_ocr(image):
    """
    Pre-processes the image to make it more readable for OCR.
    This includes cropping the ROI, converting to grayscale, and thresholding.
    """
    if image is None:
        return None

    # Crop the image to the defined ROI
    x, y, w, h = REG_NUM_ROI
    if w <= 0 or h <= 0:
        print("Error: REG_NUM_ROI width or height is zero or negative. Please set valid coordinates.")
        return None
        
    cropped_image = image[y:y+h, x:x+w]

    if cropped_image.size == 0:
        print("Error: Cropped image is empty. REG_NUM_ROI coordinates might be wrong.")
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to make the numbers stand out
    # Try different values for '150' to see what works best.
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # --- DEBUGGING: Save the pre-processed image ---
    processed_image_path = os.path.join(OUTPUT_FOLDER, 'processed_reg_num.png')
    cv2.imwrite(processed_image_path, binary)
    print(f"Pre-processed image saved to: {processed_image_path}")
    # --- END DEBUGGING ---

    return binary

def extract_reg_number(image):
    """
    Uses Tesseract OCR to extract the registration number from the image.
    """
    processed_image = preprocess_image_for_ocr(image)
    if processed_image is None:
        return None

    # Use pytesseract to perform OCR on the processed image
    text = pytesseract.image_to_string(processed_image, config='--psm 6 -c tessedit_char_whitelist=0123456789')
    
    # Clean up the extracted text (remove whitespace)
    reg_number = text.strip()
    
    # Simple validation
    if not reg_number.isdigit() or len(reg_number) < 5:
        logging.warning(f"OCR failed or produced invalid result: '{reg_number}'. Manual review needed.")
        return None
    
    return reg_number

def create_pdf(image_paths, reg_number):
    """
    Combines a list of image paths into a single PDF file.
    """
    if not image_paths:
        return None

    # Load images using PIL
    images = [Image.open(p).convert('RGB') for p in image_paths]
    
    first_image = images[0]
    
    # Construct the output filename
    pdf_filename = f"{reg_number}.pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
    
    try:
        first_image.save(pdf_path, save_all=True, append_images=images[1:])
        print(f"Successfully created PDF: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

def main():
    """
    Main function to run the booklet scanning workflow.
    """
    print("Welcome to the Booklet Scanner Automation Tool.")
    print("--------------------------------------------------")
    
    # This list will hold the paths to the images for the current booklet.
    current_booklet_images = []
    
    print("\nSimulating page capture...")
    
    sample_images = sorted([os.path.join(ASSETS_FOLDER, f) for f in os.listdir(ASSETS_FOLDER) if f.endswith(('jpg', 'png'))])
    
    for i, img_path in enumerate(sample_images):
        captured_image = mock_scanner(img_path)
        if captured_image is not None:
            current_booklet_images.append(img_path)
            print(f"Page {i+1} captured successfully.")
        else:
            print(f"Failed to capture page {i+1}. Aborting booklet process.")
            current_booklet_images.clear()
            break
    
    if not current_booklet_images:
        print("No pages were captured. Exiting.")
        return
        
    print(f"\nCaptured {len(current_booklet_images)} pages for the booklet.")
    
    print("\nProcessing booklet to PDF...")
    
    first_page_image_path = current_booklet_images[0]
    first_page_image = cv2.imread(first_page_image_path)
    
    reg_number = extract_reg_number(first_page_image)
    
    if reg_number:
        print(f"Successfully extracted Registration Number: {reg_number}")
        
        pdf_path = create_pdf(current_booklet_images, reg_number)
        
        if pdf_path:
            logging.info(f"SUCCESS: Booklet with Reg No. {reg_number} processed. PDF saved to {pdf_path}")
        else:
            logging.error(f"FAILURE: PDF creation failed for Reg No. {reg_number}.")
    else:
        print("Failed to extract a valid registration number. Manual intervention required.")
        logging.error("FAILURE: OCR failed to extract a valid registration number.")
        
if __name__ == "__main__":
    main()