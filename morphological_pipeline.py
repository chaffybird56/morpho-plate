# morphological_pipeline.py

import cv2
import numpy as np

def morphological_pipeline(roi):
    """
      1) Grayscale
      2) Blur (Gaussian)
      3) Otsu threshold
      4) Dilation (to connect text strokes)
      5) Inversion (optional, for a black-on-white effect)
    
    Returns a list of (title, image) pairs for each step.
    display them stacked vertically above the bounding box.
    """
    steps = []
    
    # Step 1: Grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    steps.append(("Gray", gray.copy()))
    
    # Step 2: Blur (reduce noise)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    steps.append(("Blur", blur.copy()))
    
    # Step 3: Otsu Threshold
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    steps.append(("Otsu", otsu.copy()))
    
    # Step 4: Dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    dilated = cv2.dilate(otsu, kernel, iterations=1)
    steps.append(("Dilate", dilated.copy()))
    
    # Step 5: Inversion
    inverted = 255 - dilated
    steps.append(("Invert", inverted.copy()))
    
    return steps
