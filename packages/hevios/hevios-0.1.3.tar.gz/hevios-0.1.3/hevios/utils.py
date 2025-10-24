import time
class Stopwatch:
    def __init__(self):
        '''
        性能计数器
        '''
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.perf_counter_ns()
        self.end_time = None

    def stop(self):
        """停止计时"""
        if self.start_time:
            self.end_time = time.perf_counter_ns()
        else:
            raise RuntimeError("请先调用start()方法开始计时")
    def timespan_format(self):
        """
            返回性能间隔，并自动选择合适单位
        """
        f,d = self.timespan()
        return f'{f}{d}'
    def timespan(self):
        """
            返回性能间隔，返回结果是一个元组（时间,单位）
        """
        if not self.end_time:
            raise RuntimeError("请先调用stop()方法结束计时")
            
        # 计算纳秒级时间差
        nanoseconds = self.end_time - self.start_time
        
        # 定义单位转换和格式
        # 定义正确的单位转换和格式（修正了阈值错误）
        # 1小时 = 3600秒 = 3600×1e9纳秒 = 3.6e12纳秒
        # 1分钟 = 60秒 = 6e10纳秒
        # 1秒 = 1e9纳秒
        # 1毫秒 = 1e6纳秒
        # 1微秒 = 1e3纳秒
        units = [
            (3.6e12, '{:.6f}','h'),    # 小时
            (6e10, '{:.6f}','m'),      # 分钟
            (1e9, '{:.6f}','s'),         # 秒
            (1e6, '{:.6f}','ms'),       # 毫秒
            (1e3, '{:.6f}','us'),       # 微秒
            (1, '{}','ns')              # 纳秒
        ]
        
        # 选择最合适的单位
        for threshold, format_str, sec in units:
            if nanoseconds >= threshold:
                value = nanoseconds / threshold
                return format_str.format(value),sec
        
        return f"{nanoseconds}"

import os
from typing import List, Optional
class Iox:
    @staticmethod
    def get_files(
        directory: str,
        filter: Optional[str] = None,
        toponly: bool = False
    ) -> List[str]:
        """
        获取目录中所有文件的路径列表
        
        :param directory: 目标目录路径
        :param filter: 文件类型过滤（如 '.txt' 只获取txt文件，None则不过滤）
        :param toponly: 是否只获取顶层目录文件（True：不递归子目录，False：递归所有子目录）
        :return: 文件路径列表（绝对路径）
        """
        if not os.path.isdir(directory):
            raise ValueError(f"目录不存在或不是有效目录: {directory}")
        
        file_paths = []
        # 遍历目录（toponly控制是否递归）
        walk_generator = os.walk(directory)
        
        for root, _, files in walk_generator:
            for file in files:
                # 构建文件绝对路径
                file_path = os.path.abspath(os.path.join(root, file))
                
                # 应用文件类型过滤
                if filter is not None:
                    # 统一处理后缀名格式（确保以.开头）
                    if not filter.startswith('.'):
                        filter = f'.{filter}'
                    if not file.endswith(filter):
                        continue  # 跳过不符合类型的文件
                
                file_paths.append(file_path)
            
            # 如果只获取顶层目录，遍历一次后退出
            if toponly:
                break
        
        return file_paths
    
    @staticmethod
    def mkdirs(dir, exist_ok = True, mask = 0o777):
        """
        创建多级目录的方法.

        :param dir: 需要创建的目录路径.
        :param exist_ok: 如果目录已经存在，是否忽略错误.
        :param mask: 目录的权限掩码.
        """
        os.makedirs(dir, exist_ok=exist_ok, mode=mask)

    @staticmethod
    def get_directories(directory: str,name_filter: Optional[str] = None,toponly: bool = False) -> List[str]:
        """
        获取目录中所有子目录的路径列表
        
        :param directory: 目标目录路径
        :param name_filter: 目录名称过滤（支持模糊匹配，如包含"test"的目录；None则不过滤）
        :param toponly: 是否只获取顶层目录（True：不递归子目录，False：递归所有子目录）
        :return: 目录路径列表（绝对路径）
        """
        if not os.path.isdir(directory):
            raise ValueError(f"目录不存在或不是有效目录: {directory}")
        
        dir_paths = []
        # 遍历目录（toponly控制是否递归）
        walk_generator = os.walk(directory)
        
        for root, dirs, _ in walk_generator:
            for dir_name in dirs:
                # 构建目录绝对路径
                dir_path = os.path.abspath(os.path.join(root, dir_name))
                
                # 应用目录名称过滤（模糊匹配）
                if name_filter is not None:
                    if name_filter not in dir_name:
                        continue  # 跳过名称不包含过滤字符的目录
                
                dir_paths.append(dir_path)
            
            # 如果只获取顶层目录，遍历一次后退出
            if toponly:
                break
        
        return dir_paths

class Listx:
    @staticmethod
    def subtraction(subtrahend,minuend):
        '''
        列表减法计算，注意可能涉及到类型转换，比如字符串类型1比较是不相等的。
        
        :param subtrahend: 减数列表.
        :param minuend: 被减数列表.
        :return: 存在减数列表且不在被减数列表中的元素.
        '''
        return [item for item in subtrahend if item not in minuend]

import importlib,importlib.util, os
from .core import Logger
class SetX:
    _log = Logger.default()
    def __init__(self, log = None):
        if log is not None:
            self._log = log
        else:
            self._log = Logger.default(False)
        if self.check_pip("subprocess") is False:
            os.system("pip install subprocess -i https://pypi.tuna.tsinghua.edu.cn/simple")
        
    def check_pip(self,package):
        return importlib.util.find_spec(package) is not None
    def with_pips(self,packages):
        for package in packages:
            self.with_pip(package=package)

    def with_pip(self, package):
        import subprocess
        if self.check_pip(package) is False:
            self._log.info(f"Install packages: {package}")
            subprocess.call(f'pip install {package} -i https://pypi.tuna.tsinghua.edu.cn/simple',stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self._log.info(f"Install packages: {package} Exist!", green_color=True)
