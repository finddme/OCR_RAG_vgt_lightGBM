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

## Demo

### 표 정보 retreival

<center><img width="600" src="https://github.com/user-attachments/assets/4ba5af82-0f89-4eae-ab3f-7fd2344ade33"></center>

- Query: 2022년부터 2024년 매출액 알려줘<br>
- Response :
 ```
  문서에 따르면 삼성SDI의 매출액은 다음과 같습니다:

  2022년 매출액: 20,124 십억원
  2023년 매출액: 22,708 십억원
  2024년 예상 매출액: 18,987 십억원
```
- 참조 표
<center><img width="400" src="https://github.com/user-attachments/assets/3545c8d1-fc65-4f5e-a34f-ef419b6383ba"></center>

### 일반적인 형식이 아닌 경우

- 가로형 pdf + 그림 내부 text에 대한 retreival
  
<center><img width="600" src="https://github.com/user-attachments/assets/04d31238-aa4d-47e2-99d3-d9e35020e6df"></center>

- 형식 없는 pdf
  
<center><img width="600" src="https://github.com/user-attachments/assets/65fe6066-2238-4e19-bbea-d5775582a5e2"></center>
