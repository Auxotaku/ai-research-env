#!/usr/bin/env python3
"""
AI科研项目环境诊断工具
检测Python版本、CUDA、GPU、已安装的AI框架等
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(cmd, timeout=10):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


def check_python():
    """检查Python版本和环境"""
    info = {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "executable": sys.executable,
        "platform": platform.platform(),
        "in_venv": hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
        "venv_path": sys.prefix
        if hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        else None,
    }
    return info


def check_pip():
    """检查pip配置"""
    info = {"installed": False, "version": None, "index_url": None}

    stdout, stderr, code = run_command(f"{sys.executable} -m pip --version")
    if code == 0 and stdout:
        info["installed"] = True
        parts = stdout.split()
        if len(parts) >= 2:
            info["version"] = parts[1]

    stdout, _, code = run_command(f"{sys.executable} -m pip config list")
    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if "index-url" in line:
                info["index_url"] = line.split("=")[-1].strip()

    return info


def check_cuda():
    """检查CUDA安装"""
    info = {"installed": False, "version": None, "nvcc_path": None}

    stdout, stderr, code = run_command("nvcc --version")
    if code == 0 and stdout:
        info["installed"] = True
        for line in stdout.split("\n"):
            if "release" in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if "release" in part.lower() and i + 1 < len(parts):
                        info["version"] = parts[i + 1].rstrip(",")
                        break

    if "CUDA_PATH" in os.environ:
        info["cuda_path"] = os.environ["CUDA_PATH"]

    return info


def check_gpu():
    """检查GPU信息"""
    info = {"available": False, "count": 0, "gpus": []}

    stdout, stderr, code = run_command(
        "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader",
        timeout=30,
    )
    if code == 0 and stdout:
        info["available"] = True
        for line in stdout.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    info["gpus"].append(
                        {"name": parts[0], "memory": parts[1], "driver": parts[2]}
                    )
        info["count"] = len(info["gpus"])

    return info


def check_torch():
    """检查PyTorch安装和CUDA支持"""
    info = {
        "installed": False,
        "version": None,
        "cuda_available": False,
        "cuda_version": None,
    }

    code = """
import sys
try:
    import torch
    print(f"TORCH_VERSION:{torch.__version__}")
    print(f"CUDA_AVAILABLE:{torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA_VERSION:{torch.version.cuda}")
except ImportError:
    pass
"""
    stdout, stderr, ret = run_command(f'{sys.executable} -c "{code}"')
    if stdout:
        info["installed"] = True
        for line in stdout.split("\n"):
            if line.startswith("TORCH_VERSION:"):
                info["version"] = line.split(":")[1]
            elif line.startswith("CUDA_AVAILABLE:"):
                info["cuda_available"] = line.split(":")[1] == "True"
            elif line.startswith("CUDA_VERSION:"):
                info["cuda_version"] = line.split(":")[1]

    return info


def check_ai_frameworks():
    """检查常用AI框架"""
    frameworks = [
        "tensorflow",
        "transformers",
        "diffusers",
        "accelerate",
        "mmcv",
        "mmdet",
        "mmaction",
        "torchvision",
        "torchaudio",
        "numpy",
        "pandas",
        "opencv-python",
        "pillow",
    ]

    installed = {}

    for pkg in frameworks:
        pkg_import = pkg.replace("-", "_").replace("opencv_python", "cv2")
        if pkg == "pillow":
            pkg_import = "PIL"

        code = f"""
try:
    import {pkg_import}
    print(f"INSTALLED:{{getattr({pkg_import}, '__version__', 'unknown')}}")
except ImportError:
    pass
"""
        stdout, _, _ = run_command(f'{sys.executable} -c "{code}"')
        if stdout and "INSTALLED:" in stdout:
            version = stdout.split("INSTALLED:")[1].strip()
            installed[pkg] = version

    return installed


def check_conda():
    """检查conda环境"""
    info = {"installed": False, "version": None, "current_env": None}

    stdout, stderr, code = run_command("conda --version")
    if code == 0 and stdout:
        info["installed"] = True
        parts = stdout.split()
        if len(parts) >= 2:
            info["version"] = parts[1]

    if "CONDA_DEFAULT_ENV" in os.environ:
        info["current_env"] = os.environ["CONDA_DEFAULT_ENV"]

    return info


def analyze_environment():
    """完整环境分析"""
    print("=" * 60)
    print("AI科研项目环境诊断报告")
    print("=" * 60)

    print("\n[Python 环境]")
    py_info = check_python()
    print(f"  版本: {py_info['version']}")
    print(f"  路径: {py_info['executable']}")
    print(f"  虚拟环境: {'是' if py_info['in_venv'] else '否'}")
    if py_info["venv_path"]:
        print(f"  虚拟环境路径: {py_info['venv_path']}")

    print("\n[pip 配置]")
    pip_info = check_pip()
    print(f"  已安装: {'是' if pip_info['installed'] else '否'}")
    if pip_info["version"]:
        print(f"  版本: {pip_info['version']}")
    if pip_info["index_url"]:
        print(f"  镜像源: {pip_info['index_url']}")
        is_china = any(
            x in pip_info["index_url"] for x in ["tuna", "aliyun", "ustc", "huawei"]
        )
        print(f"  国内镜像: {'是' if is_china else '否'}")

    print("\n[Conda 环境]")
    conda_info = check_conda()
    print(f"  已安装: {'是' if conda_info['installed'] else '否'}")
    if conda_info["version"]:
        print(f"  版本: {conda_info['version']}")
    if conda_info["current_env"]:
        print(f"  当前环境: {conda_info['current_env']}")

    print("\n[GPU 信息]")
    gpu_info = check_gpu()
    if gpu_info["available"]:
        print(f"  GPU数量: {gpu_info['count']}")
        for i, gpu in enumerate(gpu_info["gpus"]):
            print(f"  GPU {i}: {gpu['name']}")
            print(f"         显存: {gpu['memory']}")
            print(f"         驱动: {gpu['driver']}")
    else:
        print("  未检测到NVIDIA GPU")

    print("\n[CUDA 环境]")
    cuda_info = check_cuda()
    if cuda_info["installed"]:
        print(f"  已安装: 是")
        print(f"  版本: {cuda_info['version']}")
        if "cuda_path" in cuda_info:
            print(f"  路径: {cuda_info['cuda_path']}")
    else:
        print("  未检测到CUDA安装")

    print("\n[PyTorch 信息]")
    torch_info = check_torch()
    if torch_info["installed"]:
        print(f"  已安装: 是")
        print(f"  版本: {torch_info['version']}")
        print(f"  CUDA支持: {'是' if torch_info['cuda_available'] else '否'}")
        if torch_info["cuda_version"]:
            print(f"  PyTorch CUDA版本: {torch_info['cuda_version']}")
    else:
        print("  未安装PyTorch")

    print("\n[已安装的AI框架]")
    frameworks = check_ai_frameworks()
    if frameworks:
        for pkg, version in frameworks.items():
            print(f"  {pkg}: {version}")
    else:
        print("  未检测到常用AI框架")

    print("\n" + "=" * 60)

    return {
        "python": py_info,
        "pip": pip_info,
        "conda": conda_info,
        "gpu": gpu_info,
        "cuda": cuda_info,
        "pytorch": torch_info,
        "frameworks": frameworks,
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI科研项目环境诊断")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()

    result = analyze_environment()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
