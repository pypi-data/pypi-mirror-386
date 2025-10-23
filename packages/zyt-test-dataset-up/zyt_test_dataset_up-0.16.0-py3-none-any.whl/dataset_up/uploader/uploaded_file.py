import io
import os
from typing import List
from tqdm import tqdm
from requests import Response 
from dataset_up.client import Client
from dataset_up.utils.file import get_file_type_by_magic,sha256
from dataset_up.utils.concurrent_utils import error_event
from dataset_up.uploader.upload_context import lock, put_file
from dataset_up.log.logger import get_logger

logger = get_logger(__name__)

class UploadingFile(object):
    def __init__(self,client: Client,abs_path: str,rel_path: str,target_path: str,dataset_id: str,version: str,calc_sha256: bool):
        self.client = client
        self.abs_path = abs_path
        self.rel_path = rel_path
        self.target_path = target_path
        self.dataset_id :str = dataset_id
        self.version :str = version
        self.mime: str = get_file_type_by_magic(abs_path)
        self.size :int = os.path.getsize(abs_path)     
        self.upload_id :str = None
        self.part_size :int = None
        self.uploaded_part_numbers :List[int] = []
        self.uploaded_part_infos :List[dict] = []
        self.total_parts :int = None
        self.post_upload_in_progress = False
        self.tqdm = None
        self.tqdm_sha256 = None if calc_sha256 is False else tqdm(total=self.size, unit="B", unit_scale=True, desc=f'cal sha256 {self.rel_path}')
        self.sha256 :str = None if calc_sha256 is False else sha256(abs_path,self.tqdm_sha256,buf_size=1024*1024*10)

    
    
    def get_pre_upload_info(self):
        req_dict = {
            "datasetId": self.dataset_id,
            "version": self.version,
            "filePath": self.target_path,
            "fileSize": self.size,
            "sha256": self.sha256,
            "contentType": self.mime
        }
        
        self.pre_upload = self.client.pre_object_upload(req_dict)
        
        if not self.pre_upload["exists"] or self.pre_upload["resume"]:
            self.upload_id = self.pre_upload["uploadId"]
            if(len(self.pre_upload["fileParts"])) > 1:
                last_element = self.pre_upload["fileParts"].pop()
                self.pre_upload["fileParts"].insert(0, last_element)
            self.total_parts_count = len(self.pre_upload["fileParts"])
            self.part_size = self.pre_upload["partSize"]
            
            
            
            
    def upload_part(self, part_number: int):
        try:
            if self.upload_id is None:
                raise Exception("no upload id info")

            part_number_list = [filePart["partNum"] for filePart in self.pre_upload["fileParts"]]
            if part_number not in part_number_list:
                raise Exception("the part number does not exist")

            filePart = [filePart for filePart in self.pre_upload["fileParts"] if filePart["partNum"] == part_number][0]
            part_sign_url = filePart["signUrl"]
            part_size = self.pre_upload["partSize"]
            
            put_resp = Response()
            put_resp.status_code = -1
            if not error_event.is_set():
                offset = (part_number - 1) * part_size
                read_size = min(self.size - offset, part_size)
                
                with open(self.abs_path, "rb") as f:
                        f.seek(offset)
                        with io.BufferedReader(io.BytesIO(f.read(read_size))) as data:
                            logger.info(f"put file {self.abs_path} to {part_sign_url}")
                            put_resp = put_file(url=part_sign_url,size=read_size, data=data)

            if put_resp is None:
                raise Exception("failed to put file to server.")
            if put_resp.status_code != 200:
                raise Exception(
                    f"put failed, status_code = {put_resp.status_code}, text = {put_resp.text}"
                )
            self.update_progress(read_size)
            etag = put_resp.headers["Etag"]
            part_submit_dict = {"number": part_number, "etag": etag}
            
            try:
               req = {
                   "uploadId": self.upload_id,
                   "datasetId": self.dataset_id,
                   "version": self.version,
                   "filePath": self.target_path,
                   "partNumber": part_number,
                   "etag" : etag
               }
               data = self.client.report_part_uploaded(req)
               if not data["success"]: 
                   raise Exception(f"report part upload failed. Error:{data}")
               
            except Exception as e:
                logger.error(f"report part upload failed. Error:{e}")
            
            self.update_upload_info(part_num=part_number, part_info=part_submit_dict)
        except Exception as e:
            raise RuntimeError(f"put file failed. Error: {e}")    
        
    
    
    def get_post_upload_info(self):
        if not self.uploaded_part_infos or len(self.uploaded_part_infos) != len(self.pre_upload["fileParts"]):
            raise Exception("no upload task or upload does not finish")
        post_req = {
                        "datasetId":self.dataset_id, 
                        "version":self.version,
                        "filePath":self.target_path ,
                        "uploadId": self.upload_id, 
                        "partETags": self.uploaded_part_infos,
                        "sha256":self.sha256
                    }
        try:
            post_resp = self.client.post_object_upload(
                 post_req
            )
            if post_resp["success"] != True:
                raise Exception(f"file with absolute path {self.abs_path} upload failed!")
        except Exception as e:
            raise e  
    
    
    
    
    
        
    def update_upload_info(self, part_num: int, part_info: dict):
        with lock:
            self.uploaded_part_numbers.append(part_num)
            self.uploaded_part_infos.append(part_info)
    
    def init_progress(self,total_bytes_to_send):
        self.tqdm = tqdm(total=total_bytes_to_send, unit="B", unit_scale=True, desc=f'uploading {self.rel_path}')
     
    def update_progress(self, update_value: int):
        self.tqdm.update(update_value)
        
    def close_progress(self):
        self.tqdm.close()    
    
    
    
    