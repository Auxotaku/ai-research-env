#!/usr/bin/env python3
"""
智能安装脚本
自动分析依赖、智能排序、断点续传、重试机制
适用于Linux服务器科研环境

安全约束：本脚本不执行任何删除操作
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


INSTALL_ORDER = {
    "torch": 1,
    "torchvision": 1,
    "torchaudio": 1,
    "cuda": 1,
    "numpy": 2,
    "scipy": 2,
    "pillow": 2,
    "opencv-python": 2,
    "transformers": 3,
    "accelerate": 3,
    "huggingface_hub": 3,
    "diffusers": 3,
    "peft": 3,
    "timm": 3,
    "einops": 3,
    "omegaconf": 3,
    "hydra-core": 3,
    "mmengine": 4,
    "mmcv": 4,
    "mmdet": 4,
    "mmsegmentation": 4,
    "mmaction2": 4,
    "flash-attn": 99,
    "xformers": 98,
    "bitsandbytes": 97,
    "deepspeed": 96,
    "triton": 95,
}

SPECIAL_PACKAGES = {
    "flash-attn": {
        "note": "flash-attn需要预编译whl或从源码编译，建议使用预编译版本",
        "prebuilt_url": "https://github.com/bdashore3/flash-attention/releases",
        "install_cmd": "pip install flash-attn --no-build-isolation",
    },
    "xformers": {
        "note": "xformers版本需与PyTorch版本匹配",
        "install_cmd": "pip install xformers",
    },
    "bitsandbytes": {
        "note": "bitsandbytes需要CUDA 11.8+",
        "install_cmd": "pip install bitsandbytes",
    },
    "mmcv": {
        "note": "mmcv建议使用mim安装",
        "install_cmd": "pip install -U openmim && mim install mmcv",
        "alt_cmd": "pip install mmcv -f https://download.openmmlab.com/mmcv/dist/{cuda}/torch{version}/index.html",
    },
}

MAX_RETRIES = 3
STATE_FILE = ".install_state.json"


def run_command(cmd, timeout=300, capture=True):
    """运行命令"""
    try:
        if capture:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            return "", "", result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


def check_cuda_version():
    """检测CUDA版本"""
    stdout, _, code = run_command("nvcc --version")
    if code == 0 and stdout:
        for line in stdout.split("\n"):
            if "release" in line.lower():
                match = re.search(r"release\s+(\d+\.\d+)", line, re.IGNORECASE)
                if match:
                    return match.group(1)
    return None


def get_pytorch_install_cmd(cuda_version=None):
    """获取PyTorch安装命令"""
    if cuda_version is None:
        cuda_version = check_cuda_version()

    if cuda_version:
        cuda_major_minor = (
            cuda_version.rsplit(".", 1)[0] if "." in cuda_version else cuda_version
        )
        cuda_key = cuda_major_minor.replace(".", "")

        if cuda_key in ["124", "125", "126"]:
            return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124"
        elif cuda_key in ["121", "122", "123"]:
            return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        elif cuda_key in ["118", "119", "120"]:
            return "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"

    return "pip install torch torchvision torchaudio"


def parse_requirements(req_file):
    """解析requirements.txt"""
    requirements = []

    if not Path(req_file).exists():
        return requirements

    content = Path(req_file).read_text(encoding="utf-8")

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r"):
            continue

        if line.startswith("http") or line.startswith("git+"):
            continue

        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
        if match:
            pkg = match.group(1).lower()
            version_spec = line[len(pkg) :].strip()
            requirements.append({"name": pkg, "spec": version_spec, "original": line})

    return requirements


def get_install_priority(pkg_name):
    """获取安装优先级"""
    pkg_lower = pkg_name.lower()
    return INSTALL_ORDER.get(pkg_lower, 50)


def sort_requirements(requirements):
    """按安装优先级排序"""
    return sorted(
        requirements, key=lambda x: (get_install_priority(x["name"]), x["name"])
    )


def load_state(project_path):
    """加载安装状态"""
    state_file = Path(project_path) / STATE_FILE
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except:
            pass
    return {"installed": [], "failed": [], "attempts": {}}


def save_state(project_path, state):
    """保存安装状态"""
    state_file = Path(project_path) / STATE_FILE
    state["last_update"] = datetime.now().isoformat()
    state_file.write_text(json.dumps(state, indent=2))


def install_package(pkg_info, state, dry_run=False):
    """安装单个包"""
    pkg_name = pkg_info["name"]
    spec = pkg_info.get("spec", "")

    if pkg_name in state["installed"]:
        print(f"  [跳过] {pkg_name} 已安装")
        return True

    attempts = state["attempts"].get(pkg_name, 0)
    if attempts >= MAX_RETRIES:
        print(f"  [跳过] {pkg_name} 已达最大重试次数 ({MAX_RETRIES})")
        return False

    install_cmd = f"pip install {pkg_name}{spec}"

    if pkg_name.lower() in SPECIAL_PACKAGES:
        special = SPECIAL_PACKAGES[pkg_name.lower()]
        print(f"  [注意] {special['note']}")
        if "install_cmd" in special:
            install_cmd = special["install_cmd"]

    if pkg_name.lower() == "torch":
        cuda_version = check_cuda_version()
        install_cmd = get_pytorch_install_cmd(cuda_version)
        print(f"  [CUDA {cuda_version}] {install_cmd}")

    if dry_run:
        print(f"  [模拟] {install_cmd}")
        return True

    print(f"  [安装] {pkg_name}...")
    state["attempts"][pkg_name] = attempts + 1

    stdout, stderr, code = run_command(install_cmd, timeout=600, capture=False)

    if code == 0:
        print(f"  [成功] {pkg_name}")
        state["installed"].append(pkg_name)
        return True
    else:
        print(f"  [失败] {pkg_name}")
        if stderr:
            print(f"    错误: {stderr[:200]}")
        state["failed"].append(pkg_name)
        return False


def smart_install(project_path, requirements_file="requirements.txt", dry_run=False):
    """智能安装流程"""
    project_path = Path(project_path)

    print("=" * 60)
    print("智能安装流程")
    print("=" * 60)
    print(f"\n项目路径: {project_path}")
    print(f"安全约束: 不执行任何删除操作\n")

    print("[1/4] 检测CUDA环境")
    cuda_version = check_cuda_version()
    if cuda_version:
        print(f"  CUDA版本: {cuda_version}")
    else:
        print("  未检测到CUDA (将安装CPU版本PyTorch)")

    print("\n[2/4] 解析依赖")
    req_path = project_path / requirements_file
    requirements = parse_requirements(req_path)

    if not requirements:
        print(f"  未找到 {requirements_file}")
        return

    print(f"  发现 {len(requirements)} 个依赖")

    print("\n[3/4] 排序依赖")
    sorted_reqs = sort_requirements(requirements)

    torch_packages = [r for r in sorted_reqs if get_install_priority(r["name"]) == 1]
    core_packages = [r for r in sorted_reqs if get_install_priority(r["name"]) == 2]
    ml_packages = [r for r in sorted_reqs if get_install_priority(r["name"]) == 3]
    mm_packages = [r for r in sorted_reqs if get_install_priority(r["name"]) == 4]
    special_packages = [r for r in sorted_reqs if get_install_priority(r["name"]) > 90]
    other_packages = [
        r for r in sorted_reqs if 10 <= get_install_priority(r["name"]) <= 90
    ]

    print(f"  PyTorch核心: {len(torch_packages)}")
    print(f"  基础依赖: {len(core_packages)}")
    print(f"  ML框架: {len(ml_packages)}")
    print(f"  OpenMMLab: {len(mm_packages)}")
    print(f"  特殊包: {len(special_packages)}")
    print(f"  其他: {len(other_packages)}")

    print("\n[4/4] 安装依赖")
    state = load_state(project_path)

    install_order = (
        torch_packages
        + core_packages
        + ml_packages
        + mm_packages
        + other_packages
        + special_packages
    )

    success_count = 0
    fail_count = 0
    skip_count = 0

    for pkg in install_order:
        if pkg["name"] in state["installed"]:
            skip_count += 1
            continue

        if install_package(pkg, state, dry_run):
            success_count += 1
        else:
            fail_count += 1

        save_state(project_path, state)

    print("\n" + "=" * 60)
    print("安装完成")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  跳过: {skip_count}")

    if state["failed"]:
        print(f"\n失败的包:")
        for pkg in state["failed"]:
            attempts = state["attempts"].get(pkg, 0)
            print(f"  - {pkg} (尝试 {attempts} 次)")

    print(f"\n状态文件: {project_path / STATE_FILE}")
    print("=" * 60)


def generate_install_script(project_path, requirements_file="requirements.txt"):
    """生成安装脚本"""
    project_path = Path(project_path)
    req_path = project_path / requirements_file
    requirements = parse_requirements(req_path)
    sorted_reqs = sort_requirements(requirements)
    cuda_version = check_cuda_version()

    script = f"""#!/bin/bash
# 自动生成的安装脚本
# 生成时间: {datetime.now().isoformat()}
# CUDA版本: {cuda_version or "未检测"}

set -e

echo "========================================"
echo "环境安装脚本"
echo "========================================"

# 配置镜像源 (可选)
# pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装PyTorch
echo "[1] 安装PyTorch..."
{get_pytorch_install_cmd(cuda_version)}

# 安装其他依赖
echo "[2] 安装依赖..."
"""

    for pkg in sorted_reqs:
        if pkg["name"].lower() not in ["torch", "torchvision", "torchaudio"]:
            script += f"pip install {pkg['original']}\n"

    script += """
echo "========================================"
echo "安装完成"
echo "========================================
"""

    output_file = project_path / "install.sh"
    output_file.write_text(script)
    print(f"安装脚本已生成: {output_file}")
    print("运行: chmod +x install.sh && ./install.sh")


def main():
    parser = argparse.ArgumentParser(description="智能安装脚本")
    parser.add_argument("path", nargs="?", default=".", help="项目路径")
    parser.add_argument(
        "--requirements", "-r", default="requirements.txt", help="requirements文件"
    )
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际安装")
    parser.add_argument(
        "--generate-script", action="store_true", help="生成bash安装脚本"
    )
    parser.add_argument("--clear-state", action="store_true", help="清除安装状态")
    args = parser.parse_args()

    if args.clear_state:
        state_file = Path(args.path) / STATE_FILE
        if state_file.exists():
            print(f"注意: 需要手动删除状态文件: {state_file}")
        return

    if args.generate_script:
        generate_install_script(args.path, args.requirements)
    else:
        smart_install(args.path, args.requirements, args.dry_run)


if __name__ == "__main__":
    main()
