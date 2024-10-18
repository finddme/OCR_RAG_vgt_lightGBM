import requests, json
from .config import model_api
from itertools import groupby

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

class LayoutType():
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
        return self.value[0]  # Returns the numerical identifier

    @property
    def __type__(self) -> str:
        return self.value[1]  # Returns the type

    @property
    def __color__(self) -> tuple[int, int, int]:
        return self.value[2]  # Returns the color

    @staticmethod
    def get_type(detection_result):
        detection_type = detection_result.get("type", "empty")
        try:
            return LayoutType[detection_type.replace(" ","_")]
        except KeyError:
            logging.warning(f"Invalid layout type {detection_type}")
            return LayoutType.Unknown

    @classmethod
    def get_bbox_info(detection_result):
        return [detection_result['left'], 
                detection_result['top'], 
                detection_result['left'] + detection_result['width'],
                detection_result['top'] + detection_result['height']]

class Layout:
    def __init__(self):
        self.records: dict[detection_results, Any] = {page_num+1: [] for page_num in range(len(detection_results))}
        self.recovery=""" """
    
    def add(self,page_number,detection_info):
        self.records[page_number].append(detection_info)
        layout_type=detection_info.get("layout").__type__
        text=detection_info.get("text")
        self.recovery += f"\n\n## [{layout_type.title()}]({text})\n\n" 

    def get_records(self):
        result = list(map(lambda item: {'page_number': item[0], 'detection_result': item[1]}, self.records.items()))
        return result

    def get_layout_infos(self,detection_results):
        for page_detection_result in detection_results:
            page_number=page_detection_result["page_number"]
            for detection_result in page_detection_result["detection_result"]:
                self.add(page_number,self.get_layout_info(detection_result))

    def get_layout_info(self,detection_result):
        bbox_info = get_bbox_info(detection_result)
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


class RUN:
    def ocr(file_path):
        print("--- PDF PROCESSING ---")
        detection_results= Detection.model_request(file_path)

        layout=Layout()
        layout.get_layout_infos(detection_results)
        result=layout.get_records()

        print("--- OCR done ---")
        return result

    def threading_ocr_process(file_path: str, start_page: int, end_page: int):
        handle = Thread(target=ocr, args=[str(file_path)])
        handle.start()
        handle.join()

    def ocr_processing(file_name,start_page, end_page):
        global final_res
        db_class_sync_check()
        pdf_path=f"./pdf_examples/{file_name}"
        # file_name=pdf_path.split("/")[-1].rstrip(".pdf")
        file_name=file_name.rstrip(".pdf")

        saved_class_list, class_name_list, file_name_list=load_weaviate_class_list()
        print("--- check DB ---")
        if file_name in file_name_list:
            class_name = list(map(lambda x: x['class'], filter(lambda x: x['file']==file_name, saved_class_list)))
            print(f"--- PDF exist, calss name: {class_name}---")
            return class_name[0]
        else:
            print(f"--- PDF not exist, OCR start---")
            threading_ocr_process(pdf_path, start_page, end_page)
            # with open(output_path, 'w', encoding='utf-8') as outfile:
            #     json.dump(final_res, outfile,indent="\t",ensure_ascii=False)
            class_name=save_weaviate(final_res,pdf_path)
            print(f"--- weaviate save complete, calss name: {class_name}---")
            return class_name