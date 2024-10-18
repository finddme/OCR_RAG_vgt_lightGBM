from .detection import *
from rag.db_management import (get_embedding_openai,
                        load_weaviate_class_list, 
                        save_weaviate, 
                        del_weaviate_class,
                        db_class_sync_check)
from threading import Thread, Event
import json,os,random
from collections import defaultdict

class RUN:
    def __init__(self):
        self.result = None
        self.result_ready = Event()
        self.final_result=[]
        self.recovery=""" """

    def ocr(self,file_path):
        print("--- PDF PROCESSING ---")
        detection_results= Detection.model_request(file_path)

        layout=Layout(detection_results,file_path)
        layout.get_layout_infos()
        self.result=layout.get_records()

        self.result_ready.set()

        self.recovery=""" """
        self.recovery=layout.recovery

        self.post_processing(self.result)

        self.result_ready.set()

        print("--- OCR done ---")

    def threading_ocr_process(self,file_path: str):
        handle = Thread(target=self.ocr, args=[str(file_path)])
        handle.start()
        handle.join()

    def ocr_processing(self,file_name):
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
            self.result_ready.clear()
            self.threading_ocr_process(pdf_path)
            # with open(output_path, 'w', encoding='utf-8') as outfile:
            #     json.dump(final_res, outfile,indent="\t",ensure_ascii=False)
            self.result_ready.wait()
            class_name=save_weaviate(self.final_result,pdf_path)
            print(f"--- weaviate save complete, calss name: {class_name}---")
            return class_name
    
    def post_processing(self,ocr_result):
        self.final_result, title_result, merged_results=[],[],defaultdict(lambda: {'text': '', 'info': []})

        # 기본
        for fr in ocr_result:
            title = ""
            fin_resres={"page_number":fr["page_number"],"detection_result":[]}
            for dr in fr["detection_result"]:
                if dr["layout"].__type__=="Title" or dr["layout"].__type__=="Section header":
                    title=dr['text']
                # elif dr["layout"].__type__=="Text" or dr["layout"].__type__=="Table":
                else:
                    # if len(dr["text"])>5: # text minimum length
                    dr["title"] = title
                    fin_resres["detection_result"].append(dr)
            title_result.append(fin_resres)
        
        # title 기준으로 contents 합치기
        last_title = None  
        for page in title_result:
            for result in page['detection_result']:
                title = result['title']

                if title == "":
                    title = last_title
                else:
                    last_title = title
    
                if merged_results[title]['text']:
                    merged_results[title]['text'] += '\n' + result['text']
                else:
                    merged_results[title]['text'] = result['text']
                
                merged_results[title]['info'].append({
                    "bbox": result['bbox'],
                    "page_number": result['page_number'],
                    "layout": result['layout'].value
                })
    
        for title, content in merged_results.items():
            self.final_result.append({
                "title": title,
                "text": content['text'],
                "info": content['info']
            })