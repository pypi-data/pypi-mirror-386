from .core.logger import Logger
from .utils import SetX

class Orm:
    _log = Logger().default(False)
    def __init__(self,log,url, provider = "sqlite"):
        '''
        ORM控制器。
        
        :param log: 日志驱动，如果不需要可以设置成为None.
        :param url: URL是驱动配置，如果是SQLite可以直接放sqlite文件地址；如果是mysql（mariadb）则可以是字典类型的配置文件{'host': 'localhost', 'port': 3306, user: 'root', password: '123456', database:'default'}.
        :param provider: 驱动类型，目前支持SQLite、MySQL，使用SQLite数据库（默认）则配置为sqlite，MySQL（MariaDB）则配置为mysql.
        '''
        if log == None:
            self._log = Logger().default(False)
        else:
            self._log = log
        self._DATA_URL = url
        self._PROVIDER = provider
        self._setup = SetX(self._log)
        if self._PROVIDER.lower().startswith('sqlite'):
            self._log.info("use sqlite3 driver.")
            self._setup.with_pip("sqlite3")
            import sqlite3
            self.conn = sqlite3.connect(self._DATA_URL)
        elif self.PROVIDER.lower().startswith("mysql"):
            self._log.info("use mysql driver.")
            self._setup.with_pip("pymysql")
            import pymysql
            self._log.info("使用mysql/mariadb数据库！")
            self.conn = pymysql.connect(host=self.DATA_URL['host'],
                                     port=int(self.DATA_URL['port']),
                                     user=self.DATA_URL['user'],
                                     password=self.DATA_URL['password'],
                                     database=self.DATA_URL['database'])
        else:
            self._log.warn("不支持的驱动!")
    def close(self):
        '''
        关闭链接
        '''
        self.conn.close()
    def fetchall(self, sql, params = None):
        '''
        查询数据方法
        
        :param sql: SQL代码
        :param params: 参数列表.
        :return: 查询的数据.
        '''
        if params is not None:
            return self.conn.execute(sql,params).fetchall()
        else:
            return self.conn.execute(sql).fetchall()
    def fetchone(self, sql, params = None):
        '''
        查询数据方法
        
        :param sql: SQL代码
        :param params: 参数列表.
        :return: 查询的数据.
        '''
        if params is not None:
            return self.conn.execute(sql,params).fetchone()
        else:
            return self.conn.execute(sql).fetchone()
    def fetchmany(self, sql, params = None, size=1):
        '''
        查询数据方法
        
        :param sql: SQL代码
        :param params: 参数列表.
        :param size: 返回结果数量.
        :return: 查询的数据.
        '''
        if params is not None:
            return self.conn.execute(sql,params).fetchmany(size=size)
        else:
            return self.conn.execute(sql).fetchmany(size=size)
    def execute(self, sql, params = None):
        '''
        执行无需返回的方法
        
        :param sql: SQL代码
        :param params: 参数列表.
        :return: 执行结果.
        '''
        if params is not None:
            return self.conn.execute(sql,params)
        else:
            return self.conn.execute(sql)
    def commit(self):
        '''
        提交结果方法，将结果写入到数据库
        '''
        self.conn.commit()