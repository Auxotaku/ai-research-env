#!/usr/bin/env python3
"""
模型下载助手
支持HuggingFace、ModelScope，自动使用镜像站
适用于Linux服务器科研环境

特性：
1. ModelScope智能搜索（根据模型名搜索，而非精确匹配ID）
2. 大文件下载告知用户
3. 提供下载位置建议
4. 安全约束：不执行删除操作
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DOWNLOAD_LOG_FILE = ".download_history.json"


def get_hf_endpoint():
    """获取HuggingFace镜像地址"""
    return os.environ.get("HF_ENDPOINT", "https://huggingface.co")


def set_hf_mirror(url="https://hf-mirror.com"):
    """设置HuggingFace镜像"""
    os.environ["HF_ENDPOINT"] = url
    return f"export HF_ENDPOINT={url}"


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


def search_modelscope_models(keyword, limit=5):
    """在ModelScope搜索模型"""
    try:
        code = f'''
import sys
try:
    from modelscope.msdatasets import MsDataset
    from modelscope.hub.api import HubApi
    
    api = HubApi()
    result = api.list_models(filter="{keyword}", limit={limit})
    
    for model in result:
        print(f"MODEL:{{model.id}}|{{model.name}}")
except ImportError:
    print("MODELSCOPE_NOT_INSTALLED")
except Exception as e:
    print(f"ERROR:{{e}}")
'''
        result = subprocess.run(
            ["python", "-c", code], capture_output=True, text=True, timeout=60
        )

        if "MODELSCOPE_NOT_INSTALLED" in result.stdout:
            return None, "ModelScope未安装，运行: pip install modelscope"

        models = []
        for line in result.stdout.strip().split("\n"):
            if line.startswith("MODEL:"):
                parts = line[6:].split("|")
                if len(parts) >= 2:
                    models.append({"id": parts[0], "name": parts[1]})

        return models, None
    except subprocess.TimeoutExpired:
        return None, "搜索超时"
    except Exception as e:
        return None, str(e)


def download_from_modelscope(
    model_id, local_dir=None, revision=None, log_commands=None
):
    """从ModelScope下载模型"""
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("错误: 未安装modelscope")
        print("安装: pip install modelscope")
        return False, None

    print(f"\n[ModelScope下载]")
    print(f"  模型ID: {model_id}")

    if local_dir is None:
        local_dir = get_default_cache_dir() / "modelscope" / model_id.replace("/", "--")

    print(f"  目标位置: {local_dir}")

    commands = []
    cmd = f"from modelscope import snapshot_download; snapshot_download('{model_id}')"
    commands.append(f'python -c "{cmd}"')

    try:
        print("\n开始下载...")
        path = snapshot_download(
            model_id, cache_dir=str(local_dir.parent), revision=revision
        )
        print(f"\n下载完成! 文件保存在: {path}")

        if log_commands is not None:
            log_commands.extend(commands)

        return True, str(path)
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False, None


def download_from_huggingface(
    repo_id,
    repo_type="model",
    local_dir=None,
    token=None,
    use_mirror=True,
    log_commands=None,
):
    """从HuggingFace下载模型"""
    try:
        from huggingface_hub import snapshot_download, login
    except ImportError:
        print("错误: 未安装huggingface_hub")
        print("安装: pip install huggingface_hub")
        return False, None

    commands = []

    if use_mirror:
        mirror_cmd = set_hf_mirror()
        commands.append(mirror_cmd)

    if token:
        login(token=token)
        print("已使用token登录")

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

    cmd = f"from huggingface_hub import snapshot_download; snapshot_download('{repo_id}', endpoint='{endpoint}')"
    commands.append(f'python -c "{cmd}"')

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

        if log_commands is not None:
            log_commands.extend(commands)

        return True, str(local_dir)
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False, None


def smart_download(
    model_id, local_dir=None, project_path=None, prefer_modelscope=True, token=None
):
    """智能下载：优先在ModelScope搜索，让用户选择"""
    print("=" * 60)
    print("模型下载助手")
    print("=" * 60)

    commands_log = []
    download_result = {
        "model_id": model_id,
        "source": None,
        "local_path": None,
        "timestamp": datetime.now().isoformat(),
        "commands": [],
    }

    if prefer_modelscope:
        model_name = model_id.split("/")[-1]
        print(f"\n[步骤1] 在ModelScope搜索模型")
        print(f"  搜索关键词: {model_name}")
        print(f"  正在搜索...")

        models, error = search_modelscope_models(model_name)

        if models:
            print(f"\n  找到 {len(models)} 个相关模型:")
            for i, m in enumerate(models, 1):
                print(f"    {i}. {m['id']}")
                print(f"       名称: {m['name']}")

            print(f"\n  是否从ModelScope下载? (输入序号选择，或按Enter跳过)")
            try:
                choice = input(
                    "  选择 [1-{}] 或 Enter 跳过: ".format(len(models))
                ).strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        selected_model = models[idx]["id"]
                        print(f"\n  已选择: {selected_model}")

                        if local_dir is None:
                            local_dir = (
                                get_default_cache_dir()
                                / "modelscope"
                                / selected_model.replace("/", "--")
                            )

                        success, path = download_from_modelscope(
                            selected_model, local_dir, log_commands=commands_log
                        )

                        if success:
                            download_result["source"] = "ModelScope"
                            download_result["local_path"] = path
                            download_result["model_id"] = selected_model
                            download_result["commands"] = commands_log
                            save_download_history(download_result, project_path)
                            return True, download_result

                        print("  ModelScope下载失败，尝试HuggingFace...")
            except (ValueError, KeyboardInterrupt):
                print("  跳过ModelScope下载")
        elif error:
            print(f"  搜索失败: {error}")
        else:
            print(f"  未找到相关模型")

    print(f"\n[步骤2] 从HuggingFace下载")
    success, path = download_from_huggingface(
        model_id, local_dir=local_dir, token=token, log_commands=commands_log
    )

    if success:
        download_result["source"] = "HuggingFace"
        download_result["local_path"] = path
        download_result["commands"] = commands_log
        save_download_history(download_result, project_path)
        return True, download_result

    print("\n" + "=" * 60)
    print("下载失败!")
    print("建议:")
    print("  1. 检查模型ID是否正确")
    print("  2. 尝试设置代理: export HTTP_PROXY=http://your-proxy:port")
    print("  3. 检查网络连接")
    print("=" * 60)

    return False, download_result


def save_download_history(result, project_path=None):
    """保存下载历史"""
    if project_path:
        history_file = Path(project_path) / DOWNLOAD_LOG_FILE
    else:
        history_file = Path.cwd() / DOWNLOAD_LOG_FILE

    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text())
        except:
            pass

    history.append(result)
    history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    print(f"\n下载历史已保存: {history_file}")


def list_cached_models():
    """列出已缓存模型"""
    cache_dir = get_default_cache_dir()
    print(f"缓存目录: {cache_dir}\n")

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
            print(f"    路径: {item}\n")

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
        "--no-modelscope", action="store_true", help="跳过ModelScope搜索"
    )
    parser.add_argument("--project", "-p", help="项目路径")
    parser.add_argument("--list-cache", action="store_true", help="列出已缓存模型")
    parser.add_argument("--modelscope-id", help="直接指定ModelScope模型ID")

    args = parser.parse_args()

    if args.list_cache:
        list_cached_models()
        return

    if args.modelscope_id:
        success, result = download_from_modelscope(args.modelscope_id, args.output)
        if success:
            print(f"\n模型已下载到: {result}")
        return

    if not args.model_id:
        parser.print_help()
        print("\n示例:")
        print("  # 智能下载 (自动搜索ModelScope)")
        print("  python download_model.py meta-llama/Llama-2-7b-hf")
        print()
        print("  # 指定ModelScope模型ID")
        print("  python download_model.py --modelscope-id Qwen/Qwen2-7B-Instruct")
        print()
        print("  # 跳过ModelScope，直接从HuggingFace下载")
        print("  python download_model.py meta-llama/Llama-2-7b-hf --no-modelscope")
        return

    success, result = smart_download(
        args.model_id,
        local_dir=args.output,
        project_path=args.project,
        prefer_modelscope=not args.no_modelscope,
        token=args.token,
    )


if __name__ == "__main__":
    main()
