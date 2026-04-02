import re
import os

def list_top_level_objects(file_path):
    if not os.path.exists(file_path):
        print(f"错误: 文件未找到 - {file_path}")
        return

    top_level_keys = []
    brace_level = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 移除注释和行首尾空格
            clean_line = re.sub(r'#.*', '', line).strip()
            if not clean_line:
                continue
            
            # 如果当前在最外层（层级为 0）
            if brace_level == 0:
                # 匹配格式为 key = { 或 key = value 的行
                # 排除以 @ 开头的变量定义
                match = re.match(r'^([a-zA-Z0-9_]+)\s*=', clean_line)
                if match:
                    top_level_keys.append(match.group(1))
            
            # 更新大括号深度
            brace_level += clean_line.count('{')
            brace_level -= clean_line.count('}')

    return top_level_keys

if __name__ == "__main__":
    target_file = r'D:\SteamLibrary\steamapps\common\Stellaris\common\colony_types\00_colony_types.txt'
    # 如果你在 Linux/macOS 下运行，请确保路径斜杠正确，或者使用 os.path.join
    
    objects = list_top_level_objects(target_file)
    
    if objects:
        print(f"在 {target_file} 中找到以下顶级对象：")
        for obj in objects:
            print(f"{obj}")
    else:
        print("未找到任何顶级对象。")
