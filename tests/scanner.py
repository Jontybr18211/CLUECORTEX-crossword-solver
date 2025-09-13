import cv2
import numpy as np
import pytesseract
import re
from typing import Dict, Tuple, List, Any

# ==============================================================================
# == Function from your FIRST scanner.py file (for the grid)
# ==============================================================================

def _sort_corners(pts):
    """Sort 4 points in order: top-left, top-right, bottom-right, bottom-left."""
    pts = pts.reshape(4, 2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(4)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype='float32')

def _four_point_transform(image, pts, size=450):
    """Perform perspective transform to get a top-down, square view of the grid."""
    rect = _sort_corners(pts)
    dst = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]], dtype='float32')
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (size, size))
    return warped

def scan_crossword_image(image_path: str) -> Tuple[List[List[Dict[str, Any]]], np.ndarray]:
    """
    Scan a crossword image and return the grid structure AND the grid contour.
    """
    orig = cv2.imread(image_path)
    if orig is None:
        raise ValueError(f"Cannot read image at path: {image_path}")

    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found in image.")

    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    grid_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            grid_contour = approx
            break

    if grid_contour is None:
        raise ValueError("Could not find a 4-corner grid outline in the image.")

    warped_gray = _four_point_transform(gray, grid_contour, size=450)
    
    GRID_N = 15
    SIZE = 450
    cell_h = SIZE // GRID_N
    cell_w = SIZE // GRID_N
    grid = [[{'type': None, 'number': None} for _ in range(GRID_N)] for _ in range(GRID_N)]

    for r in range(GRID_N):
        for c in range(GRID_N):
            cell = warped_gray[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            if cell.shape[0] == 0 or cell.shape[1] == 0:
                grid[r][c] = {'type': 'black', 'number': None}
                continue
            
            _, cell_thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            white_pixels = cv2.countNonZero(cell_thresh)
            total_pixels = cell_thresh.size
            white_ratio = white_pixels / float(total_pixels) if total_pixels > 0 else 0

            cell_type = 'white' if white_ratio > 0.60 else 'black'
            number = None
            if cell_type == 'white':
                nh = max(1, int(cell.shape[0] * 0.40))
                nw = max(1, int(cell.shape[1] * 0.40))
                num_region = cell[0:nh, 0:nw]
                if num_region.size > 0:
                    _, num_thresh = cv2.threshold(num_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    if cv2.countNonZero(num_thresh) / num_thresh.size > 0.5:
                        num_thresh = cv2.bitwise_not(num_thresh)
                    
                    num_scaled = cv2.resize(num_thresh, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                    tcfg = r"--psm 10 -c tessedit_char_whitelist=0123456789"
                    try:
                        digits = pytesseract.image_to_string(num_scaled, config=tcfg).strip()
                        if digits:
                            number = int(digits)
                    except Exception:
                        pass
            grid[r][c] = {'type': cell_type, 'number': number}

    return grid, grid_contour

# ==============================================================================
# == Function from your SECOND scanner.py file (for the clues)
# ==============================================================================

def scan_clues_from_image(image_path: str, grid_contour: np.ndarray) -> Dict[str, str]:
    """
    Scans an image to find and OCR the crossword clues.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        try:
            poly = np.array(grid_contour, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(gray, [poly], color=255)
        except Exception:
            pass

        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, blockSize=15, C=9)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {}

        h_img, w_img = thresh.shape
        text_blocks = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area < (w_img * h_img * 0.001) or area > (w_img * h_img * 0.95) or w / float(h + 1e-6) > 3.0 or h < h_img * 0.05:
                continue
            text_blocks.append((x, y, w, h))

        if not text_blocks:
            return {}

        text_blocks = sorted(text_blocks, key=lambda r: r[0])
        clue_dict: Dict[str, str] = {}
        
        def ocr_and_parse(col_img):
            if col_img is None: return {}
            try:
                full_text = pytesseract.image_to_string(col_img, config="--psm 6 -l eng")
            except Exception:
                return {}
                
            results = {}
            lines = full_text.splitlines()
            for i, raw_line in enumerate(lines):
                line = raw_line.strip()
                if not line: continue
                
                m = re.match(r'^\s*(\d{1,3})\s*[\.\)\-]?\s*(.*)$', line)
                if m:
                    num, txt = m.groups()
                    if not txt: # handle multi-line clues
                        next_lines = []
                        for j in range(i + 1, len(lines)):
                            next_line = lines[j].strip()
                            if re.match(r'^\s*\d{1,3}\s*[\.\)\-]?\s*', next_line) or not next_line:
                                break
                            next_lines.append(next_line)
                        txt = ' '.join(next_lines)
                    
                    if txt and num not in results:
                        results[num] = txt.strip(' .,:;')
            return results

        identified_blocks = []
        for (x, y, w, h) in text_blocks:
            top_crop = thresh[y:y + max(20, int(h * 0.18)), x:x + w]
            try:
                quick_text = pytesseract.image_to_string(top_crop, config="--psm 6 -l eng").lower()
                if "across" in quick_text or "down" in quick_text:
                    identified_blocks.append((x, y, w, h))
            except Exception:
                continue
        
        if not identified_blocks and len(text_blocks) >= 2:
            identified_blocks = text_blocks[:2] # Fallback
        
        for (x, y, w, h) in identified_blocks:
            col_crop = thresh[y:y + h, x:x + w]
            parsed_clues = ocr_and_parse(col_crop)
            for k, v in parsed_clues.items():
                if k not in clue_dict:
                    clue_dict[k] = v
                    
        return clue_dict

    except Exception:
        return {}