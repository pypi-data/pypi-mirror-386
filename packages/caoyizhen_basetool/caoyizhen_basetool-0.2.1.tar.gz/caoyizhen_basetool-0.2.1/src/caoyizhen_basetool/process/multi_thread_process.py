# -*- encoding: utf-8 -*-
# @Time    :   2025/10/11 22:16:26
# @File    :   MultiThreadProcess.py
# @Author  :   ciaoyizhen
# @Contact :   yizhen.ciao@gmail.com
# @Function:   多线程的消费者生产者进程处理

from pathlib import Path
from concurrent.futures import as_completed, ThreadPoolExecutor
from ..utils import LoggerManager
from ..file import save_file, read_file

try:
    from tqdm import tqdm
except ImportError:
    # tqdm 没装时，定义一个假的 tqdm 占位符
    def tqdm(iterable=None, *args, **kwargs):
        return iterable if iterable is not None else []



class BaseMultiThreading():
    """
    基类, 实现多线程的消费者生产者的处理, 实现边处理边存储
    """
    def __init__(self, max_workers:int, save_temp_dir:str|Path, single_file_size, finally_save_path: str|Path=None, *, file_type:str|Path=None):
        """_summary_

        Args:
            max_workers (int): 并发数
            save_temp_dir (str|Path): 临时存储文件夹
            single_file_size (int): 临时存储时，单个文件的大小
            finally_save_path (str|Path): 最终完整保存的文件
            file_type (str|Path): 文件存储类型
        """
        self.max_workers = max_workers
        self.single_file_size = single_file_size
        self.save_temp_dir = save_temp_dir
        self.finally_save_path = finally_save_path
        self.file_type = file_type
        
        if not isinstance(self.save_temp_dir, Path):
            self.save_temp_dir = Path(self.save_temp_dir)

        if self.save_temp_dir.exists():
            raise RuntimeError("临时存储目录已经存在,请先确认是否可删除,若不可删除,请更换目录,若可删除,请手动删除")
        self.save_temp_dir.mkdir(parents=True)

        if (finally_save_path is not None) and (not isinstance(finally_save_path, Path)):
            finally_save_path = Path(finally_save_path)
        if finally_save_path is not None and finally_save_path.exists():
            raise RuntimeError("最终存储文件位置已经存在,请先确认是否可删除,若不可删除,请更换存储位置,若可删除,请手动删除")

        self.file_count = 0  # 文件计数
        
        if self.file_type is None:
            # 如果没有传file_type,就根据finally_save_path的后缀判断
            if finally_save_path is None:
                raise RuntimeError(f"没有传入file_type 以及finally_save_path, 无法推断你需要保存的数据样式")
            else:
                self.file_type = finally_save_path.suffix.lstrip(".")
            
        if self.file_type not in {"json", "jsonl", "xlsx", "csv"}:
            raise RuntimeError(f"传入的file_type不符合要求或你的文件后缀不符合要求")

        self.logger = LoggerManager()
            
    def single_data_process(self):
        """
        这个函数实现单个数据怎么处理，输入是一个数据，进行处理，返回一个数据
        需要用户自定义实现
        """
        raise NotImplementedError(f"未实现函数 single_data_process, 该函数需要解决每个数据要怎么")
    
    def _merge_data(self):
        """
        将临时存储的数据合起来，放到最终存储的位置
        """
        if self.finally_save_path is not None:
            total_data = []
            for file in self.save_temp_dir.iterdir():
                data = read_file(file, disable_tqdm=True)
                total_data.extend(data)
                
            save_file(self.finally_save_path, total_data)
            self.logger.info(f"全部数据成功存储于{self.finally_save_path}")
            
    
    def __call__(self, data:list):
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="线程处理数据") as exec, \
            tqdm(total=len(data), desc=f"{self.max_workers}并发处理中") as p_bar:
            try:
                futures_list = []
                for item in data:
                    future = exec.submit(self.single_data_process, item)
                    future.add_done_callback(lambda x: p_bar.update(1))
                    futures_list.append(future)
                
                processed_data = []  # 存储处理好的数据
                for future in as_completed(futures_list):
                    result = future.result()
                    processed_data.append(result)
                    if len(processed_data) == self.single_file_size:
                        temp_file_path = self.save_temp_dir / f"{self.file_count*self.single_file_size}_{(self.file_count+1)*self.single_file_size}.{self.file_type}"
                        save_file(temp_file_path, processed_data)
                        
                        processed_data.clear()
                        self.file_count += 1
                        self.logger.info(f"文件存储成功,已保存至{temp_file_path}")
                        
                if processed_data:
                    # 保存最后的数据
                    temp_file_path = self.save_temp_dir / f"{self.file_count*self.single_file_size}_{(self.file_count+1)*self.single_file_size}.{self.file_type}"
                    save_file(temp_file_path, processed_data)
            except KeyboardInterrupt:
                self.logger.info("用户中断代码,尝试保存当前剩余的数据,请不要进行任何操作")
                exec.shutdown(cancel_futures=True)
                temp_file_path = self.save_temp_dir / f"{self.file_count*self.single_file_size}_{(self.file_count+1)*self.single_file_size}.{self.file_type}"
                save_file(temp_file_path, processed_data)
            except:
                import traceback
                self.logger(traceback.format_exc())
                exec.shutdown(cancel_futures=True)
                
        self._merge_data()