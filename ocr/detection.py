import requests, json
from config import model_api
from itertools import groupby
from typing import Dict
from enum import Enum
import camelot

class Color:
    Red = (255, 0, 0)
    Green = (0, 255, 0)
    Blue = (0, 0, 255)
    Yellow = (255, 255, 0)
    Cyan = (0, 255, 255)
    Magenta = (255, 0, 255)
    Purple = (128, 0, 128)
    Orange = (255, 165, 0)
    Seagreen = (46, 139, 87)
    Salmon = (250, 128, 114)
    Olive = (60, 76, 36)
    Lightpink = (255, 182, 193)

class LayoutType(Enum):
    Unknown = (0, "Footnote", Color.Red)
    Caption = (1, "Caption", Color.Purple)
    Footnote = (2, "Footnote", Color.Lightpink)
    Formula = (3, "Formula", Color.Green)
    List_item = (4, "List item", Color.Seagreen)
    Page_footer = (5, "Page footer", Color.Yellow)
    Page_header = (6, "Page header", Color.Salmon)
    Picture = (7, "Picture", Color.Magenta)
    Section_header = (8, "Section header", Color.Olive)
    Table = (9, "Table", Color.Cyan)
    Text = (10, "Text", Color.Blue)
    Title = (11, "Title", Color.Orange)

    @property
    def __number__(self) -> int:
        return self.value[0]  

    @property
    def __type__(self) -> str:
        return self.value[1]  

    @property
    def __color__(self) -> tuple[int, int, int]:
        return self.value[2]  

    @staticmethod
    def get_type(detection_result):
        detection_type = detection_result.get("type", "empty").replace(" ","_")
        try:
            # return getattr(LayoutType, detection_type)
            return LayoutType[detection_type]
        except KeyError:
            logging.warning(f"Invalid layout type {detection_type}")
            return LayoutType.Unknown

    @staticmethod
    def get_bbox_info(detection_result):
        return [detection_result['left'], 
                detection_result['top'], 
                detection_result['left'] + detection_result['width'],
                detection_result['top'] + detection_result['height']]

class Detection:
    @staticmethod
    def model_request(file_path):
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(model_api, files=files)
        result=json.loads(response.text)
        detection_results = [{'page_number': key, 'detection_result': list(group)} 
                for key, group in groupby(sorted(result, key=lambda x: x['page_number']), lambda x: x['page_number'])]
        return detection_results

    @staticmethod
    def additional_table_detection(detected_result,file_path,page_width,page_height):
        def convert_pdfplumber_to_camelot(pdfplumber_bbox, page_height):
            new_x1, new_y1, new_x2, new_y2 = pdfplumber_bbox
            
            # 좌표 변환. 스케일링 없이 단순히 y축만 반전
            x1 = new_x1
            x2 = new_x2
            y1 = page_height - new_y2
            y2 = page_height - new_y1
            
            return [x1, y1, x2, y2]

        total_res=[]
        for dr in detected_result:
            tables = camelot.read_pdf(file_path, pages=str(dr["page_number"]), backend="poppler")
            page_res={"page_number":dr["page_number"],"detection_result":[]}
            for i in dr["detection_result"]:
                if i["layout"].__type__=="Table":
                    table_check_flag=False
                    pdfplumber_bbox=i["bbox"]
                    for table in tables:
                        if table.df[0][0]!="":
                            camelot_bbox=table._bbox
                            converted_pdfplumber_bbox=convert_pdfplumber_to_camelot(pdfplumber_bbox, page_height)
                            diff= abs(int(converted_pdfplumber_bbox[0])-int(camelot_bbox[0]))

                            if diff < 3:
                                i["text"]=table.df.to_markdown(index=False)
                                table_check_flag=True
                                page_res["detection_result"].append(i)

                    if table_check_flag==False:
                        page_res["detection_result"].append(i)
                else: page_res["detection_result"].append(i)
            
                    # TODO camelot으로도 추출되지 않는 table(주로 table이 낮은 해상도의 그림으로(드래그 되지 않는) 삽입되어 있는 경우)
                    # if table_check_flag==False:
                    #     PDF_FOR_TXT_EXTRACTION_page = PDF_FOR_TXT_EXTRACTION.load_page(dr["page_number"]-1)
                    #     PDF_FOR_TXT_EXTRACTION_page.get_textbox(pdfplumber_bbox)
            
            total_res.append(page_res)
        return total_res


class Layout:
    def __init__(self,detection_results,file_path):
        self.file_path=file_path
        self.detection_results=detection_results
        self.records: dict[detection_results, Any] = {page_num+1: [] for page_num in range(len(detection_results))}
        self.recovery=""" """
        self.page_width=None
        self.page_height=None
    
    def add(self,page_number,detection_info):
        try:
            self.records[page_number].append(detection_info)
        except Exception as e: 
            self.records[page_number]=[detection_info]

        layout_type=detection_info.get("layout").__type__
        text=detection_info.get("text")
        self.recovery += f"\n\n## [{layout_type.title()}]({text})\n\n" 

    def get_records(self):
        result = list(map(lambda item: {'page_number': item[0], 'detection_result': item[1]}, self.records.items()))
        result=Detection.additional_table_detection(result,self.file_path,self.page_width,self.page_height)
        return result

    def get_layout_infos(self):
        for page_detection_result in self.detection_results:
            page_number=page_detection_result["page_number"]
            for detection_result in page_detection_result["detection_result"]:
                self.add(page_number,self.get_layout_info(detection_result))
                self.page_width=detection_result["page_width"]
                self.page_height=detection_result["page_height"]

    def get_layout_info(self,detection_result):
        bbox_info = LayoutType.get_bbox_info(detection_result)
        layout_type = LayoutType.get_type(detection_result)

        # if len(detection_result["text"])==0:
            # detections, table, img = [], None, None
            # if layout_type == LayoutType.Table:
            #     detections = get_table_markdown(line,box,pdf_page,img_height,img_width,pdf_doc)
            # elif layout_type == LayoutType.Picture:
            #     detections, table_check_flag = get_detections(line,pdf_page,box,img_height,img_width,page_number,file_path)
            #     img = line.get("img")  # Currently not in use
            # else:
            #     detections, table_check_flag = get_detections(line,pdf_page,box,img_height,img_width,page_number,file_path)
            #     if table_check_flag==True:layout_type=LayoutType.TABLE
            # return layout_type, box, detections, table, img

        return {"bbox":bbox_info,
                "page_number":detection_result["page_number"],
                "text":detection_result["text"],
                "layout":layout_type}