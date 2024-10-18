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
from visualise.retrieve_visualisation import page_to_img
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from logging_wrapper import LoggingWrapper

logger = LoggingWrapper('ayaan_logger')
logger.add_file_handler("info")
logger.add_stream_handler("error")

app = rag_graph()

# FastAPI
fast_api_app = FastAPI(
    title="OCR_RAG"
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
    return {"message": "OCR_RAG"}

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

from pydantic import BaseModel as BM
class UserInput(BM):
    user_input: str

def return_res(res,bbox_vis):
    yield res["response"].encode("utf-8")
    for bv in bbox_vis:
        yield bv

def threading_vis(self,file_name, res):
    handle = Thread(target=page_to_img, args=[file_name, res])
    handle.start()
    handle.join()


@fast_api_app.post("/OCR_RAG")
async def api(user_input: str, file: UploadFile = File(...)):
    global app

    # user_input=user_input.user_input

    file_name=file.filename
    vgt_file_name="<vgt>"+file_name

    import glob
    exist_file_list = glob.glob("./pdf_examples/"+ "*.pdf")
    exist_file_list=list(map(lambda x: x.split("/")[-1], exist_file_list))
    if vgt_file_name not in exist_file_list:
        print("--- Save Input File ---")
        file_location = f"./pdf_examples/{vgt_file_name}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        with open(file_location, "wb") as f:
            content = await file.read()  # Read the file content
            # print(content)
            f.write(content)  # Write the content to the file

    {"file_name": file_name,"question":user_input}
    inputs = {"file_name":file_name,"question": user_input}

    logger.info(f"User Input: {user_input}")

    print("--- Start Graph ---")
    res= await app.ainvoke(inputs)
    pages=await page_to_img(file_name, res)

    # return StreamingResponse(return_res(res,bbox_vis), media_type="multipart/mixed; boundary=frame")
    response= res["response"]
    result = {
        "response": response,
        "annotations": res["annotations"],
        "pages": pages
    }
    logger.info(f"Answer: {response}")
    logger.info("="*200)

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
    uvicorn.run(fast_api_app, host="0.0.0.0", port=8777)

