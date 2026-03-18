#!/usr/bin/env python3
"""
依赖静态分析工具
扫描Python代码中的import语句，对比requirements.txt检测缺失依赖
"""

import ast
import argparse
import json
import re
import sys
from pathlib import Path
from collections import defaultdict


STDLIB_MODULES = {
    "abc",
    "argparse",
    "array",
    "ast",
    "asyncio",
    "atexit",
    "base64",
    "binascii",
    "bisect",
    "builtins",
    "bz2",
    "calendar",
    "cmath",
    "cmd",
    "code",
    "codecs",
    "collections",
    "colorsys",
    "concurrent",
    "configparser",
    "contextlib",
    "copy",
    "copyreg",
    "csv",
    "ctypes",
    "dataclasses",
    "datetime",
    "dbm",
    "decimal",
    "difflib",
    "dis",
    "doctest",
    "email",
    "enum",
    "errno",
    "faulthandler",
    "fcntl",
    "filecmp",
    "fileinput",
    "fnmatch",
    "fractions",
    "ftplib",
    "functools",
    "gc",
    "getopt",
    "getpass",
    "gettext",
    "glob",
    "graphlib",
    "grp",
    "gzip",
    "hashlib",
    "heapq",
    "hmac",
    "html",
    "http",
    "imaplib",
    "imghdr",
    "importlib",
    "inspect",
    "io",
    "ipaddress",
    "itertools",
    "json",
    "keyword",
    "linecache",
    "locale",
    "logging",
    "lzma",
    "mailbox",
    "marshal",
    "math",
    "mimetypes",
    "mmap",
    "multiprocessing",
    "netrc",
    "numbers",
    "operator",
    "optparse",
    "os",
    "pathlib",
    "pdb",
    "pickle",
    "pipes",
    "pkgutil",
    "platform",
    "plistlib",
    "poplib",
    "posix",
    "posixpath",
    "pprint",
    "profile",
    "pstats",
    "pty",
    "pwd",
    "py_compile",
    "pyclbr",
    "pydoc",
    "queue",
    "quopri",
    "random",
    "re",
    "readline",
    "reprlib",
    "resource",
    "rlcompleter",
    "runpy",
    "sched",
    "secrets",
    "select",
    "selectors",
    "shelve",
    "shlex",
    "shutil",
    "signal",
    "site",
    "smtpd",
    "smtplib",
    "sndhdr",
    "socket",
    "socketserver",
    "spwd",
    "sqlite3",
    "ssl",
    "stat",
    "statistics",
    "string",
    "stringprep",
    "struct",
    "subprocess",
    "sunau",
    "symtable",
    "sys",
    "sysconfig",
    "syslog",
    "tabnanny",
    "tarfile",
    "telnetlib",
    "tempfile",
    "termios",
    "test",
    "textwrap",
    "threading",
    "time",
    "timeit",
    "tkinter",
    "token",
    "tokenize",
    "trace",
    "traceback",
    "tracemalloc",
    "tty",
    "types",
    "typing",
    "unicodedata",
    "unittest",
    "urllib",
    "uu",
    "uuid",
    "venv",
    "warnings",
    "wave",
    "weakref",
    "webbrowser",
    "winreg",
    "winsound",
    "wsgiref",
    "xdrlib",
    "xml",
    "xmlrpc",
    "zipapp",
    "zipfile",
    "zipimport",
    "zlib",
    "_thread",
}


PACKAGE_NAME_MAP = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "sklearn": "scikit-learn",
    "torch": "torch",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "mxnet": "mxnet",
    "np": "numpy",
    "pd": "pandas",
    "plt": "matplotlib",
    "sns": "seaborn",
    "tqdm": "tqdm",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "usb": "pyusb",
    "serial": "pyserial",
    "Crypto": "pycryptodome",
    "OpenSSL": "pyopenssl",
    "skimage": "scikit-image",
    "Bio": "biopython",
    "google": "google-api-python-client",
    "googleapiclient": "google-api-python-client",
    "pymongo": "pymongo",
    "MySQLdb": "mysqlclient",
    "psycopg2": "psycopg2-binary",
    "ignite": "pytorch-ignite",
    "mmcv": "mmcv",
    "mmdet": "mmdet",
    "mmseg": "mmsegmentation",
    "mmaction": "mmaction2",
    "peft": "peft",
    "diffusers": "diffusers",
    "transformers": "transformers",
    "accelerate": "accelerate",
    "datasets": "datasets",
    "huggingface_hub": "huggingface_hub",
    "bitsandbytes": "bitsandbytes",
    "xformers": "xformers",
    "flash_attn": "flash-attn",
    "triton": "triton",
    "deepspeed": "deepspeed",
    "wandb": "wandb",
    "mlflow": "mlflow",
    "tensorboard": "tensorboard",
    "onnx": "onnx",
    "onnxruntime": "onnxruntime",
    "tensorrt": "tensorrt",
    "timm": "timm",
    "einops": "einops",
    "omegaconf": "omegaconf",
    "hydra": "hydra-core",
    "albumentations": "albumentations",
    "imgaug": "imgaug",
    "lap": "lap",
    "cython": "cython",
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "pandas": "pandas",
    "requests": "requests",
    "flask": "flask",
    "django": "django",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "gunicorn": "gunicorn",
    "celery": "celery",
    "redis": "redis",
    "boto3": "boto3",
    "botocore": "botocore",
    "s3fs": "s3fs",
    "gcsfs": "gcsfs",
    "fsspec": "fsspec",
    "pyarrow": "pyarrow",
    "polars": "polars",
    "dask": "dask",
    "ray": "ray",
    "cupy": "cupy-cuda11x",
    "numba": "numba",
    "cytoolz": "cytoolz",
    "toolz": "toolz",
    "pytest": "pytest",
    "black": "black",
    "ruff": "ruff",
    "mypy": "mypy",
    "flake8": "flake8",
    "isort": "isort",
    "pre-commit": "pre-commit",
}


def parse_requirements(req_file):
    """解析requirements.txt"""
    requirements = set()

    if not Path(req_file).exists():
        return requirements

    content = Path(req_file).read_text(encoding="utf-8")

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        pkg = (
            line.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("~=")[0]
            .split("[")[0]
        )
        pkg = pkg.strip().lower()
        if pkg and not pkg.startswith("-r") and not pkg.startswith("http"):
            requirements.add(pkg)

    return requirements


def scan_imports_in_file(file_path):
    """扫描单个Python文件的import语句"""
    imports = set()

    try:
        content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    imports.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    imports.add(module)
    except SyntaxError:
        pass
    except Exception:
        pass

    return imports


def scan_directory(directory, exclude_dirs=None):
    """扫描目录下所有Python文件"""
    if exclude_dirs is None:
        exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            "node_modules",
            ".tox",
            "build",
            "dist",
            "egg-info",
            ".eggs",
            "site-packages",
            "anaconda3",
            "miniconda3",
        }

    all_imports = set()
    file_count = 0

    for py_file in Path(directory).rglob("*.py"):
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        imports = scan_imports_in_file(py_file)
        all_imports.update(imports)
        file_count += 1

    return all_imports, file_count


def get_package_name(import_name):
    """将import名称转换为pip包名"""
    import_lower = import_name.lower()

    if import_lower in PACKAGE_NAME_MAP:
        return PACKAGE_NAME_MAP[import_lower]

    if import_lower in STDLIB_MODULES:
        return None

    if import_name in PACKAGE_NAME_MAP:
        return PACKAGE_NAME_MAP[import_name]

    return import_lower


def analyze_dependencies(project_path):
    """分析项目依赖"""
    project_path = Path(project_path)

    print(f"分析项目: {project_path}")
    print("=" * 60)

    print("\n[扫描代码]")
    imports, file_count = scan_directory(project_path)
    print(f"  扫描文件数: {file_count}")
    print(f"  发现import数: {len(imports)}")

    print("\n[解析requirements]")
    req_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements/common.txt",
        "requirements/base.txt",
    ]

    all_requirements = set()
    for req_file in req_files:
        req_path = project_path / req_file
        if req_path.exists():
            reqs = parse_requirements(req_path)
            all_requirements.update(reqs)
            print(f"  {req_file}: {len(reqs)} 个依赖")

    if not all_requirements:
        print("  未找到requirements.txt")

    print("\n[分析缺失依赖]")
    third_party_imports = set()
    for imp in imports:
        pkg = get_package_name(imp)
        if pkg:
            third_party_imports.add(pkg)

    missing = third_party_imports - all_requirements - STDLIB_MODULES

    if missing:
        print(f"  发现 {len(missing)} 个可能缺失的依赖:")
        for pkg in sorted(missing):
            print(f"    - {pkg}")
    else:
        print("  未发现缺失依赖")

    print("\n[分析未使用的依赖]")
    unused = all_requirements - third_party_imports

    if unused:
        print(f"  发现 {len(unused)} 个可能未使用的依赖:")
        for pkg in sorted(unused):
            if pkg not in ["pip", "setuptools", "wheel"]:
                print(f"    - {pkg}")
    else:
        print("  未发现未使用依赖")

    print("\n[AI框架检测]")
    ai_frameworks = {
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "transformers": "Transformers",
        "diffusers": "Diffusers",
        "accelerate": "Accelerate",
        "mmcv": "MMCV",
        "mmdet": "MMDetection",
        "mmseg": "MMSegmentation",
        "mmaction": "MMAction2",
        "peft": "PEFT",
        "bitsandbytes": "BitsAndBytes",
        "flash_attn": "Flash Attention",
        "xformers": "xFormers",
        "deepspeed": "DeepSpeed",
        "timm": "TIMM",
    }

    detected = []
    for pkg, framework in ai_frameworks.items():
        if pkg in third_party_imports:
            detected.append(framework)

    if detected:
        for fw in detected:
            print(f"  - {fw}")
    else:
        print("  未检测到常用AI框架")

    print("\n" + "=" * 60)

    return {
        "imports": list(imports),
        "third_party": list(third_party_imports),
        "requirements": list(all_requirements),
        "missing": list(missing),
        "unused": list(unused),
        "frameworks": detected,
        "file_count": file_count,
    }


def main():
    parser = argparse.ArgumentParser(description="依赖静态分析")
    parser.add_argument("path", help="项目路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument(
        "--generate-req", action="store_true", help="生成缺失依赖的pip install命令"
    )
    args = parser.parse_args()

    result = analyze_dependencies(args.path)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.generate_req and result["missing"]:
        print("\n[安装命令]")
        print("pip install " + " ".join(sorted(result["missing"])))


if __name__ == "__main__":
    main()
