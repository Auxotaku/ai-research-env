#!/usr/bin/env python3
"""
仓库依赖分析工具
分析GitHub仓库的README、requirements.txt、setup.py等
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def parse_requirements(file_path):
    """解析requirements.txt"""
    requirements = []

    if not Path(file_path).exists():
        return requirements

    content = Path(file_path).read_text(encoding="utf-8")

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "==" in line:
            pkg, version = line.split("==", 1)
            requirements.append(
                {"name": pkg.strip(), "version": version.strip(), "op": "=="}
            )
        elif ">=" in line:
            pkg, version = line.split(">=", 1)
            requirements.append(
                {"name": pkg.strip(), "version": version.strip(), "op": ">="}
            )
        elif "<=" in line:
            pkg, version = line.split("<=", 1)
            requirements.append(
                {"name": pkg.strip(), "version": version.strip(), "op": "<="}
            )
        elif "~=" in line:
            pkg, version = line.split("~=", 1)
            requirements.append(
                {"name": pkg.strip(), "version": version.strip(), "op": "~="}
            )
        else:
            if not any(x in line for x in ["http", "git+", "-r "]):
                requirements.append({"name": line, "version": None, "op": None})

    return requirements


def parse_setup_py(file_path):
    """解析setup.py提取依赖"""
    requirements = []

    if not Path(file_path).exists():
        return requirements

    content = Path(file_path).read_text(encoding="utf-8")

    install_requires_match = re.search(
        r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
    )
    if install_requires_match:
        deps_str = install_requires_match.group(1)
        for line in deps_str.split("\n"):
            line = line.strip()
            if line and line.startswith(("'", '"')):
                line = line.strip("'\"")
                if "==" in line:
                    pkg, version = line.split("==", 1)
                    requirements.append(
                        {"name": pkg.strip(), "version": version.strip(), "op": "=="}
                    )
                elif ">=" in line:
                    pkg, version = line.split(">=", 1)
                    requirements.append(
                        {"name": pkg.strip(), "version": version.strip(), "op": ">="}
                    )
                else:
                    requirements.append({"name": line, "version": None, "op": None})

    return requirements


def parse_pyproject_toml(file_path):
    """解析pyproject.toml"""
    requirements = []

    if not Path(file_path).exists():
        return requirements

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        deps = data.get("project", {}).get("dependencies", [])
        if not deps:
            deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            deps = [
                f"{k}=={v}" if isinstance(v, str) and not v.startswith("^") else k
                for k, v in deps.items()
                if k != "python"
            ]

        for dep in deps:
            if isinstance(dep, str):
                if "==" in dep:
                    pkg, version = dep.split("==", 1)
                    requirements.append(
                        {"name": pkg.strip(), "version": version.strip(), "op": "=="}
                    )
                elif ">=" in dep:
                    pkg, version = dep.split(">=", 1)
                    requirements.append(
                        {"name": pkg.strip(), "version": version.strip(), "op": ">="}
                    )
                else:
                    requirements.append({"name": dep, "version": None, "op": None})
    except Exception as e:
        print(f"解析pyproject.toml失败: {e}")

    return requirements


def parse_environment_yml(file_path):
    """解析conda environment.yml"""
    requirements = []

    if not Path(file_path).exists():
        return requirements

    try:
        import yaml

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        deps = data.get("dependencies", [])
        pip_deps = None

        for dep in deps:
            if isinstance(dep, dict) and "pip" in dep:
                pip_deps = dep["pip"]
            elif isinstance(dep, str):
                requirements.append(
                    {"name": dep, "version": None, "op": None, "source": "conda"}
                )

        if pip_deps:
            for dep in pip_deps:
                if "==" in dep:
                    pkg, version = dep.split("==", 1)
                    requirements.append(
                        {
                            "name": pkg.strip(),
                            "version": version.strip(),
                            "op": "==",
                            "source": "pip",
                        }
                    )
                else:
                    requirements.append(
                        {"name": dep, "version": None, "op": None, "source": "pip"}
                    )
    except Exception as e:
        print(f"解析environment.yml失败: {e}")

    return requirements


def analyze_readme(file_path):
    """分析README提取安装说明"""
    instructions = {
        "install_commands": [],
        "requirements": [],
        "python_version": None,
        "cuda_requirements": None,
    }

    if not Path(file_path).exists():
        return instructions

    content = Path(file_path).read_text(encoding="utf-8")

    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)

    for block in code_blocks:
        lines = block.strip().split("\n")
        for line in lines:
            line = line.strip()

            if "pip install" in line:
                instructions["install_commands"].append(line)
            elif "conda install" in line:
                instructions["install_commands"].append(line)
            elif "python setup.py" in line:
                instructions["install_commands"].append(line)

    python_match = re.search(r"Python\s*>=?\s*(\d+\.\d+)", content)
    if python_match:
        instructions["python_version"] = python_match.group(1)

    cuda_match = re.search(r"CUDA\s*(\d+\.\d+)", content)
    if cuda_match:
        instructions["cuda_requirements"] = cuda_match.group(1)

    return instructions


def detect_framework(requirements):
    """检测项目使用的框架"""
    frameworks = []

    framework_patterns = {
        "PyTorch": ["torch", "pytorch", "torchvision", "torchaudio"],
        "TensorFlow": ["tensorflow", "tf", "tensorboard"],
        "Transformers": ["transformers", "huggingface"],
        "Diffusers": ["diffusers"],
        "MMCV": ["mmcv", "mmengine"],
        "MMDetection": ["mmdet", "mmdetection"],
        "MMAction": ["mmaction", "mmaction2"],
        "MMSegmentation": ["mmseg", "mmsegmentation"],
        "Accelerate": ["accelerate"],
        "DeepSpeed": ["deepspeed"],
        "PEFT": ["peft"],
        "BitsAndBytes": ["bitsandbytes"],
        "Flash Attention": ["flash-attn"],
        "xFormers": ["xformers"],
        "ONNX": ["onnx", "onnxruntime"],
        "TensorRT": ["tensorrt"],
    }

    req_names = [r["name"].lower() for r in requirements]

    for framework, patterns in framework_patterns.items():
        if any(p.lower() in " ".join(req_names) for p in patterns):
            frameworks.append(framework)

    return frameworks


def analyze_repo(repo_path):
    """分析整个仓库"""
    repo_path = Path(repo_path)

    print(f"分析仓库: {repo_path}")
    print("=" * 60)

    all_requirements = []

    req_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements/*.txt",
        "setup.py",
        "pyproject.toml",
        "environment.yml",
        "environment.yaml",
    ]

    for pattern in req_files:
        for file_path in repo_path.glob(pattern):
            print(f"\n发现: {file_path.name}")

            if file_path.suffix == ".txt":
                reqs = parse_requirements(file_path)
            elif file_path.name == "setup.py":
                reqs = parse_setup_py(file_path)
            elif file_path.name == "pyproject.toml":
                reqs = parse_pyproject_toml(file_path)
            elif file_path.suffix in [".yml", ".yaml"]:
                reqs = parse_environment_yml(file_path)
            else:
                continue

            if reqs:
                print(f"  依赖数量: {len(reqs)}")
                all_requirements.extend(reqs)

    readme_files = ["README.md", "README.rst", "README.txt"]
    for readme in readme_files:
        readme_path = repo_path / readme
        if readme_path.exists():
            print(f"\n分析: {readme}")
            instructions = analyze_readme(readme_path)

            if instructions["install_commands"]:
                print("  安装命令:")
                for cmd in instructions["install_commands"][:5]:
                    print(f"    {cmd}")

            if instructions["python_version"]:
                print(f"  Python版本要求: >= {instructions['python_version']}")

            if instructions["cuda_requirements"]:
                print(f"  CUDA版本要求: {instructions['cuda_requirements']}")

    frameworks = detect_framework(all_requirements) if all_requirements else []

    if all_requirements:
        print("\n" + "=" * 60)
        print("检测到的框架:")
        for fw in frameworks:
            print(f"  - {fw}")

        print("\n" + "=" * 60)
        print("关键依赖:")
        key_deps = [
            "torch",
            "tensorflow",
            "transformers",
            "diffusers",
            "accelerate",
            "mmcv",
            "mmdet",
            "mmaction",
            "cuda",
            "numpy",
            "pillow",
            "opencv",
        ]
        for req in all_requirements:
            if any(k in req["name"].lower() for k in key_deps):
                ver_str = f"{req['op']}{req['version']}" if req["version"] else ""
                print(f"  {req['name']}{ver_str}")

    return {
        "requirements": all_requirements,
        "frameworks": frameworks if all_requirements else [],
    }


def main():
    parser = argparse.ArgumentParser(description="仓库依赖分析")
    parser.add_argument("path", help="仓库路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()

    result = analyze_repo(args.path)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
