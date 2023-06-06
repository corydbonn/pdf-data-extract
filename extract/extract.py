from pdf2image import convert_from_path
import argparse
import cv2
import pytesseract
import numpy as np
import json
import re

# This procedure is like fancy low-pass filtering to bring large items into relief in a way that is friendly to document parsing.
def get_contours(gray_img, gaussian_blur_dims: tuple, kernel_dims: tuple):
    blur = cv2.GaussianBlur(gray_img, gaussian_blur_dims, 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_dims)
    dilate = cv2.dilate(thresh, kernel, iterations = 1)
    cntrs = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cntrs = cntrs[0] if len(cntrs) == 2 else cntrs[1]
    cntrs = sorted(cntrs, key = lambda x: cv2.boundingRect(x)[0])
    return(cntrs)

def grab_vertical_line_bounding_boxes(raw_contours):
    line_contours = [cv2.boundingRect(c) for c in raw_contours if \
                     cv2.boundingRect(c)[2] < 30 and \
                     cv2.boundingRect(c)[3] > 200 and \
                     cv2.boundingRect(c)[0] > 250]
    return(line_contours)

def grab_vertical_line_bounding_box(roi):
    raw_contours = get_contours(roi, (5,21), (11, 21))
    line_boxes = [cv2.boundingRect(c) for c in raw_contours if \
                  cv2.boundingRect(c)[2] < 30 and \
                  cv2.boundingRect(c)[3] > 200 and \
                  cv2.boundingRect(c)[0] > 300]
    line_boxes = sorted(line_boxes, key = lambda x: x[3], reverse = True)
    return(line_boxes[0])

# Helper for determining if center of narrow line contour is in 
# larger block
def point_in_contour(point, contour):
    return (
        point[0] >= contour[0] and \
        point[0] <= contour[0] + contour[2] and \
        point[1] >= contour[1] and \
        point[1] <= contour[1] + contour[3]
    )


# Helper for splitting existing wide roi if vertical line lies inside it
def split_list_item_rois_into_cols(list_item_rois):
    split_list_rois = []
    for roi in list_item_rois:
        line_coords = grab_vertical_line_bounding_box(roi)
        split_list_rois.append({
            "left": roi[:, 0:line_coords[0]],
            "right": roi[:, line_coords[0]:]
        })
    return(split_list_rois)

# For parsing names/professions using post-processing
def parse_name_list(tess_output: str):
    # Split by extracted lines and remove empties
    name_list = [nm for nm in tess_output.split("\n") if len(nm) > 0]
    # Remove category headers
    name_list = [nm for nm in name_list if not nm.isupper()]
    # If no comma in string, append to previous
    new_name_list = []
    last_item_idx = -1
    for nm in name_list:
        if last_item_idx >= 0:
            if "," in nm:
                new_name_list.append(nm)
                last_item_idx += 1
            else:
                new_name_list[last_item_idx] = new_name_list[last_item_idx] + nm
        else:
            new_name_list.append(nm)
            last_item_idx += 1
    # Separate by comma, convert to dict
    new_name_list = [{"name": nm[0], "profession": nm[1]} for nm in [n.split(", ") for n in new_name_list]]
    return(new_name_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Arguments to pass to OCR routine."
    )

    parser.add_argument(
        "--file", help="Path to PDF", required=True
    )

    parser.add_argument(
        "--start", help="Page on which excerpt starts", required=False
    )

    args = parser.parse_args()
    
    images = convert_from_path(vars(args)["file"], 500)
    
    if vars(args)["start"]:
        img_ct = int(vars(args)["start"])
    else:
        img_ct = 1

    out = []

    for img in images:
        # Detect wide text blocks
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        raw_wide_cntrs = get_contours(gray, (101, 31), (101, 31))
        wide_contours = [cv2.boundingRect(c) for c in raw_wide_cntrs if cv2.boundingRect(c)[2] > img.shape[1]/2]
        wide_rois = [img[y:y+h, x:x+w] for x,y,w,h in wide_contours]

        # Detect line breaks demarcating columns
        # Detect line breaks demarcating columns
        raw_line_cntrs = get_contours(gray, (5,21), (11, 21))
        line_contours = grab_vertical_line_bounding_boxes(raw_line_cntrs)
        
        # Calculate line contour centers, then determine which of wide blocks contains
        # list items that need parsing
        # Calculate line contour centers, then determine which of wide blocks contains
        # list items that need parsing
        line_contour_centers = [(c[0] + c[2]/2, c[1] + c[3]/2) for c in line_contours]

        list_item_contours = [wc for wc in wide_contours if any([point_in_contour(lcc, wc) for lcc in line_contour_centers])]
        paragraph_contours = [wc for wc in wide_contours if not any([point_in_contour(lcc, wc) for lcc in line_contour_centers])]

        list_item_rois = [gray[y:y+h, x:x+w] for x,y,w,h in list_item_contours]
        paragraph_rois = [gray[y:y+h, x:x+w] for x,y,w,h in paragraph_contours]
        
        # Extract text from paragraphs
        paragraph_texts = [pytesseract.image_to_string(r, lang="enm") for r in paragraph_rois]
        
        # For each list-item roi, split into two, parse with pytesseract, reconcatenate
        split_list_item_rois = split_list_item_rois_into_cols(list_item_rois)

        list_item_texts = []
        for split_roi in split_list_item_rois:
            list_item_texts.append(
                pytesseract.image_to_string(split_roi["left"], lang = "enm") + "\n" + 
                pytesseract.image_to_string(split_roi["right"], lang = "enm")
            )

        # Parse list items with post-processing
        inhabitants = [parse_name_list(nm_ls) for nm_ls in list_item_texts]
        
        parsed_data = {
            "page": img_ct,
            "text_block": paragraph_texts,
            "data": inhabitants
        }

        out.append(parsed_data)

        img_ct += 1

with open('data.json', 'w') as fp:
    json.dump(out, fp)
