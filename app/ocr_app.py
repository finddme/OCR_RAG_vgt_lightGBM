import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
# from motor.motor_asyncio import AsyncIOMotorClient
import streamlit as st
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn, os
from fastapi.middleware.cors import CORSMiddleware
from rag.ocr_rag import rag_graph
from visualise.ocr_visualisation import ocr_vis
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from ocr.run import RUN
from pydantic import BaseModel as BM

run=RUN()
app = rag_graph()

# FastAPI
fast_api_app = FastAPI(
    title="OCR"
)

origins = ["*"]

fast_api_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fast_api_app.get("/")
def home():
    return {"message": "OCR"}

class ConnectionManager:
    """Web socket connection manager."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


conn_mgr = ConnectionManager()

def return_res(res,bbox_vis):
    yield res["response"].encode("utf-8")
    for bv in bbox_vis:
        yield bv

@fast_api_app.post("/OCR")
async def api(file: UploadFile = File(...)):
    global app

    # user_input=user_input.user_input

    file_name=file.filename
    file_name="<vgt_ocr>"+file_name

    if file_name =="<vgt_ocr>input.pdf":
        input_pdf_path = os.path.join("./pdf_examples/", file_name)
        
        i = 1
        while True:
            new_filename = f"<vgt_ocr>input{i}.pdf"
            new_file_path = os.path.join("./pdf_examples/", new_filename)
            if not os.path.exists(new_file_path):
                break
            i += 1

    file_name=new_filename
    import glob
    exist_file_list = glob.glob("./pdf_examples/"+ "*.pdf")
    exist_file_list=list(map(lambda x: x.split("/")[-1], exist_file_list))
    if file_name not in exist_file_list:
        print("--- Save Input File ---")
        file_location = f"./pdf_examples/{file_name}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        with open(file_location, "wb") as f:
            content = await file.read()  
            # print(content)
            f.write(content)  

    print("--- Start OCR ---")
    with open("./file_name.txt","a") as f: f.write(file_name)
    _=run.ocr_processing(file_name)
    pages=await ocr_vis(file_name, run.final_result)

    # return StreamingResponse(return_res(res,bbox_vis), media_type="multipart/mixed; boundary=frame")

    result = {
        "response":run.final_result,
        "pages": pages,
        "texts": run.recovery
    }
    return result

    # return StreamingResponse(bbox_visualisation(file_name, res), media_type="image/png")
    # return JSONResponse(content=result)
    
    # yield json.dumps({
    #                 "response": retrieval_res["response"],
    #                 "annotations": retrieval_res["annotations"]
    #                 })
    """
    yield JSONResponse(content={
                    "response": retrieval_res["response"],
                    "annotations": retrieval_res["annotations"]
                    })
    yield StreamingResponse(bbox_visualisation(file_name, res), media_type="multipart/mixed; boundary=frame")
    """


if __name__ == '__main__':
    uvicorn.run(fast_api_app, host="0.0.0.0", port=8767)

