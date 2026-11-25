"""统一游戏路径配置。

优先读环境变量 STELLARIS_GAME_ROOT，其次探测常见的 Steam 安装位置
（Steam 库在多块硬盘上移动时不必改代码）。解析步骤需要的是游戏根目录下存在
``common/districts``、``common/zones``、``common/zone_slots``、``common/pop_jobs``、
``common/economic_categories``。
"""

import os
from pathlib import Path

# 常见安装位置，按顺序探测；都不存在时用第一项（调用方会打印明确的报错）
_CANDIDATE_GAME_ROOTS = (
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stellaris"),
    Path(r"D:\SteamLibrary\steamapps\common\Stellaris"),
    Path(r"D:\Games\Stellaris"),
    Path(r"D:\Steam\steamapps\common\Stellaris"),
    Path(r"E:\SteamLibrary\steamapps\common\Stellaris"),
    Path(r"G:\SteamLibrary\steamapps\common\Stellaris"),
)


def _looks_like_game_root(path: Path) -> bool:
    return (path / "common" / "districts").is_dir()


def resolve_game_root() -> Path:
    override = os.environ.get("STELLARIS_GAME_ROOT")
    if override:
        return Path(override)

    for candidate in _CANDIDATE_GAME_ROOTS:
        if _looks_like_game_root(candidate):
            return candidate

    return _CANDIDATE_GAME_ROOTS[0]


# Stellaris 游戏根目录
GAME_ROOT = resolve_game_root()
