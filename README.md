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

## improvement

- [yolo 기반 ocr-rag](https://github.com/finddme/OCR_RAG_yolo) 문제점 개선
  - 문제점 1. 일반적인 보고서/논문 형식의 pdf layout에 대한 detection 성능은 좋지만 구성이 일반적인 형식과 다른 경우 layout을 탐지하지 못함
    
    -> 해결 방법: 모델 교체
    
  - 문제점 2. 속도
    
    -> 해결 방법:<br>
        - 주요 병목 지점 확인 (pdf image 변환 부분, bounding box 그리는 부분)<br>
        - 참조한 page만 변환. <br>
        - 해상도 낮춤 DPI 조절<br>
        - PIL은 이미지 처리 속도가 느림. NumPy와 OpenCV 사용.<br>
        - ProcessPoolExecutor로 여러 페이지 병렬 처리<br>
