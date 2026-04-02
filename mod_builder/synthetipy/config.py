"""
Synthetipy 配置模块

管理游戏目录、mod 目录等环境变量
"""

import os
from pathlib import Path
from typing import Optional


# 环境变量名
ENV_GAME_DIR = "STELLARIS_GAME_DIR"
ENV_MOD_DIR = "STELLARIS_MOD_DIR"


class Config:
    """配置管理类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._game_dir: Optional[Path] = None
        self._mod_dir: Optional[Path] = None
        self._initialized = True
        
        # 尝试从环境变量加载
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        game_dir = os.environ.get(ENV_GAME_DIR)
        if game_dir:
            self._game_dir = Path(game_dir)
        
        mod_dir = os.environ.get(ENV_MOD_DIR)
        if mod_dir:
            self._mod_dir = Path(mod_dir)
    
    @property
    def game_dir(self) -> Optional[Path]:
        """获取游戏目录"""
        return self._game_dir
    
    @game_dir.setter
    def game_dir(self, path: str | Path):
        """设置游戏目录"""
        self._game_dir = Path(path) if path else None
        if self._game_dir:
            os.environ[ENV_GAME_DIR] = str(self._game_dir)
    
    @property
    def mod_dir(self) -> Optional[Path]:
        """获取 mod 目录"""
        return self._mod_dir
    
    @mod_dir.setter
    def mod_dir(self, path: str | Path):
        """设置 mod 目录"""
        self._mod_dir = Path(path) if path else None
        if self._mod_dir:
            os.environ[ENV_MOD_DIR] = str(self._mod_dir)
    
    @property
    def inline_scripts_dir(self) -> Optional[Path]:
        """获取 inline_scripts 目录"""
        if self._game_dir:
            return self._game_dir / "common" / "inline_scripts"
        return None
    
    def get_inline_script_path(self, script_name: str) -> Optional[Path]:
        """
        获取 inline_script 文件的完整路径
        
        Args:
            script_name: 脚本名称，如 "districts/ai_research_extra_weighting"
        
        Returns:
            脚本文件的完整路径，如果不存在则返回 None
        """
        if not self.inline_scripts_dir:
            return None
        
        # 脚本名可能包含路径分隔符
        script_path = self.inline_scripts_dir / f"{script_name}.txt"
        
        if script_path.exists():
            return script_path
        
        # 尝试其他可能的位置（mod 目录）
        if self._mod_dir:
            mod_script_path = self._mod_dir / "common" / "inline_scripts" / f"{script_name}.txt"
            if mod_script_path.exists():
                return mod_script_path
        
        return None
    
    def validate(self) -> list[str]:
        """
        验证配置是否有效
        
        Returns:
            错误消息列表，如果配置有效则为空列表
        """
        errors = []
        
        if not self._game_dir:
            errors.append(f"游戏目录未设置。请设置环境变量 {ENV_GAME_DIR}")
        elif not self._game_dir.exists():
            errors.append(f"游戏目录不存在: {self._game_dir}")
        elif not self.inline_scripts_dir.exists():
            errors.append(f"inline_scripts 目录不存在: {self.inline_scripts_dir}")
        
        return errors


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取配置实例（便捷函数）"""
    return config


def set_game_dir(path: str | Path):
    """设置游戏目录（便捷函数）"""
    config.game_dir = path


def set_mod_dir(path: str | Path):
    """设置 mod 目录（便捷函数）"""
    config.mod_dir = path


def get_inline_script_path(script_name: str) -> Optional[Path]:
    """获取 inline_script 文件路径（便捷函数）"""
    return config.get_inline_script_path(script_name)
