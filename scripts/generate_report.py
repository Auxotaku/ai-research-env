#!/usr/bin/env python3
"""
环境配置报告生成器
汇总安装过程、模型位置、使用指南，生成最终报告
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path


REPORT_FILE = "environment_setup_report.md"
STATE_FILE = ".install_state.json"
DOWNLOAD_HISTORY_FILE = ".download_history.json"


def load_install_state(project_path):
    """加载安装状态"""
    state_file = Path(project_path) / STATE_FILE
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except:
            pass
    return {"installed": [], "failed": [], "attempts": {}}


def load_download_history(project_path):
    """加载下载历史"""
    history_file = Path(project_path) / DOWNLOAD_HISTORY_FILE
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except:
            pass
    return []


def analyze_readme(project_path):
    """分析README提取关键信息"""
    readme_path = None
    for name in ["README.md", "README.rst", "README.txt"]:
        candidate = Path(project_path) / name
        if candidate.exists():
            readme_path = candidate
            break

    if not readme_path:
        return None

    content = readme_path.read_text(encoding="utf-8", errors="ignore")

    info = {
        "path": str(readme_path),
        "usage_examples": [],
        "requirements": [],
        "python_version": None,
        "cuda_version": None,
    }

    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)

    for block in code_blocks:
        lines = block.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("python ") or line.startswith("python3 "):
                if not line.startswith("python -m pip"):
                    info["usage_examples"].append(line)
            elif line.startswith("./") and not "install" in line.lower():
                info["usage_examples"].append(line)

    py_match = re.search(r"Python\s*>=?\s*(\d+\.\d+)", content)
    if py_match:
        info["python_version"] = py_match.group(1)

    cuda_match = re.search(r"CUDA\s*(\d+\.\d+)", content)
    if cuda_match:
        info["cuda_version"] = cuda_match.group(1)

    return info


def detect_project_type(project_path):
    """检测项目类型"""
    project_path = Path(project_path)

    indicators = {
        "LLM": ["transformers", "peft", "bitsandbytes", "accelerate", "vllm"],
        "Video Generation": ["diffusers", "omegaconf", "einops", "xformers"],
        "Image Generation": ["diffusers", "controlnet", "compel"],
        "Object Detection": ["mmdet", "detectron2", "yolov"],
        "Video Understanding": ["mmaction", "timesformer", "videomae"],
        "Segmentation": ["mmseg", "segment-anything"],
        "General PyTorch": ["torch", "torchvision"],
    }

    requirements_files = [
        project_path / "requirements.txt",
        project_path / "setup.py",
        project_path / "pyproject.toml",
    ]

    all_deps = []
    for req_file in requirements_files:
        if req_file.exists():
            content = req_file.read_text(encoding="utf-8", errors="ignore")
            all_deps.append(content.lower())

    combined = " ".join(all_deps)

    detected = []
    for ptype, keywords in indicators.items():
        for kw in keywords:
            if kw.lower() in combined:
                detected.append(ptype)
                break

    return detected if detected else ["Unknown"]


def get_conda_env_name():
    """获取当前conda环境名"""
    return os.environ.get("CONDA_DEFAULT_ENV", None)


def get_python_version():
    """获取Python版本"""
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_cuda_version():
    """获取CUDA版本"""
    try:
        import subprocess

        result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            match = re.search(r"release\s+(\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    return None


def generate_report(project_path, env_name=None, additional_notes=None):
    """生成完整报告"""
    project_path = Path(project_path).resolve()

    install_state = load_install_state(project_path)
    download_history = load_download_history(project_path)
    readme_info = analyze_readme(project_path)
    project_types = detect_project_type(project_path)

    current_env = env_name or get_conda_env_name() or "未知"
    python_ver = get_python_version()
    cuda_ver = get_cuda_version()

    report = f"""# 环境配置报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**项目路径**: `{project_path}`

---

## 环境概览

| 项目 | 值 |
|------|-----|
| 项目类型 | {", ".join(project_types)} |
| Python版本 | {python_ver} |
| CUDA版本 | {cuda_ver or "未检测到"} |
| 虚拟环境 | {current_env} |

---

## 安装结果

**成功安装**: {len(install_state.get("installed", []))} 个包
**安装失败**: {len(install_state.get("failed", []))} 个包

"""

    if install_state.get("installed"):
        report += "### 成功安装的包\n\n```\n"
        for pkg in install_state["installed"][:20]:
            report += f"{pkg}\n"
        if len(install_state["installed"]) > 20:
            report += f"... 共 {len(install_state['installed'])} 个\n"
        report += "```\n\n"

    if install_state.get("failed"):
        report += "### 安装失败的包\n\n"
        for pkg in install_state["failed"]:
            attempts = install_state.get("attempts", {}).get(pkg, 0)
            report += f"- `{pkg}` (尝试 {attempts} 次)\n"
        report += "\n**建议**: 手动检查这些包的安装问题\n\n"

    if download_history:
        report += "---\n\n## 下载的模型\n\n"
        for i, item in enumerate(download_history, 1):
            report += f"### 模型 {i}\n\n"
            report += f"| 项目 | 值 |\n"
            report += f"|------|-----|\n"
            report += f"| 模型ID | `{item.get('model_id', '未知')}` |\n"
            report += f"| 来源 | {item.get('source', '未知')} |\n"
            report += f"| 本地路径 | `{item.get('local_path', '未知')}` |\n"
            report += f"| 下载时间 | {item.get('timestamp', '未知')} |\n\n"

            if item.get("commands"):
                report += "**下载命令**:\n```\n"
                for cmd in item["commands"]:
                    report += f"{cmd}\n"
                report += "```\n\n"

    if readme_info:
        report += "---\n\n## 使用指南 (来自README)\n\n"

        if readme_info.get("usage_examples"):
            report += "### 运行示例\n\n```bash\n"
            for example in readme_info["usage_examples"][:5]:
                report += f"{example}\n"
            report += "```\n\n"

        if readme_info.get("python_version"):
            report += f"**Python要求**: >={readme_info['python_version']}\n\n"

        if readme_info.get("cuda_version"):
            report += f"**CUDA要求**: {readme_info['cuda_version']}\n\n"

        report += f"**README路径**: `{readme_info['path']}`\n\n"

    report += (
        """---

## 快速开始

```bash
# 激活环境
conda activate """
        + current_env
        + """

# 进入项目目录
cd """
        + str(project_path)
        + """

# 运行项目 (参考上方使用指南)
# python train.py  # 或其他命令
```

"""
    )

    if additional_notes:
        report += "---\n\n## 补充说明\n\n" + additional_notes + "\n\n"

    report += """---

## 文件说明

| 文件 | 说明 |
|------|------|
| `.install_state.json` | 安装状态记录 |
| `.download_history.json` | 模型下载历史 |
| 本报告 | 环境配置总结 |

---

*报告由 AI Research Environment Skill 自动生成*
"""

    return report


def save_report(project_path, report):
    """保存报告"""
    report_file = Path(project_path) / REPORT_FILE
    report_file.write_text(report, encoding="utf-8")
    return report_file


def main():
    parser = argparse.ArgumentParser(description="环境配置报告生成器")
    parser.add_argument("path", nargs="?", default=".", help="项目路径")
    parser.add_argument("--env", "-e", help="虚拟环境名称")
    parser.add_argument("--notes", "-n", help="补充说明")
    parser.add_argument("--output", "-o", help="报告输出路径")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()

    print(f"生成环境配置报告...")
    print(f"项目路径: {project_path}")

    report = generate_report(project_path, args.env, args.notes)

    output_path = Path(args.output) if args.output else project_path
    report_file = save_report(output_path, report)

    print(f"\n报告已生成: {report_file}")
    print("\n" + "=" * 60)
    print(report[:500] + "..." if len(report) > 500 else report)


if __name__ == "__main__":
    main()
