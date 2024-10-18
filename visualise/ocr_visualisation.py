from langgraph.graph import END, StateGraph, START
from typing_extensions import TypedDict
from typing import List
from langchain_core.prompts import ChatPromptTemplate
import weaviate, os
import openai
import pdfplumber
import io, json
import base64
from io import BytesIO
import base64,io
from PIL import Image, ImageDraw

async def ocr_vis(pdf_path, ocr_res):
    pdf_path=f"./pdf_examples/{pdf_path}"
    bbox_vis=[]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            for page_detection_result in ocr_res:
                if page_num+1==page_detection_result["page_number"]:
                    im = page.to_image()
                    for detection_result in page_detection_result["detection_result"]:
                        bbox=detection_result["bbox"]
                        stroke=detection_result["layout"].__color__
                        im.draw_rect(bbox, stroke=stroke, stroke_width=2)

                    pil_image = im.original
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    png_data = img_byte_arr.getvalue() # PNG됐다

                    # PNG data to base64
                    pil_image.seek(0)
                    img_base64 = base64.b64encode(png_data).decode('utf-8')

                    bbox_vis.append(img_base64)
    return bbox_vis

async def bbox_visualisation(response):
    vis_res=[]
    for p_idx,page in enumerate(response["pages"]):
        img_data = base64.b64decode(page)
        page_img = Image.open(io.BytesIO(img_data))
        # display(page_img)
        for annotation in response["response"]:
            if annotation["page_number"]==p_idx+1:
                for a in annotation["detection_result"]:
                    bbox=a["bbox"]
                    box_color=tuple(a["layout"][2])
                    # page_img.draw_rect(bbox, stroke=box_color, stroke_width=3)
                    draw = ImageDraw.Draw(page_img)
                    draw.rectangle(bbox, outline=box_color, width = 3)
        vis_res.append(page_img)
    return vis_res