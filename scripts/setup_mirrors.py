#!/usr/bin/env python3
"""
配置国内镜像源工具
支持pip、conda、HuggingFace镜像
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


MIRROR_SOURCES = {
    "tsinghua": {
        "name": "清华大学镜像站",
        "pip": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "conda": "https://mirrors.tuna.tsinghua.edu.cn/anaconda",
    },
    "aliyun": {
        "name": "阿里云镜像站",
        "pip": "https://mirrors.aliyun.com/pypi/simple",
        "conda": "https://mirrors.aliyun.com/anaconda",
    },
    "ustc": {
        "name": "中科大镜像站",
        "pip": "https://pypi.mirrors.ustc.edu.cn/simple",
        "conda": "https://mirrors.ustc.edu.cn/anaconda",
    },
    "huawei": {
        "name": "华为云镜像站",
        "pip": "https://repo.huaweicloud.com/repository/pypi/simple",
        "conda": "https://repo.huaweicloud.com/repository/anaconda",
    },
    "tencent": {
        "name": "腾讯云镜像站",
        "pip": "https://mirrors.cloud.tencent.com/pypi/simple",
        "conda": "https://mirrors.cloud.tencent.com/anaconda",
    },
}

HF_MIRRORS = {
    "hf-mirror": {
        "name": "HuggingFace镜像站 (hf-mirror.com)",
        "url": "https://hf-mirror.com",
        "env_var": "HF_ENDPOINT",
    }
}


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


def get_pip_config_file():
    """获取pip配置文件路径"""
    if platform.system() == "Windows":
        config_dir = Path(os.environ.get("APPDATA", "~")) / "pip"
    else:
        config_dir = Path.home() / ".pip"
    return (
        config_dir / "pip.conf"
        if platform.system() != "Windows"
        else config_dir / "pip.ini"
    )


def get_current_pip_mirror():
    """获取当前pip镜像源"""
    stdout, _, code = run_command(
        f"{sys.executable} -m pip config get global.index-url"
    )
    if code == 0 and stdout:
        return stdout.strip()
    return None


def setup_pip_mirror(mirror_name="tsinghua", permanent=True):
    """配置pip镜像源"""
    if mirror_name not in MIRROR_SOURCES:
        print(f"错误: 未知的镜像源 '{mirror_name}'")
        print(f"可选: {', '.join(MIRROR_SOURCES.keys())}")
        return False

    mirror = MIRROR_SOURCES[mirror_name]
    pip_url = mirror["pip"]

    print(f"配置pip镜像源: {mirror['name']} ({pip_url})")

    if permanent:
        stdout, stderr, code = run_command(
            f"{sys.executable} -m pip config set global.index-url {pip_url}"
        )
        if code != 0:
            print(f"配置失败: {stderr}")
            return False

        stdout, stderr, code = run_command(
            f"{sys.executable} -m pip config set install.trusted-host {pip_url.split('//')[1].split('/')[0]}"
        )

        config_file = get_pip_config_file()
        print(f"配置文件: {config_file}")

    print("pip镜像源配置成功!")
    return True


def get_conda_config_file():
    """获取conda配置文件路径"""
    return Path.home() / ".condarc"


def setup_conda_mirror(mirror_name="tsinghua", permanent=True):
    """配置conda镜像源"""
    if mirror_name not in MIRROR_SOURCES:
        print(f"错误: 未知的镜像源 '{mirror_name}'")
        return False

    mirror = MIRROR_SOURCES[mirror_name]
    conda_url = mirror["conda"]

    print(f"配置conda镜像源: {mirror['name']} ({conda_url})")

    config_content = f"""
channels:
  - defaults
show_channel_urls: true
default_channels:
  - {conda_url}/pkgs/main
  - {conda_url}/pkgs/r
  - {conda_url}/pkgs/msys2
custom_channels:
  conda-forge: {conda_url}/cloud/
  pytorch: {conda_url}/cloud/
"""

    if permanent:
        config_file = get_conda_config_file()
        backup_file = config_file.with_suffix(".condarc.bak")

        if config_file.exists():
            import shutil

            shutil.copy(config_file, backup_file)
            print(f"已备份原配置到: {backup_file}")

        config_file.write_text(config_content.strip(), encoding="utf-8")
        print(f"配置文件: {config_file}")

    print("conda镜像源配置成功!")
    return True


def setup_hf_mirror(mirror_name="hf-mirror", permanent=True):
    """配置HuggingFace镜像源"""
    if mirror_name not in HF_MIRRORS:
        print(f"错误: 未知的镜像源 '{mirror_name}'")
        return False

    mirror = HF_MIRRORS[mirror_name]
    env_var = mirror["env_var"]
    url = mirror["url"]

    print(f"配置HuggingFace镜像源: {mirror['name']} ({url})")

    if permanent:
        shell_config = None
        if platform.system() == "Windows":
            pass
        else:
            home = Path.home()
            for rc in [".zshrc", ".bashrc", ".bash_profile", ".profile"]:
                rc_path = home / rc
                if rc_path.exists():
                    shell_config = rc_path
                    break

        if shell_config:
            content = shell_config.read_text(encoding="utf-8")
            env_line = f'export {env_var}="{url}"'

            if env_var in content:
                import re

                new_content = re.sub(rf"export {env_var}=.*", env_line, content)
            else:
                new_content = content + f"\n# HuggingFace Mirror\n{env_line}\n"

            shell_config.write_text(new_content, encoding="utf-8")
            print(f"已添加环境变量到: {shell_config}")
            print(f"运行 'source {shell_config}' 使其生效")
        else:
            print(f'请手动添加环境变量: export {env_var}="{url}"')

    os.environ[env_var] = url
    print(f"当前会话已设置: {env_var}={url}")
    print("HuggingFace镜像源配置成功!")
    return True


def list_mirrors():
    """列出所有可用镜像源"""
    print("\n=== pip/conda 镜像源 ===")
    for name, info in MIRROR_SOURCES.items():
        current_pip = get_current_pip_mirror()
        is_current = current_pip and info["pip"] in current_pip
        marker = " (当前)" if is_current else ""
        print(f"  {name}: {info['name']}{marker}")
        print(f"         pip: {info['pip']}")
        print(f"         conda: {info['conda']}")

    print("\n=== HuggingFace 镜像源 ===")
    for name, info in HF_MIRRORS.items():
        current_val = os.environ.get(info["env_var"], "")
        is_current = current_val == info["url"]
        marker = " (当前)" if is_current else ""
        print(f"  {name}: {info['name']}{marker}")
        print(f'         设置: export {info["env_var"]}="{info["url"]}"')


def setup_all_mirrors(mirror_name="tsinghua", permanent=True):
    """配置所有镜像源"""
    print("=" * 60)
    print("配置所有镜像源")
    print("=" * 60)

    setup_pip_mirror(mirror_name, permanent)
    print()

    stdout, _, code = run_command("conda --version")
    if code == 0:
        setup_conda_mirror(mirror_name, permanent)
        print()

    setup_hf_mirror(permanent=permanent)

    print("\n" + "=" * 60)
    print("镜像源配置完成!")
    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="配置国内镜像源")
    parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "pip", "conda", "hf", "all"],
        help="操作: list(列出), pip, conda, hf, all",
    )
    parser.add_argument(
        "--mirror",
        "-m",
        default="tsinghua",
        choices=list(MIRROR_SOURCES.keys()),
        help="镜像源名称",
    )
    parser.add_argument(
        "--temporary", "-t", action="store_true", help="仅临时设置(不写入配置文件)"
    )
    args = parser.parse_args()

    permanent = not args.temporary

    if args.action == "list":
        list_mirrors()
    elif args.action == "pip":
        setup_pip_mirror(args.mirror, permanent)
    elif args.action == "conda":
        setup_conda_mirror(args.mirror, permanent)
    elif args.action == "hf":
        setup_hf_mirror(permanent=permanent)
    elif args.action == "all":
        setup_all_mirrors(args.mirror, permanent)


if __name__ == "__main__":
    main()
