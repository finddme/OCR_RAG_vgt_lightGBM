# OCR_RAG_vgt_lightGBM

## model setting 

```
docker run -it -d --name ocr --gpus '"device=1"' -p 5060:5060 --entrypoint ./start.sh huridocs/pdf-document-layout-analysis:v0.0.14
```

## run api

```
cd app
python app.py
```

## run streamlit demo

```
cd app
streamlit run streamlit_fastapi.py --server.port 'port number'
```
