#!/usr/bin/env python3
"""
GPU/CUDA环境检查工具
检测GPU信息、CUDA版本兼容性
"""

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(cmd, timeout=30):
    """运行命令"""
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
    except Exception as e:
        return "", str(e), -1


CUDA_PYTORCH_COMPATIBILITY = {
    "12.4": ["2.5.0", "2.4.0", "2.3.0"],
    "12.1": ["2.5.0", "2.4.0", "2.3.0", "2.2.0", "2.1.0"],
    "11.8": ["2.5.0", "2.4.0", "2.3.0", "2.2.0", "2.1.0", "2.0.0", "1.13.0"],
    "11.7": ["2.0.0", "1.13.0", "1.12.0"],
    "11.6": ["1.12.0", "1.11.0"],
    "11.3": ["1.11.0", "1.10.0", "1.9.0"],
}


def check_nvidia_driver():
    """检查NVIDIA驱动"""
    info = {"installed": False, "version": None}

    stdout, stderr, code = run_command("nvidia-smi")
    if code == 0 and stdout:
        info["installed"] = True
        for line in stdout.split("\n"):
            if "Driver Version" in line:
                parts = line.split("Driver Version:")
                if len(parts) > 1:
                    version_part = parts[1].split()[0]
                    info["version"] = version_part
                break

    return info


def check_cuda():
    """检查CUDA安装"""
    info = {
        "nvcc_installed": False,
        "nvcc_version": None,
        "cuda_path": None,
        "cuda_home": None,
    }

    stdout, stderr, code = run_command("nvcc --version")
    if code == 0 and stdout:
        info["nvcc_installed"] = True
        for line in stdout.split("\n"):
            if "release" in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if "release" in part.lower() and i + 1 < len(parts):
                        info["nvcc_version"] = parts[i + 1].rstrip(",")
                        break

    if "CUDA_PATH" in os.environ:
        info["cuda_path"] = os.environ["CUDA_PATH"]
    if "CUDA_HOME" in os.environ:
        info["cuda_home"] = os.environ["CUDA_HOME"]

    return info


def check_gpus():
    """检查GPU信息"""
    info = {"available": False, "count": 0, "gpus": []}

    stdout, stderr, code = run_command(
        "nvidia-smi --query-gpu=index,name,memory.total,memory.free,compute_cap --format=csv,noheader",
        timeout=30,
    )

    if code == 0 and stdout:
        info["available"] = True
        for line in stdout.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    info["gpus"].append(
                        {
                            "index": parts[0],
                            "name": parts[1],
                            "memory_total": parts[2],
                            "memory_free": parts[3],
                            "compute_cap": parts[4] if len(parts) > 4 else "N/A",
                        }
                    )
        info["count"] = len(info["gpus"])

    return info


def check_pytorch_cuda():
    """检查PyTorch的CUDA支持"""
    info = {
        "pytorch_installed": False,
        "pytorch_version": None,
        "cuda_available": False,
        "pytorch_cuda_version": None,
        "cudnn_version": None,
        "gpu_count": 0,
    }

    code = """
import sys
try:
    import torch
    print(f"PYTORCH_VERSION:{torch.__version__}")
    print(f"CUDA_AVAILABLE:{torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA_VERSION:{torch.version.cuda}")
        print(f"CUDNN_VERSION:{torch.backends.cudnn.version()}")
        print(f"GPU_COUNT:{torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU_NAME_{i}:{torch.cuda.get_device_name(i)}")
except ImportError:
    pass
"""

    stdout, stderr, ret = run_command(f'{sys.executable} -c "{code}"')

    if stdout and "PYTORCH_VERSION" in stdout:
        info["pytorch_installed"] = True
        for line in stdout.split("\n"):
            if line.startswith("PYTORCH_VERSION:"):
                info["pytorch_version"] = line.split(":")[1]
            elif line.startswith("CUDA_AVAILABLE:"):
                info["cuda_available"] = line.split(":")[1] == "True"
            elif line.startswith("CUDA_VERSION:"):
                info["pytorch_cuda_version"] = line.split(":")[1]
            elif line.startswith("CUDNN_VERSION:"):
                info["cudnn_version"] = line.split(":")[1]
            elif line.startswith("GPU_COUNT:"):
                info["gpu_count"] = int(line.split(":")[1])

    return info


def check_tensorflow_gpu():
    """检查TensorFlow的GPU支持"""
    info = {
        "tf_installed": False,
        "tf_version": None,
        "gpu_available": False,
        "gpu_devices": [],
    }

    code = """
import sys
try:
    import tensorflow as tf
    print(f"TF_VERSION:{tf.__version__}")
    gpus = tf.config.list_physical_devices('GPU')
    print(f"GPU_AVAILABLE:{len(gpus) > 0}")
    for gpu in gpus:
        print(f"GPU_DEVICE:{gpu}")
except ImportError:
    pass
"""

    stdout, stderr, ret = run_command(f'{sys.executable} -c "{code}"')

    if stdout and "TF_VERSION" in stdout:
        info["tf_installed"] = True
        for line in stdout.split("\n"):
            if line.startswith("TF_VERSION:"):
                info["tf_version"] = line.split(":")[1]
            elif line.startswith("GPU_AVAILABLE:"):
                info["gpu_available"] = line.split(":")[1] == "True"
            elif line.startswith("GPU_DEVICE:"):
                info["gpu_devices"].append(line.split("GPU_DEVICE:")[1])

    return info


def get_pytorch_install_command(cuda_version, pytorch_version="latest"):
    """获取PyTorch安装命令"""
    if cuda_version is None:
        return "pip install torch torchvision torchaudio"

    cuda_version = cuda_version.replace(".", "")
    if cuda_version.startswith("12"):
        cuda_version = cuda_version[:3]

    commands = {
        "124": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124",
        "121": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        "118": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
    }

    return commands.get(cuda_version, commands.get("118"))


def analyze_gpu_environment():
    """完整GPU环境分析"""
    print("=" * 60)
    print("GPU/CUDA环境检查报告")
    print("=" * 60)

    print("\n[NVIDIA驱动]")
    driver = check_nvidia_driver()
    if driver["installed"]:
        print(f"  已安装: 是")
        print(f"  版本: {driver['version']}")
    else:
        print("  未检测到NVIDIA驱动")
        return None

    print("\n[GPU信息]")
    gpus = check_gpus()
    if gpus["available"]:
        print(f"  GPU数量: {gpus['count']}")
        for gpu in gpus["gpus"]:
            print(f"  GPU {gpu['index']}: {gpu['name']}")
            print(f"         显存: {gpu['memory_total']} (可用: {gpu['memory_free']})")
            print(f"         计算能力: {gpu['compute_cap']}")
    else:
        print("  未检测到GPU")
        return None

    print("\n[CUDA环境]")
    cuda = check_cuda()
    if cuda["nvcc_installed"]:
        print(f"  nvcc: 已安装")
        print(f"  CUDA版本: {cuda['nvcc_version']}")
    else:
        print("  nvcc: 未安装 (可能只有运行时CUDA)")

    if cuda["cuda_path"]:
        print(f"  CUDA_PATH: {cuda['cuda_path']}")

    print("\n[PyTorch CUDA]")
    torch_info = check_pytorch_cuda()
    if torch_info["pytorch_installed"]:
        print(f"  PyTorch版本: {torch_info['pytorch_version']}")
        print(f"  CUDA支持: {'是' if torch_info['cuda_available'] else '否'}")
        if torch_info["cuda_available"]:
            print(f"  PyTorch CUDA版本: {torch_info['pytorch_cuda_version']}")
            print(f"  cuDNN版本: {torch_info['cudnn_version']}")
            print(f"  可用GPU: {torch_info['gpu_count']}")
    else:
        print("  PyTorch: 未安装")

    print("\n[TensorFlow GPU]")
    tf_info = check_tensorflow_gpu()
    if tf_info["tf_installed"]:
        print(f"  TensorFlow版本: {tf_info['tf_version']}")
        print(f"  GPU支持: {'是' if tf_info['gpu_available'] else '否'}")
    else:
        print("  TensorFlow: 未安装")

    if cuda["nvcc_version"] and not torch_info["pytorch_installed"]:
        print("\n[建议安装命令]")
        install_cmd = get_pytorch_install_command(cuda["nvcc_version"])
        print(f"  {install_cmd}")

    print("\n" + "=" * 60)

    return {
        "driver": driver,
        "gpus": gpus,
        "cuda": cuda,
        "pytorch": torch_info,
        "tensorflow": tf_info,
    }


def main():
    parser = argparse.ArgumentParser(description="GPU/CUDA环境检查")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument(
        "--install-cmd", action="store_true", help="输出PyTorch安装命令"
    )
    args = parser.parse_args()

    result = analyze_gpu_environment()

    if args.json and result:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.install_cmd and result and result["cuda"].get("nvcc_version"):
        print(get_pytorch_install_command(result["cuda"]["nvcc_version"]))


if __name__ == "__main__":
    main()
