import os
import json
import hashlib
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from tqdm import tqdm
import requests
import signal
import threading
from dataset_down.exception.IncompleteReadException import IncompleteReadException
from dataset_down.exception.InterruptExcepiton import InterruptException
from dataset_down.exception.InterruptExcepiton import InterruptException
from dataset_down.client.AuthClient import auth_client
from dataset_down.config.constants import SERVER_URL,OPERATE_URL,DOWNLOAD_URL
from dataset_down.update.update_check import update_check
from dataset_down.utils.retryable import retry_with_backoff
from dataset_down.utils.speed_calculator import DownloadSpeedCalculator
from dataset_down.utils.system_utils import caculate_download_worker_num,get_physical_cores_count
from dataset_down.utils.file import create_empty_file
from dataset_down.log.logger import get_logger

logger = get_logger(__name__)


lock = threading.Lock()

interrupt_event = threading.Event()

base_headers = {
    "accept": "application/json",
}
headers_post_base = {
    **base_headers,
    "Content-Type": "application/json",
}

def http_authorization_header() -> dict:
        try:
            header_dict = headers_post_base
            token = auth_client.get_token()
            header_dict['Authorization'] = token
        except Exception as e:
            print("\nauth failed\n")
            logger.error(f"auth failed:{e}")
            sys.exit(-1)
        return header_dict


def signal_handler(sig, frame):
        print("\ninterrupt detected,force exit...\n")
        logger.info("interrupt detected,force exit...")
        interrupt_event.set()
        os._exit(1)

class Downloader:
    def __init__(self, dataset_id : str , source_path: str, version: str = 'master' , download_dir: str ='.', max_workers=4,limit_rate = "1M"):
        logger.info(f"worker num: {max_workers}")
        self.task_id = "default-task_id" 
        self.dataset_id = dataset_id
        self.version = version
        self.source_path = source_path
        self.download_dir = download_dir
        self.max_workers = max_workers
        self.chunk_dirs = []
        self.total_bytes = 0
        self.downloaded_bytes = 0
        self.sampling_downloaded_bytes = 0
        self.start_time = None
        self.speed_calculator = DownloadSpeedCalculator()
        self.limit_rate = self.parse_limit_rate(limit_rate)
        os.makedirs(self.download_dir, exist_ok=True)
    
    
    
    @staticmethod
    def parse_limit_rate(limit_rate):
        if limit_rate.endswith("M") or limit_rate.endswith("m"):
            return int(limit_rate[:-1]) * 1024 * 1024
        elif limit_rate.endswith("K") or limit_rate.endswith("k"):
            return int(limit_rate[:-1]) * 1024
        return 1024 * 1024
    
        
    def create_task(self):
        create_task_url = f"{SERVER_URL}{OPERATE_URL}/createTask"
        data = {
            "datasetId": self.dataset_id,
            "version": self.version,
        }
        response = requests.post(create_task_url, data=json.dumps(data), headers=http_authorization_header(), timeout=3)
        response.raise_for_status()
        if response.status_code == 200:
            ret_code = response.json()["code"]
            if ret_code == 0:
                self.task_id = response.json()["data"]["taskId"]
                if self.task_id != None and self.task_id != "":
                    print("create task success,taskId: %s" % self.task_id)
                    return
        raise Exception("create task failed")
        
    
    @retry_with_backoff(max_retries=6, base_delay=5, max_delay=20)
    def list_files(self):
        print("\nGetting download files information...\n")
        list_url = f"{SERVER_URL}{OPERATE_URL}pre_download_list"
        query_dict = { "datasetId": self.dataset_id, "version": self.version , "filePath": self.source_path}
        response = requests.post(list_url, data=json.dumps(query_dict),headers=http_authorization_header(),timeout=2600)
        response.raise_for_status()
        if response.status_code == 200:
            ret_code = response.json()['code']
            if ret_code == 0:
                objects = response.json()['data']['objects']
                files = []
                for obj in objects:
                    if obj['relPath'] is None or len(obj['relPath']) == 0:
                        continue
                    files.append(obj['relPath'])
                return files
            else:
                raise Exception(response.json()['message'])
        else:
            raise Exception(f"list error: {response.status_code},query_dict: {query_dict}")
        
    
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=5)    
    def pre_downLoad(self, file_path):
        # 如果是文件夹，则返回空
        if file_path.endswith('/'):
            return {
                "key": "",
                "relPath": file_path,
                "fileSize": 0,
                "fileParts": [],
                "sha256": "",
            }
        
        pre_download_url = f"{SERVER_URL}{DOWNLOAD_URL}preDownLoad"
        query_dict = {
            "taskId": self.task_id,
            "datasetId": self.dataset_id,
            "version": self.version,
            "filePath": file_path
        }
        response = requests.post(pre_download_url, data=json.dumps(query_dict),headers=http_authorization_header(),timeout=30)
        response.raise_for_status()
        if response.status_code == 200:
            ret_code = response.json()["code"]
            if ret_code == 0:
                data = response.json()["data"]
                return {
                    "key": data["key"],
                    "relPath": data["relPath"],
                    "fileSize": data["fileSize"],
                    "fileParts": data["fileParts"],
                    "sha256": data["sha256"],
                }
            else:
                raise Exception(f"failed to preDownLoad {file_path},ret_code:{ret_code}")
        else:
            raise Exception("failed to preDownLoad {file_path},response.status_code:{response.status_code}")
    
    
    def pre_download(self,file_paths: List):
        with ThreadPoolExecutor(max_workers=get_physical_cores_count()) as executor:
            # 提交所有预下载任务
            future_to_path = {
                executor.submit(self.pre_downLoad, file_path): file_path 
                for file_path in file_paths
            }
    
            files_info = []
            
            completed_set = set()
            total = len(future_to_path)
            
            with tqdm(total=len(file_paths), desc="Preparing",unit="file") as progress_bar: 
                while len(completed_set) < total:
                    newly_completed = []
                    for future in future_to_path.keys():
                        if future in completed_set:
                            continue
                        if future.done():
                            try:
                                file_info = future.result()
                                files_info.append(file_info)
                            except Exception as e:
                                progress_bar.set_postfix( {"fail": future_to_path[future]})
                                logger.critical(f"Error occurred while processing {future_to_path[future]}")
                                raise e
                            newly_completed.append(future)
                            
                    for future in newly_completed:
                        completed_set.add(future)
                        progress_bar.update(1)
                        progress_bar.set_postfix( {"finish": future_to_path[future]})
                        
                return files_info
        
    def download(self):
        file_paths = self.list_files()
        files_info = []
        files_info = self.pre_download(file_paths)
        self.download_folder(files_info)
        self.delete_chunks_dirs()
        print("download completed")
            
            
    def download_folder(self, files_info):
        self.total_bytes = sum(file_info['fileSize'] for file_info in files_info)
        self.downloaded_bytes = 0
        self.sampling_downloaded_bytes = 0
        self.start_time = time.time()
        
        
        """下载整个文件夹"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for file_info in files_info:
                future = executor.submit(
                    self.download_file,
                    file_info['key'],
                    file_info['relPath'],
                    file_info['fileSize'],
                    file_info['fileParts'],
                    file_info['sha256']
                )
                futures.append(future)
                
            
            
            completed_set = set()
            total = len(futures)
            desc = "total progress"
            with tqdm(total=total, desc=desc) as progress_bar:
                while len(completed_set) < total:
                    if self.is_interrupted():
                        for future in futures:
                            future.cancel()
                        executor.shutdown(wait=False)
                        raise InterruptException("error happend,please retry...")

                    newly_completed = []
                    for future in futures:
                        if future in completed_set:
                            continue
                        if future.done():
                            try:
                                future.result()  # 触发异常抛出
                            except Exception as e:
                                logger.critical(f"download failed: {e}")
                                raise e
                            newly_completed.append(future)

                    for f in newly_completed:
                        completed_set.add(f)
                        progress_bar.update(1)
                    
                    try:
                        remaining_time = 0 
                        with lock:
                            if self.downloaded_bytes > 0:
                                self.speed_calculator.add_sample(self.sampling_downloaded_bytes)
                                current_speed = self.speed_calculator.get_speed()
                                    
                                if current_speed > 0:
                                    remaining_bytes = self.total_bytes - self.downloaded_bytes
                                    remaining_time = remaining_bytes // current_speed
                                    
                                    hours = int(remaining_time // 3600)
                                    minutes = int((remaining_time % 3600) // 60)
                                    seconds = int(remaining_time % 60)
                                    eta_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                                    
                                    progress_bar.set_postfix({"speed":f"{current_speed/1024/1024:.2f} MB/s", "eta": eta_str})
                    except Exception as e:
                        pass
                       
                    time.sleep(4)  # 避免 CPU 占用过高
            

    def download_file(self, key, relative_path,file_size, file_parts, sha256):
        # 如果是文件夹，那么直接本地创建一个文件夹即可
        if relative_path.endswith('/'):
            relative_path = os.path.normpath(relative_path)
            local_file_path = os.path.join(self.download_dir, relative_path)
            with lock:
                os.makedirs(local_file_path, exist_ok=True)
            return
        
        # 获取文件大小
        if not file_size or file_size == 0:
            print(f"\nfile size for {relative_path} is invalid or zero. touch a empty file\n")
            relative_path = os.path.normpath(relative_path)
            local_file_path = os.path.join(self.download_dir, relative_path)
            with lock:
                create_empty_file(local_file_path)
            return
        
        if not file_parts or len(file_parts) == 0:
            print(f"\nfile parts for {relative_path} is invalid or empty. touch a empty file\n")
            relative_path = os.path.normpath(relative_path)
            local_file_path = os.path.join(self.download_dir, relative_path)
            with lock:
                create_empty_file(local_file_path)
            return
        
        """下载单个文件"""
        # 构建本地路径
        relative_path = os.path.normpath(relative_path)
        local_dir = os.path.join(self.download_dir, os.path.dirname(relative_path))
        local_file_path = os.path.join(self.download_dir, relative_path)
        chunk_dir = os.path.join(local_dir, '.chunks')
        with lock:
            self.chunk_dirs.append(chunk_dir)
        
        cache_dir = os.path.join(chunk_dir,  os.path.basename(relative_path) + '.cache')
        
        with lock:
            # 并发创建目录会有问题
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(chunk_dir, exist_ok=True)
            os.makedirs(cache_dir, exist_ok=True)

        
                
        if os.path.exists(local_file_path):
            if sha256 is not None and len(sha256) > 0:
                if not self.verify_sha256(local_file_path, sha256):
                    logger.critical(f"File {local_file_path} exists but SHA-256 does not match.remove it and exit")
                    with lock:
                        os.remove(local_file_path)
                        os.rmdir(cache_dir)
                    interrupt_event.set()
                    raise Exception(f"File {local_file_path} exists but SHA-256 does not match")
                else:
                    print(f"\nFile {local_file_path} exists. Skipping download.\n")
                    with lock:
                        os.rmdir(cache_dir)
                    return    
            else:
                if not self.verify_size(local_file_path, file_size):
                    logger.critical(f"Error: File {local_file_path} exists but size does not match.remove it and exit")
                    with lock:
                        os.remove(local_file_path)
                        os.rmdir(cache_dir)
                    interrupt_event.set()
                    raise Exception(f"File {local_file_path} exists but size does not match")
                else:  
                    print(f"File {local_file_path} exists. Skipping download.")
                    with lock:
                        os.rmdir(cache_dir)
                    return

        
        # 计算分片数量
        num_chunks = len(file_parts)
        
        # 检查已下载的分片
        chunks_to_download = self.check_existing_chunks(cache_dir, file_parts , num_chunks)
        
        downloaded_before = self.calculate_downloaded_bytes(cache_dir, file_parts, num_chunks)
        with lock:
            self.total_bytes = self.total_bytes - downloaded_before
        
        
        # 下载进度条
        progress_bar = tqdm(
            total=file_size,
            desc=f"downloading: {relative_path}",
            unit="B",
            unit_scale=True,
            initial=downloaded_before,
        )

        # 并发下载分片
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []
            for i in chunks_to_download:
                future = executor.submit(
                    self.download_chunk,
                    file_parts, 
                    cache_dir, 
                    i, 
                    progress_bar
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    interrupt_event.set()
                    for future in futures:
                        future.cancel()
                    executor.shutdown(wait=False)
                    progress_bar.close()
                    raise e

        progress_bar.close()

        # 合并分片
        if self.merge_chunks(cache_dir, num_chunks, local_file_path):
            # 校验SHA256
            if sha256 is not None and len(sha256) > 0:
                if self.verify_sha256(local_file_path, sha256):
                    with lock:
                    # 清理分片文件
                        self.cleanup_chunks(cache_dir)
                        os.rmdir(cache_dir)
                    logger.info(f"File {relative_path} downloaded successfully.")
                    self.post_download(relative_path)
                    return
                else:
                    logger.critical(f"SHA-256 check failed: {local_file_path}")
                    with lock:
                        os.remove(local_file_path)
                        self.cleanup_chunks(cache_dir)
                        os.rmdir(cache_dir)
                    interrupt_event.set()
                    raise Exception(f"SHA-256 check failed: {local_file_path}")
            else:
                if self.verify_size(local_file_path, file_size):
                    with lock:
                        self.cleanup_chunks(cache_dir)
                        os.rmdir(cache_dir)
                    logger.info(f"File {relative_path} downloaded successfully.")
                    self.post_download(relative_path)
                    return
                else:
                    logger.critical(f"file size check failed: {local_file_path}")
                    with lock:
                        os.remove(local_file_path)
                        self.cleanup_chunks(cache_dir)
                        os.rmdir(cache_dir)
                    interrupt_event.set()
                    raise Exception(f"file size check failed: {local_file_path}")
        else:
            pass
    
    def post_download(self,file_path: str):
        if not file_path or len(file_path) == 0:
            return
        post_download_url = f"{SERVER_URL}{DOWNLOAD_URL}postDownload"
        query_dict = {
            "taskId": self.task_id,
            "datasetId": self.dataset_id,
            "version": self.version,
            "filePath": file_path,
        }
        try:
            response = requests.post(post_download_url, data=json.dumps(query_dict),headers=http_authorization_header(),timeout=3)
            response.raise_for_status()
            if response.status_code == 200:
                code = response.json()['code']
                if code == 0:
                    data = response.json()['data']
                    result = data['success']
                    if result:
                        pass
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except Exception as e:
            pass
    
    
    
    
    def check_existing_chunks(self, cache_dir, file_parts, num_chunks):
        """检查已存在的分片"""
        existing_chunks = []
        for i in range(num_chunks):
            cur_part = file_parts[i]
            range_start = cur_part['rangeStart']
            range_end = cur_part['rangeEnd']
            expected_size = range_end - range_start + 1
            
            chunk_path = os.path.join(cache_dir, f"part_{i:03d}.tmp")
            
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) == expected_size:
                existing_chunks.append(i)
        
        return [i for i in range(num_chunks) if i not in existing_chunks]

    def calculate_downloaded_bytes(self, cache_dir, file_parts,num_chunks):
        """计算已下载字节数"""
        total = 0
        for i in range(num_chunks):
            chunk_path = os.path.join(cache_dir, f"part_{i:03d}.tmp")
            if os.path.exists(chunk_path):
                cur_part = file_parts[i]
                range_start = cur_part['rangeStart']
                range_end = cur_part['rangeEnd']
                expected_size = range_end - range_start + 1
                if expected_size == os.path.getsize(chunk_path):
                    total += os.path.getsize(chunk_path)
        return total

    @retry_with_backoff(max_retries=20, base_delay=5, max_delay=160)
    def download_chunk(self, file_parts, cache_dir, chunk_index, progress_bar):
        if self.is_interrupted():
            raise InterruptException(f"cache_dir: {cache_dir} ,download chunk index: {chunk_index} interrupted")
        
        """下载单个分片"""
        url = file_parts[chunk_index]['signUrl']
        start = file_parts[chunk_index]['rangeStart']
        end = file_parts[chunk_index]['rangeEnd']
        
        headers = {'Range': f'bytes={start}-{end}'}
        chunk_path = os.path.join(cache_dir, f"part_{chunk_index:03d}.tmp")
        downloaded_length = 0
        try:
            begin = time.time()
            with requests.get(url, headers=headers, stream=True, timeout=(600,60000)) as r:
                logger.warning(f"Downloading chunk {chunk_index} from {url}, cache dir:{cache_dir} , get cost time: {time.time()-begin}s")
                r.raise_for_status()
                expected_length = r.headers.get('Content-Length')
                with open(chunk_path, 'wb') as f:
                    start_time = time.time()
                    for chunk in r.iter_content(chunk_size=64*1024):
                        real_duration = time.time() - start_time
                        if real_duration > 0:
                            #print(f"real_duration: {real_duration}")
                            pass
                        expected_duration = float(64*1024) / (self.limit_rate / float(self.max_workers))
                        if expected_duration > real_duration:
                            time.sleep(expected_duration - real_duration)
                        
                        
                        if self.is_interrupted():
                            raise InterruptException(f"cache_dir: {cache_dir} ,download chunk index: {chunk_index} interrupted")
                        if chunk:
                            f.write(chunk)
                            downloaded_length += len(chunk)
                            progress_bar.update(len(chunk))
                            with lock:
                                self.downloaded_bytes += len(chunk)
                                self.sampling_downloaded_bytes += len(chunk)
                        start_time = time.time()
                if expected_length and int(expected_length) != downloaded_length:
                    logger.error(f"Incomplete read chunk {chunk_index} , cache dir:{cache_dir} ,cost time: {time.time()-begin}s ")
                    raise  IncompleteReadException(cache_dir,chunk_index,downloaded_length,expected_length)
            logger.warning(f"Downloaded chunk {chunk_index} successfully. cache dir:{cache_dir} cost time: {time.time()-begin}s")               
        except Exception as e:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
            with lock:
                self.downloaded_bytes -= downloaded_length
                progress_bar.update(-downloaded_length)
            raise e

    def merge_chunks(self, cache_dir, num_chunks, output_path):
        """合并分片"""
        try:
            with open(output_path, 'wb') as output_file:
                for i in range(num_chunks):
                    chunk_path = os.path.join(cache_dir, f"part_{i:03d}.tmp")
                    with open(chunk_path, 'rb') as chunk_file:
                        output_file.write(chunk_file.read())
                    os.remove(chunk_path)
            return True
        except Exception as e:
            print(f"merge chunk failed: {e}")
            interrupt_event.set()
            raise e
            

    def verify_sha256(self, file_path, expected_sha256):
        """验证SHA256"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest() == expected_sha256
        except Exception as e:
            print(f"SHA-256 check failed: {e}")
            raise e
            #return False
    
    def verify_size(self, file_path, expected_size):
        """验证文件大小"""
        return os.path.getsize(file_path) == expected_size
    

    def cleanup_chunks(self, cache_dir):
        """清理分片文件"""
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=5)
    def delete_chunks_dirs(self):
        for dir in self.chunk_dirs:
            if os.path.exists(dir) and os.path.isdir(dir) and len(os.listdir(dir)) == 0:
                os.rmdir(dir)
            

    def is_interrupted(self):
        """检查是否被中断"""
        return interrupt_event.is_set()
            






def login(ak: str, sk: str): 
    try:
        auth_client.login(ak, sk)
        update_check()
    except Exception as e:
        raise e 
    


    
            
def download(dataset_id: str, source_path: str, target_path: str,version = 'master',parallel = 1,limit_rate = "1M"):
    if not dataset_id or len(dataset_id) == 0:
        raise ValueError("dataset_id cannot be empty")
    
    if not source_path or len(source_path) == 0:
        raise ValueError("source_path cannot be empty")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    
    if not target_path:
        target_path = os.getcwd()
    if target_path.startswith('~'):
        target_path = os.path.expanduser(target_path)
    target_path = os.path.realpath(target_path)
    
    downloader = Downloader(
            dataset_id=dataset_id,
            source_path=source_path,
            version=version,
            download_dir=target_path,
            max_workers=parallel,
            limit_rate=limit_rate
            )
    
    downloader.download()
