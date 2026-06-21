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

    # 2. 生成 templates/generated_configs 下的统一配置层
    parse_build_script = base_dir / "parse" / "build_generated_configs.py"
    if parse_build_script.exists():
        run_script(parse_build_script, base_dir / "parse")

    # 3. 把 YAML 数据渲染到模板生成代码
    generate_script = base_dir / "generate.py"
    if generate_script.exists():
        run_script(generate_script, base_dir)

    print("🎉 整个 Mod 构建流水线已全部执行完成！")

