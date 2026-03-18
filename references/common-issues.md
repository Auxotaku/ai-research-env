# 常见问题与解决方案

## 目录
1. [网络问题](#网络问题)
2. [CUDA/GPU问题](#cudagpu问题)
3. [依赖冲突](#依赖冲突)
4. [安装失败](#安装失败)
5. [运行时错误](#运行时错误)

---

## 网络问题

### pip安装超时
**错误信息**: `pip._vendor.urllib3.exceptions.ReadTimeoutError`

**解决方案**:
```bash
# 增加超时时间
pip install package --timeout 100

# 使用国内镜像
pip install package -i https://pypi.tuna.tsinghua.edu.cn/simple

# 使用代理
pip install package --proxy http://127.0.0.1:7890
```

### HuggingFace下载慢/失败
**错误信息**: `ConnectionError`, `ReadTimeout`

**解决方案**:
```bash
# 设置镜像
export HF_ENDPOINT=https://hf-mirror.com

# 使用断点续传
from huggingface_hub import snapshot_download
snapshot_download('model_id', resume_download=True)

# 使用ModelScope替代
pip install modelscope
from modelscope import snapshot_download
snapshot_download('model_id')
```

### GitHub克隆慢
**解决方案**:
```bash
# 使用镜像站
git clone https://gitclone.com/github.com/user/repo.git
git clone https://mirror.ghproxy.com/https://github.com/user/repo.git

# 浅克隆
git clone --depth 1 https://github.com/user/repo.git

# 只克隆特定分支
git clone -b branch_name --single-branch https://github.com/user/repo.git
```

---

## CUDA/GPU问题

### CUDA版本不匹配
**错误信息**: 
- `RuntimeError: CUDA error: no kernel image is available for execution on the device`
- `RuntimeError: The NVIDIA driver on your system is too old`

**解决方案**:
```bash
# 检查CUDA版本
nvcc --version
nvidia-smi  # 查看驱动支持的最高CUDA版本

# 重新安装匹配的PyTorch
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### torch.cuda.is_available()返回False
**排查步骤**:
```python
import torch
print(torch.__version__)  # 检查版本
print(torch.version.cuda)  # 检查PyTorch编译时的CUDA版本
print(torch.cuda.is_available())  # GPU是否可用

# 检查CUDA环境变量
import os
print(os.environ.get('CUDA_PATH'))
print(os.environ.get('CUDA_HOME'))
```

**解决方案**:
1. 确保安装了GPU版本的PyTorch (不是CPU版本)
2. 检查NVIDIA驱动是否正常
3. 确保CUDA版本与PyTorch匹配

### cuDNN错误
**错误信息**: `cudnn_status_not_initialized`

**解决方案**:
```bash
# 检查cuDNN
python -c "import torch; print(torch.backends.cudnn.version())"

# 禁用cuDNN
import torch
torch.backends.cudnn.enabled = False
```

### 显存不足 (OOM)
**错误信息**: `CUDA out of memory`

**解决方案**:
```python
# 1. 减小batch_size
batch_size = 1

# 2. 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

with autocast():
    output = model(input)
    loss = criterion(output, target)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()

# 3. 清理缓存
import torch
torch.cuda.empty_cache()

# 4. 使用gradient checkpointing
model.gradient_checkpointing_enable()

# 5. 使用8-bit量化
pip install bitsandbytes
model = AutoModelForCausalLM.from_pretrained(
    "model_id",
    load_in_8bit=True,
    device_map="auto"
)
```

---

## 依赖冲突

### 版本冲突
**错误信息**: `ERROR: pip's dependency resolver does not currently take into account all the packages`

**解决方案**:
```bash
# 1. 使用虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 2. 查看依赖树
pip install pipdeptree
pipdeptree

# 3. 强制重装
pip install package --force-reinstall

# 4. 使用uv解决依赖
pip install uv
uv pip install -r requirements.txt
```

### MMCV系列冲突
**问题**: mmcv、mmdet、mmaction等版本互相依赖

**解决方案**:
```bash
# 使用MIM安装 (推荐)
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
mim install mmdet
mim install mmaction2

# 或使用官方推荐版本组合
# 参考: https://mmdetection.readthedocs.io/en/latest/get_started.html
pip install mmengine mmcv mmdet
```

### transformers与PEFT冲突
**解决方案**:
```bash
# 使用兼容版本
pip install transformers==4.36.0 peft==0.7.0

# 查看兼容性
# PEFT文档: https://huggingface.co/docs/peft/index
```

---

## 安装失败

### 编译错误
**错误信息**: `error: Microsoft Visual C++ 14.0 is required`

**解决方案**:
```bash
# Windows: 安装 Visual Studio Build Tools
# 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用conda安装预编译版本
conda install package -c conda-forge
```

### 权限错误
**错误信息**: `PermissionError: [Errno 13] Permission denied`

**解决方案**:
```bash
# 使用用户安装
pip install package --user

# 或使用虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install package
```

### setup.py安装失败
**解决方案**:
```bash
# 尝试pip install
pip install -e .

# 或使用legacy安装
pip install -e . --no-build-isolation

# 检查setup.py依赖
python setup.py --help-commands
```

---

## 运行时错误

### ImportError
**常见原因与解决方案**:

```python
# 1. 模块未安装
pip install module_name

# 2. 环境变量问题
import sys
sys.path.append('/path/to/module')

# 3. conda环境未激活
conda activate env_name

# 4. CUDA相关导入错误
# 确保安装了GPU版本
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### DLL加载失败 (Windows)
**错误信息**: `DLL load failed: 找不到指定的模块`

**解决方案**:
```bash
# 添加CUDA到PATH
set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;%PATH%

# 或重新安装PyTorch
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### numpy版本问题
**错误信息**: `AttributeError: module 'numpy' has no attribute 'float'`

**解决方案**:
```bash
# numpy 1.24+ 移除了 np.float/np.int
pip install "numpy<1.24"

# 或修改代码
# np.float -> float 或 np.float64
# np.int -> int 或 np.int64
```

### SSL证书错误
**错误信息**: `SSLError`, `CERTIFICATE_VERIFY_FAILED`

**解决方案**:
```bash
# 信任主机
pip install package --trusted-host pypi.org --trusted-host files.pythonhosted.org

# 或更新证书
pip install --upgrade certifi

# conda
conda config --set ssl_verify false
```

---

## 快速诊断命令

```bash
# 环境诊断
python diagnose_env.py

# GPU检查
python check_gpu.py

# 仓库分析
python analyze_repo.py /path/to/repo
```