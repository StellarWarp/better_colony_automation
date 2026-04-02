import subprocess
import sys
from pathlib import Path

def run_script(script_path, cwd):
    print(f"========== 正在执行 {script_path.name} ==========")
    # 确保在对应的上下文目录中运行，防止相对路径找不到文件
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(cwd))
    if result.returncode != 0:
        print(f"❌ {script_path.name} 执行失败！")
        sys.exit(result.returncode)
    print(f"✅ {script_path.name} 执行完成\n")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent

    print("🚀 开始构建 Stellaris Mod...")

    # 1. 运行所有的图像生成 (位于 mod_builder/image_gen.py)
    image_gen_script = base_dir / "image_gen.py"
    if image_gen_script.exists():
        run_script(image_gen_script, base_dir)

    # 2. 从源码解析最新的 YAML 数据 (在 mod_builder/parse 下可能存在主控脚本或可分别调用)
    # 假设目前还没有完善统一的 parse main 脚本，这里你可以后续添加 run_script(base_dir / "parse" / "build_ast.py", base_dir / "parse")
    # run_script(base_dir / "parse" / "xxx.py", base_dir / "parse")

    # 3. 把 YAML 数据渲染到模板生成代码
    generate_script = base_dir / "generate.py"
    if generate_script.exists():
        run_script(generate_script, base_dir)

    print("🎉 整个 Mod 构建流水线已全部执行完成！")

