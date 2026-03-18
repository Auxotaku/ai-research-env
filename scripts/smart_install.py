#!/usr/bin/env python3
"""
智能安装脚本
自动分析依赖、智能排序、断点续传、重试机制
适用于Linux服务器科研环境

安全约束：本脚本不执行任何删除操作

功能：
1. PyTorch优先安装
2. 智能依赖排序
3. 断点续传
4. 命令历史记录
5. 自动生成环境配置报告
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


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
        "note": "flash-attn需要预编译whl或从源码编译",
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
        "install_cmd": "mim install mmcv",
    },
}

MAX_RETRIES = 3
STATE_FILE = ".install_state.json"
COMMANDS_LOG_FILE = ".install_commands.log"


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
        cuda_key = (
            cuda_version.rsplit(".", 1)[0] if "." in cuda_version else cuda_version
        )
        cuda_key = cuda_key.replace(".", "")

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
    return INSTALL_ORDER.get(pkg_name.lower(), 50)


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
    return {
        "installed": [],
        "failed": [],
        "attempts": {},
        "commands": [],
        "start_time": None,
    }


def save_state(project_path, state):
    """保存安装状态"""
    state_file = Path(project_path) / STATE_FILE
    state["last_update"] = datetime.now().isoformat()
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def log_command(project_path, cmd, success=True):
    """记录命令到日志"""
    log_file = Path(project_path) / COMMANDS_LOG_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if success else "FAIL"
    line = f"# [{timestamp}] [{status}]\n{cmd}\n\n"
    log_file.write_text(log_file.read_text() + line if log_file.exists() else line)


def install_package(pkg_info, state, project_path, dry_run=False):
    """安装单个包"""
    pkg_name = pkg_info["name"]
    spec = pkg_info.get("spec", "")

    if pkg_name in state["installed"]:
        return True, None

    attempts = state["attempts"].get(pkg_name, 0)
    if attempts >= MAX_RETRIES:
        return False, None

    install_cmd = f"pip install {pkg_name}{spec}"

    if pkg_name.lower() in SPECIAL_PACKAGES:
        special = SPECIAL_PACKAGES[pkg_name.lower()]
        install_cmd = special.get("install_cmd", install_cmd)

    if pkg_name.lower() == "torch":
        cuda_version = check_cuda_version()
        install_cmd = get_pytorch_install_cmd(cuda_version)

    if dry_run:
        return True, install_cmd

    print(f"  安装: {pkg_name}...")
    state["attempts"][pkg_name] = attempts + 1

    stdout, stderr, code = run_command(install_cmd, timeout=600, capture=False)

    success = code == 0

    if success:
        state["installed"].append(pkg_name)
        state["commands"].append(install_cmd)
        log_command(project_path, install_cmd, success=True)
        print(f"  成功: {pkg_name}")
    else:
        state["failed"].append(pkg_name)
        log_command(project_path, install_cmd, success=False)
        print(f"  失败: {pkg_name}")

    return success, install_cmd


def smart_install(
    project_path,
    requirements_file="requirements.txt",
    dry_run=False,
    generate_report=True,
):
    """智能安装流程"""
    project_path = Path(project_path).resolve()

    print("=" * 60)
    print("智能安装流程")
    print("=" * 60)
    print(f"\n项目路径: {project_path}")
    print("安全约束: 不执行任何删除操作\n")

    state = load_state(project_path)
    if not state.get("start_time"):
        state["start_time"] = datetime.now().isoformat()

    print("[1/5] 检测CUDA环境")
    cuda_version = check_cuda_version()
    if cuda_version:
        print(f"  CUDA版本: {cuda_version}")
    else:
        print("  未检测到CUDA")

    print("\n[2/5] 解析依赖")
    req_path = project_path / requirements_file
    requirements = parse_requirements(req_path)

    if not requirements:
        print(f"  未找到 {requirements_file}")
        return

    print(f"  发现 {len(requirements)} 个依赖")

    print("\n[3/5] 排序依赖")
    sorted_reqs = sort_requirements(requirements)

    groups = {
        "PyTorch核心": [r for r in sorted_reqs if get_install_priority(r["name"]) == 1],
        "基础依赖": [r for r in sorted_reqs if get_install_priority(r["name"]) == 2],
        "ML框架": [r for r in sorted_reqs if get_install_priority(r["name"]) == 3],
        "OpenMMLab": [r for r in sorted_reqs if get_install_priority(r["name"]) == 4],
        "特殊包": [r for r in sorted_reqs if get_install_priority(r["name"]) > 90],
        "其他": [r for r in sorted_reqs if 10 <= get_install_priority(r["name"]) <= 90],
    }

    for name, pkgs in groups.items():
        if pkgs:
            print(f"  {name}: {len(pkgs)} 个")

    print("\n[4/5] 安装依赖")

    install_order = (
        groups["PyTorch核心"]
        + groups["基础依赖"]
        + groups["ML框架"]
        + groups["OpenMMLab"]
        + groups["其他"]
        + groups["特殊包"]
    )

    success_count = 0
    fail_count = 0
    skip_count = 0
    commands_run = []

    for pkg in install_order:
        if pkg["name"] in state["installed"]:
            skip_count += 1
            continue

        success, cmd = install_package(pkg, state, project_path, dry_run)
        if cmd:
            commands_run.append(cmd)
        if success:
            success_count += 1
        else:
            fail_count += 1

        save_state(project_path, state)

    print("\n[5/5] 安装完成")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  跳过: {skip_count}")

    if state.get("failed"):
        print(f"\n失败的包:")
        for pkg in state["failed"]:
            attempts = state["attempts"].get(pkg, 0)
            print(f"  - {pkg} (尝试 {attempts} 次)")

    print(f"\n状态文件: {project_path / STATE_FILE}")
    print(f"命令日志: {project_path / COMMANDS_LOG_FILE}")

    if generate_report and not dry_run:
        print("\n" + "=" * 60)
        print("生成环境配置报告...")

        try:
            from generate_report import generate_report, save_report

            report = generate_report(str(project_path))
            report_file = save_report(project_path, report)
            print(f"报告已生成: {report_file}")
        except ImportError:
            print("提示: 运行 generate_report.py 生成详细报告")

    print("\n" + "=" * 60)

    return {
        "success": success_count,
        "failed": fail_count,
        "skipped": skip_count,
        "commands": commands_run,
    }


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
echo "========================================"
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
    parser.add_argument("--dry-run", action="store_true", help="模拟运行")
    parser.add_argument(
        "--generate-script", action="store_true", help="生成bash安装脚本"
    )
    parser.add_argument("--no-report", action="store_true", help="不生成报告")
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
        smart_install(
            args.path,
            args.requirements,
            args.dry_run,
            generate_report=not args.no_report,
        )


if __name__ == "__main__":
    main()
