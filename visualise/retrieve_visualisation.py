from langgraph.graph import END, StateGraph, START
from typing_extensions import TypedDict
from typing import List
from langchain_core.prompts import ChatPromptTemplate
import weaviate, os
import openai
import pdfplumber
import io, json
from io import BytesIO
import base64,io
from PIL import Image, ImageDraw
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from pdf2image import convert_from_bytes
from reportlab.graphics import renderPM
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from pdf2image import convert_from_path
import asyncio
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2
import asyncio
import base64
import io
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

"""
시각화 속도 개선

병목 지점: pdf to image, bounding box 그리기
-> 해결: 참조한 page만 변환. 
-> 해상도 낮춤 DPI 조절
-> PIL은 이미지 처리 속도가 느림. NumPy와 OpenCV 사용.

+ ProcessPoolExecutor로 여러 페이지 병렬 처리
"""
def process_page(args):
    pdf_path, page_num, annotations, dpi = args
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=dpi)
    img = np.array(images[0])
    
    pdf_reader = PdfReader(pdf_path)
    pdf_page = pdf_reader.pages[page_num - 1]
    pdf_width = float(pdf_page.mediabox.width)
    pdf_height = float(pdf_page.mediabox.height)
    
    scale_x = img.shape[1] / pdf_width
    scale_y = img.shape[0] / pdf_height
    
    for info in annotations:
        if info['page_number'] == page_num:
            x0, y0, x1, y1 = map(float, info['bbox'])
            x0, y0 = int(x0 * scale_x), int(y0 * scale_y)
            x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
            r, g, b = map(int, info['layout'][2])
            cv2.rectangle(img, (x0, y0), (x1, y1), (r, g, b), 5)  
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  
    _, buffer = cv2.imencode('.png', img_rgb)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {"page_num": page_num, "page": img_base64}

async def page_to_img(pdf_path, retrieval_res, dpi=150):
    print("--- Visualization ---")
    pdf_path = f"./pdf_examples/{pdf_path}"
    
    page_nums = list(set(ra["page_number"] for ra in retrieval_res["annotations"]))
    
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                process_page,
                (pdf_path, page_num, retrieval_res["annotations"], dpi)
            )
            for page_num in page_nums
        ]
        
        pages = await asyncio.gather(*tasks)
    
    return sorted(pages, key=lambda x: x["page_num"])

# async def page_to_img(pdf_path, retrieval_res):
#     print("--- Visualization ---")
#     pdf_path=f"./pdf_examples/{pdf_path}"
#     page_num_list=[]
#     pages=[]

#     for ra in retrieval_res["annotations"]:
#         page_num_list.append(ra["page_number"])
#     page_num_list=list(dict.fromkeys(page_num_list))

#     images = convert_from_path(pdf_path)  # DPI를 300으로 설정
#     pdf_reader = PdfReader(pdf_path)

#     for page_num, img in enumerate(images, start=1):
#         if page_num in page_num_list:
#             # Get PDF page size
#             pdf_page = pdf_reader.pages[page_num - 1]
#             pdf_width = float(pdf_page.mediabox.width)
#             pdf_height = float(pdf_page.mediabox.height)

#             # Calculate scaling factor
#             scale_x = img.width / pdf_width
#             scale_y = img.height / pdf_height

#             # Create a drawing context
#             draw = ImageDraw.Draw(img)

#             # Draw bounding boxes
#             for info in retrieval_res["annotations"]:
#                 if info['page_number'] == page_num:
#                     x0, y0, x1, y1 = map(float, info['bbox'])
                    
#                     # Scale coordinates
#                     x0, y0 = x0 * scale_x, y0 * scale_y
#                     x1, y1 = x1 * scale_x, y1 * scale_y
                    
#                     r, g, b = info['layout'][2]
#                     color = (int(r), int(g), int(b))
#                     draw.rectangle([x0, y0, x1, y1], outline=color, width=5)

#                 # Convert to base64
#                 img_byte_arr = io.BytesIO()
#                 img.save(img_byte_arr, format='PNG')
#                 img_byte_arr.seek(0)
#                 img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
#             pages.append({"page_num": page_num, "page": img_base64})

#     return pages

async def bbox_visualisation(response):
    print("--- Show ---")
    vis_res=[]
    for page in response["pages"]:
        img_data = base64.b64decode(page["page"])
        page_img = Image.open(io.BytesIO(img_data))
        # display(page_img)
        for annotation in response["annotations"]:
            if annotation["page_number"]==page["page_num"]:
        #         bbox=list(map(lambda x : float(x),annotation["bbox"]))
        #         box_color=tuple(map(lambda x : int(x),annotation["layout"][2]))
        #         # page_img.draw_rect(bbox, stroke=box_color, stroke_width=3)
        #         draw = ImageDraw.Draw(page_img)
        #         draw.rectangle(bbox, outline=box_color, width = 3)
                vis_res.append(page_img)
    return vis_res

async def comprehensive_vis_process(pdf_path, retrieval_res):
    pdf_path=f"./pdf_examples/{pdf_path}"
    bboxes={}
    bbox_vis=[]
    # yield json.dumps({
    #     "response": retrieval_res["response"],
    #     "annotations": retrieval_res["annotations"]
    #     })
    for ra in retrieval_res["annotations"]:
        bbox=list(map(lambda x : float(x),ra["bbox"]))
        box_color=tuple(map(lambda x : int(x),ra["box_color"]))
        if ra["page_num"] not in list(bboxes.keys()):
            bboxes[ra["page_num"]]=[{"bbox":bbox, "box_color":box_color}]
        else:bboxes[ra["page_num"]].append({"bbox":bbox, "box_color":box_color})

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            for b_page_num,b_infos in bboxes.items():
                if page_num+1== b_page_num:
                    im = page.to_image()
                    for bi in b_infos:
                        im.draw_rect(bi["bbox"], stroke=bi["box_color"], stroke_width=1)
                    # im.save(f"./img{page_num}.png")
                    # PageImage to PNG
                    pil_image = im.original
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    png_data = img_byte_arr.getvalue() # PNG됐다

                    # PNG data to base64
                    pil_image.seek(0)
                    img_base64 = base64.b64encode(png_data).decode('utf-8')

                    bbox_vis.append(img_base64)
    return bbox_vis
