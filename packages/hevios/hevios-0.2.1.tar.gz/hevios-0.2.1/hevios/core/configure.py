from datetime import datetime
import yaml
from typing import Any, Dict, List, Optional
from ..utils import SetX

try:
    setx = SetX()
    setx.with_pip("pyyaml")
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

class Configure:
    def __init__(self, file_path: str):
        """
        初始化配置管理器
        :param file_path: YAML 配置文件路径
        """
        self.file_path = file_path
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件内容，若文件不存在则返回空字典"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析错误: {e}")

    def _save_config(self) -> None:
        """将当前配置保存到文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持多级键，用:分隔，如 'database:host'）
        :param key: 配置键（支持多级）
        :param default: 不存在时的默认值
        :return: 配置值
        """
        keys = key.split(':')
        current = self.config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值（支持多级键，用:分隔，如 'database:port'）
        :param key: 配置键（支持多级）
        :param value: 配置值
        """
        keys = key.split(':')
        current = self.config

        # 遍历除最后一个键之外的所有键，创建不存在的层级
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        # 设置最后一个键的值
        current[keys[-1]] = value
        self._save_config()

    def delete(self, key: str) -> bool:
        """
        删除配置项（支持多级键）
        :param key: 配置键（支持多级）
        :return: 是否删除成功
        """
        keys = key.split(':')
        current = self.config
        parent_nodes: List[Dict[str, Any]] = []
        parent_keys: List[str] = []

        # 记录路径上的所有父节点和键
        for k in keys:
            parent_nodes.append(current)
            parent_keys.append(k)
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]

        # 从父节点中删除目标键
        parent_node = parent_nodes[-2] if len(parent_nodes) > 1 else parent_nodes[0]
        target_key = parent_keys[-1]
        if target_key in parent_node:
            del parent_node[target_key]
            self._save_config()
            return True
        return False

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()

    def clear(self) -> None:
        """清空所有配置"""
        self.config = {}
        self._save_config()
