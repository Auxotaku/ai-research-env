#!/usr/bin/env python3
"""
模型下载助手
支持HuggingFace、ModelScope，自动使用镜像站
适用于Linux服务器科研环境

特性：
1. ModelScope优先检查
2. 大文件下载告知用户
3. 提供下载位置建议
4. 安全约束：不执行删除操作
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def get_hf_endpoint():
    """获取HuggingFace镜像地址"""
    return os.environ.get("HF_ENDPOINT", "https://huggingface.co")


def set_hf_mirror(url="https://hf-mirror.com"):
    """设置HuggingFace镜像"""
    os.environ["HF_ENDPOINT"] = url
    print(f"已设置HF_ENDPOINT={url}")


def get_default_cache_dir():
    """获取默认缓存目录"""
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home)

    return Path.home() / ".cache" / "huggingface"


def suggest_download_location(model_id, project_path=None):
    """建议下载位置"""
    cache_dir = get_default_cache_dir()

    suggestions = []

    suggestions.append(
        {
            "path": str(cache_dir / "hub" / f"models--{model_id.replace('/', '--')}"),
            "description": "HuggingFace默认缓存位置 (推荐，可被多个项目共享)",
            "is_default": True,
        }
    )

    if project_path:
        project_models = Path(project_path) / "models" / model_id.split("/")[-1]
        suggestions.append(
            {
                "path": str(project_models),
                "description": "项目目录内 (适合项目专用模型)",
                "is_default": False,
            }
        )

    suggestions.append(
        {
            "path": f"/data/models/{model_id.replace('/', '--')}",
            "description": "服务器共享模型目录 (适合团队共享)",
            "is_default": False,
        }
    )

    return suggestions


def check_modelscope_availability(model_id):
    """检查ModelScope是否有该模型"""
    try:
        result = subprocess.run(
            [
                "python",
                "-c",
                f'''
from modelscope.hub.api import HubApi
api = HubApi()
try:
    model_info = api.get_model(model_id="{model_id}")
    print("AVAILABLE")
except:
    pass
''',
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "AVAILABLE" in result.stdout
    except:
        return False


def get_model_size_estimate(model_id, source="huggingface"):
    """估算模型大小"""
    size_info = {
        "7b": "~14GB (FP16) / ~4GB (4-bit)",
        "13b": "~26GB (FP16) / ~8GB (4-bit)",
        "30b": "~60GB (FP16) / ~16GB (4-bit)",
        "70b": "~140GB (FP16) / ~40GB (4-bit)",
        "1.3b": "~2.6GB (FP16)",
        "3b": "~6GB (FP16)",
    }

    model_lower = model_id.lower()
    for key, size in size_info.items():
        if key in model_lower:
            return size

    return "未知 (请查看模型页面)"


def download_from_modelscope(model_id, local_dir=None, revision=None):
    """从ModelScope下载模型"""
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("错误: 未安装modelscope")
        print("安装: pip install modelscope")
        return False

    print(f"\n[ModelScope下载]")
    print(f"  模型ID: {model_id}")

    if local_dir is None:
        local_dir = get_default_cache_dir() / "modelscope" / model_id.replace("/", "--")

    print(f"  目标位置: {local_dir}")
    print(f"  估算大小: {get_model_size_estimate(model_id)}")

    try:
        print("\n开始下载...")
        path = snapshot_download(
            model_id, cache_dir=str(local_dir.parent), revision=revision
        )
        print(f"\n下载完成! 文件保存在: {path}")
        return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False


def download_from_huggingface(
    repo_id, repo_type="model", local_dir=None, token=None, use_mirror=True
):
    """从HuggingFace下载模型"""
    try:
        from huggingface_hub import snapshot_download, login
    except ImportError:
        print("错误: 未安装huggingface_hub")
        print("安装: pip install huggingface_hub")
        return False

    if token:
        login(token=token)
        print("已使用token登录")

    if use_mirror:
        set_hf_mirror()

    endpoint = get_hf_endpoint()
    print(f"\n[HuggingFace下载]")
    print(f"  仓库ID: {repo_id}")
    print(f"  类型: {repo_type}")
    print(f"  镜像源: {endpoint}")

    if local_dir is None:
        local_dir = (
            get_default_cache_dir() / "hub" / f"models--{repo_id.replace('/', '--')}"
        )

    print(f"  目标位置: {local_dir}")
    print(f"  估算大小: {get_model_size_estimate(repo_id)}")

    try:
        print("\n开始下载...")
        snapshot_download(
            repo_id=repo_id,
            repo_type=repo_type,
            local_dir=str(local_dir),
            endpoint=endpoint,
            resume_download=True,
        )
        print(f"\n下载完成! 文件保存在: {local_dir}")
        return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False


def download_with_git(repo_url, local_dir=None):
    """使用git clone下载"""
    if "huggingface.co" in repo_url:
        endpoint = get_hf_endpoint()
        if "hf-mirror.com" in endpoint:
            repo_url = repo_url.replace("huggingface.co", "hf-mirror.com")
            print(f"已替换为镜像地址: {repo_url}")

    if not local_dir:
        local_dir = repo_url.split("/")[-1].replace(".git", "")

    print(f"\n[Git克隆]")
    print(f"  URL: {repo_url}")
    print(f"  目标位置: {local_dir}")

    try:
        result = subprocess.run(
            ["git", "clone", repo_url, str(local_dir)], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"克隆完成! 文件保存在: {local_dir}")
            return True
        else:
            print(f"克隆失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"Git命令失败: {e}")
        return False


def smart_download(
    model_id, local_dir=None, project_path=None, prefer_modelscope=True, token=None
):
    """智能下载：优先ModelScope，失败则HuggingFace"""
    print("=" * 60)
    print("模型下载助手")
    print("=" * 60)

    suggestions = suggest_download_location(model_id, project_path)

    print("\n[建议下载位置]")
    for i, sug in enumerate(suggestions, 1):
        marker = " (默认)" if sug["is_default"] else ""
        print(f"  {i}. {sug['path']}{marker}")
        print(f"     {sug['description']}")

    if local_dir is None:
        local_dir = suggestions[0]["path"]

    print(f"\n[选择的下载位置]")
    print(f"  {local_dir}")

    print(f"\n[模型大小估算]")
    print(f"  {get_model_size_estimate(model_id)}")

    if prefer_modelscope:
        print(f"\n[检查ModelScope可用性]")
        print(f"  正在检查...")

        if check_modelscope_availability(model_id):
            print(f"  ModelScope: 可用")
            print(f"\n优先从ModelScope下载...")
            if download_from_modelscope(model_id, local_dir):
                return True
            print("ModelScope下载失败，尝试HuggingFace...")
        else:
            print(f"  ModelScope: 未找到")

    print(f"\n[从HuggingFace下载]")
    if download_from_huggingface(model_id, local_dir=local_dir, token=token):
        return True

    print("\n" + "=" * 60)
    print("下载失败!")
    print("建议:")
    print("  1. 检查模型ID是否正确")
    print("  2. 尝试设置代理: export HTTP_PROXY=http://your-proxy:port")
    print("  3. 检查网络连接")
    print("=" * 60)

    return False


def list_cached_models():
    """列出已缓存模型"""
    cache_dir = get_default_cache_dir()

    print(f"缓存目录: {cache_dir}")
    print()

    hub_dir = cache_dir / "hub"
    if not hub_dir.exists():
        print("未找到缓存模型")
        return

    print("已缓存模型:")
    total_size = 0

    for item in hub_dir.iterdir():
        if item.is_dir() and item.name.startswith("models--"):
            model_name = item.name.replace("models--", "").replace("--", "/")

            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
            size_gb = size / (1024**3)
            total_size += size

            print(f"  {model_name}")
            print(f"    大小: {size_gb:.2f} GB")
            print(f"    路径: {item}")
            print()

    print(f"总缓存大小: {total_size / (1024**3):.2f} GB")


def main():
    parser = argparse.ArgumentParser(description="模型下载助手")
    parser.add_argument(
        "model_id", nargs="?", help="模型ID (如: meta-llama/Llama-2-7b-hf)"
    )
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument(
        "--type",
        "-t",
        choices=["model", "dataset", "space"],
        default="model",
        help="仓库类型",
    )
    parser.add_argument("--token", help="HuggingFace token")
    parser.add_argument(
        "--mirror", "-m", action="store_true", help="使用hf-mirror.com镜像"
    )
    parser.add_argument(
        "--no-modelscope", action="store_true", help="不优先从ModelScope下载"
    )
    parser.add_argument("--project", "-p", help="项目路径(用于建议下载位置)")
    parser.add_argument("--git", action="store_true", help="使用git clone下载")
    parser.add_argument("--list-cache", action="store_true", help="列出已缓存模型")
    parser.add_argument("--modelscope", help="直接从ModelScope下载 (指定model_id)")

    args = parser.parse_args()

    if args.list_cache:
        list_cached_models()
        return

    if args.modelscope:
        download_from_modelscope(args.modelscope, args.output)
        return

    if not args.model_id:
        parser.print_help()
        print("\n示例:")
        print("  # 智能下载 (优先ModelScope)")
        print("  python download_model.py meta-llama/Llama-2-7b-hf")
        print()
        print("  # 从ModelScope下载")
        print("  python download_model.py --modelscope Qwen/Qwen-7B-Chat")
        print()
        print("  # 使用HuggingFace镜像")
        print("  python download_model.py meta-llama/Llama-2-7b-hf --mirror")
        print()
        print("  # 指定下载位置")
        print(
            "  python download_model.py meta-llama/Llama-2-7b-hf -o /data/models/llama2-7b"
        )
        return

    if args.git:
        repo_url = f"https://huggingface.co/{args.model_id}"
        download_with_git(repo_url, args.output)
    else:
        smart_download(
            args.model_id,
            local_dir=args.output,
            project_path=args.project,
            prefer_modelscope=not args.no_modelscope,
            token=args.token,
        )


if __name__ == "__main__":
    main()
