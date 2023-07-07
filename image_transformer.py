# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 14:00:25 2022

@author: Admin
"""
import base64, io, IPython
from PIL import Image as PILImage
class image_transformer():
    def __init__(self):
        pass 
    def transform_img(self,images):
        
            dic=[]
        
            for image in images:
                imag = PILImage.open(image)
                output = io.BytesIO()    
                imag.save(output, format='PNG')
                encoded_string = "data:image/jpeg;base64,"+base64.b64encode(output.getvalue()).decode()
                dic.append([image,encoded_string])
                
            return dict(dic)