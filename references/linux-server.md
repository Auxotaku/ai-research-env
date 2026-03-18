# Linux服务器环境配置

## 目录
1. [服务器基础配置](#服务器基础配置)
2. [权限与用户管理](#权限与用户管理)
3. [环境变量配置](#环境变量配置)
4. [存储与缓存管理](#存储与缓存管理)
5. [多用户环境](#多用户环境)
6. [常见问题](#常见问题)

---

## 服务器基础配置

### 检查系统信息
```bash
# 系统版本
cat /etc/os-release
lsb_release -a

# 内核版本
uname -a

# GPU信息
nvidia-smi
lspci | grep -i nvidia

# CUDA版本
nvcc --version
ls /usr/local/ | grep cuda

# 磁盘空间
df -h
```

### 检查Python环境
```bash
# 系统Python
which python
python --version

# 已安装的conda
which conda
conda --version
conda env list

# 已安装的Python版本
ls /usr/bin/python*
```

---

## 权限与用户管理

### conda安装位置
```bash
# 用户级安装 (推荐)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -p $HOME/miniconda3

# 或使用Mambaforge (更轻量)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh
bash Mambaforge-Linux-x86_64.sh -p $HOME/mambaforge
```

### 权限问题排查
```bash
# pip安装权限问题
pip install package --user  # 用户级安装
# 或使用虚拟环境

# conda权限问题
# 确保conda安装在用户目录下
conda config --append envs_dirs $HOME/.conda/envs
conda config --append pkgs_dirs $HOME/.conda/pkgs
```

---

## 环境变量配置

### Shell配置文件
```bash
# Bash
~/.bashrc
~/.bash_profile

# Zsh
~/.zshrc

# 使配置生效
source ~/.bashrc
```

### 常用环境变量
```bash
# CUDA路径
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# HuggingFace镜像
export HF_ENDPOINT=https://hf-mirror.com

# HuggingFace缓存位置
export HF_HOME=/data/cache/huggingface
export TRANSFORMERS_CACHE=/data/cache/transformers
export HF_DATASETS_CACHE=/data/cache/datasets

# pip镜像
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 多CUDA版本切换
alias cuda11='export PATH=/usr/local/cuda-11.8/bin:$PATH LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH'
alias cuda12='export PATH=/usr/local/cuda-12.1/bin:$PATH LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH'
```

### 自动切换环境
```bash
# 在 ~/.bashrc 中添加
# 根据目录自动激活conda环境
function cd() {
    builtin cd "$@"
    if [[ -f environment.yml ]]; then
        env_name=$(head -n 1 environment.yml | cut -d':' -f2 | tr -d ' ')
        conda activate $env_name 2>/dev/null
    elif [[ -f requirements.txt ]]; then
        venv_name=$(basename $(pwd))
        source ~/.venvs/$venv_name/bin/activate 2>/dev/null
    fi
}
```

---

## 存储与缓存管理

### 模型缓存位置
```bash
# 默认位置
~/.cache/huggingface/
~/.cache/torch/

# 修改缓存位置
export HF_HOME=/data/cache/huggingface
export TORCH_HOME=/data/cache/torch
```

### 查看缓存大小
```bash
du -sh ~/.cache/huggingface/
du -sh ~/.cache/torch/

# 查看conda环境大小
conda env list | awk '{print $2}' | xargs -I {} du -sh {}
```

### 清理缓存 (谨慎操作)
```bash
# pip缓存
pip cache purge

# conda缓存
conda clean --all

# HuggingFace缓存
# 注意：此操作会删除已下载的模型
rm -rf ~/.cache/huggingface/hub/models--*
```

### 共享模型目录
```bash
# 创建共享目录
sudo mkdir -p /data/models
sudo chmod 777 /data/models

# 设置环境变量
export HF_HOME=/data/models/huggingface
```

---

## 多用户环境

### 共享conda环境
```bash
# 在共享位置创建环境
conda create --prefix /shared/envs/myenv python=3.10

# 激活共享环境
conda activate /shared/envs/myenv
```

### 环境隔离
```bash
# 每个项目独立环境
project_name="my-project"
conda create -n $project_name python=3.10
conda activate $project_name

# 或使用项目目录内的环境
python -m venv .venv
source .venv/bin/activate
```

### 多用户权限
```bash
# 创建用户组
sudo groupadd ml-users
sudo usermod -aG ml-users $USER

# 设置共享目录权限
sudo chgrp -R ml-users /data/models
sudo chmod -R g+rw /data/models
```

---

## 常见问题

### 1. conda安装慢
```bash
# 使用mamba (更快的依赖解析)
conda install mamba -n base -c conda-forge
mamba install package

# 或直接使用Mambaforge
```

### 2. 磁盘空间不足
```bash
# 查找大文件
find ~ -type f -size +1G 2>/dev/null

# 清理conda
conda clean --all

# 清理pip
pip cache purge

# 删除不用的环境
conda env remove -n old_env
```

### 3. GPU不可用
```bash
# 检查驱动
nvidia-smi

# 检查CUDA
nvcc --version
echo $CUDA_HOME
echo $LD_LIBRARY_PATH

# 检查PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# 如果返回False，重新安装正确的PyTorch版本
```

### 4. 内存不足
```bash
# 查看内存使用
free -h
htop

# 设置交换空间
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 添加到fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 5. 权限被拒绝
```bash
# 检查文件权限
ls -la file_or_directory

# 修改权限 (谨慎)
chmod +x script.sh
chmod -R u+rw directory/

# 检查所属
chown -R user:group directory/
```

### 6. 网络问题
```bash
# 检查网络
ping pypi.org
ping huggingface.co

# 使用代理
export HTTP_PROXY=http://proxy-server:port
export HTTPS_PROXY=http://proxy-server:port

# 测试代理
curl -x http://proxy-server:port https://pypi.org
```

### 7. 进程管理
```bash
# 查看GPU进程
nvidia-smi
fuser -v /dev/nvidia*

# 杀死占用GPU的进程
kill -9 PID

# 后台运行
nohup python train.py > output.log 2>&1 &

# 查看后台进程
jobs -l
ps aux | grep python

# 使用tmux
tmux new -s training
python train.py
# Ctrl+B, D 分离
tmux attach -t training
```

---

## 快速检查脚本

保存为 `check_server.sh`:
```bash
#!/bin/bash
echo "=== 系统信息 ==="
uname -a
cat /etc/os-release | head -n 2

echo -e "\n=== GPU信息 ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

echo -e "\n=== CUDA信息 ==="
nvcc --version 2>/dev/null || echo "nvcc未安装"
ls /usr/local/cuda* 2>/dev/null || echo "未找到CUDA安装"

echo -e "\n=== Python信息 ==="
which python
python --version

echo -e "\n=== Conda信息 ==="
which conda 2>/dev/null && conda --version || echo "conda未安装"

echo -e "\n=== 磁盘空间 ==="
df -h / $HOME

echo -e "\n=== 内存信息 ==="
free -h
```