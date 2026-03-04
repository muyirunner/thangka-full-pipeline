# -*- coding: utf-8 -*-
import cv2

def get_image_info(image_path):
 #get the height and width of the pic
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"can not read the pic: {image_path}")
    height, width = img.shape[:2]
    return width, height

def validate_image_format(filename):

    #examine whether the form of the pic is suppored
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp']
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in supported_formats
