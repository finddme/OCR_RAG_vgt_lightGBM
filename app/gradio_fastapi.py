import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import os
import sys
import streamlit as st
import requests
import gradio as gr 
import random
import time
import glob
from pprint import pprint
import json
from visualise.ocr_visualisation import bbox_visualisation
import uvicorn
from rag.db_management import (load_weaviate_class_list, 
                        del_weaviate_class
                        )

import gradio as gr
import requests
from PIL import Image
from io import BytesIO
import io
from pyngrok import conf, ngrok
# conf.get_default().auth_token = "ak_2nPvshtTp8xNeSM4RPbMRk4jLhf"

async def process_pdf(pdf_file):
    url = "http://192.168.2.186:8767/OCR"  # FastAPI 서버 URL을 여기에 입력하세요
    files = {"file": ("input.pdf", pdf_file, "application/pdf")}
    
    response = requests.post(url, files=files)
    
    result = response.json()
    texts = result.get("texts", [])
    
    vis_res= await bbox_visualisation(result)
    
    return vis_res, texts



iface = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Upload PDF", type="binary"),
        outputs=[
        gr.Gallery(label="OCR Results"),
        gr.Textbox(label="Extracted Text", lines=100)
    ],
    title="PDF OCR",
    # timeout=300
)

http_tunnel = ngrok.connect(8986) 
tunnels = ngrok.get_tunnels() 
for kk in tunnels: 
    print(kk)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0",
                    # share=True, 
                    server_port=8986, 
                        # share_parameters={"max_threads": 100, "timeout": 60 * 5}
                        # debug=True, inline=False
                        )