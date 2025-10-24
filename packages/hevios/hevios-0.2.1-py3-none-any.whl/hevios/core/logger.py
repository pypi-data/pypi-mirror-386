from datetime import datetime
import os
from ..utils import Iox
class Logger:
    def __init__(self, dir = "logs/", console=True, debug=False):
        self.dir = dir
        self.iohelper = Iox()
        self.iohelper.mkdirs(self.dir)
        self.console = console
        self.is_debug = debug
        try:
            if os.path.exists(self.dir) ==False:
                os.makedirs(self.dir)
        except:
            return

    def write(self,content):
        if len(self.dir) > 0:
            with open(f'{self.dir}/{datetime.now().strftime('%Y%m%d')}.log', mode='+a', encoding='utf-8') as w:
                w.write(f'{content}\n')
                w.flush()

    def info(self, *objects, green_color=False):
        str_objects = "".join([str(obj) for obj in objects])
        if self.console:
            msg = f'{datetime.now().strftime('%H:%M:%S')} [I]: {str_objects}'
            if green_color:
                print(f'\033[32m{msg}\033[0m')
            else:
                print(f'{msg}')
            self.write(msg)

    def debug(self, *objects, green_color=False):
        str_objects = "".join([str(obj) for obj in objects])
        if self.console and self.is_debug:
            msg = f'{datetime.now().strftime('%H:%M:%S')} [D]: {str_objects}'
            if green_color:
                print(f'\033[32m {msg}\033[0m')
            else:
                print(f'{msg}')
            self.write(msg)

    def warn(self, *objects, yellow_color=True):
        str_objects = "".join([str(obj) for obj in objects])
        if self.console:
            msg = f'{datetime.now().strftime('%H:%M:%S')} [W]: {str_objects}'
            if yellow_color:
                print(f'\033[93m{msg}\033[0m')
            else:
                print(f'{msg}')
            self.write(msg)

    def error(self, *objects, red_color=True):
        str_objects = "".join([str(obj) for obj in objects])
        if self.console:
            msg = f'{datetime.now().strftime('%H:%M:%S')} [E]: {str_objects}'
            if red_color:
                print(f'\033[91m{msg}\033[0m')
            else:
                print(f'{msg}')
            self.write(msg)
            exit(-1)

    @staticmethod
    def default(console = False):
        log = Logger("logs/", False)
        return log