---
name: ai-research-env
description: |
  AI科研项目环境部署助手 (Linux服务器专用)
  
  解决PyTorch/深度学习项目的环境配置痛点：国内网络镜像源配置、GPU/CUDA检测与兼容性、依赖冲突解决、HuggingFace/ModelScope模型权重下载、GitHub仓库README自动分析、静态依赖扫描检测缺失包。
  
  触发场景：
  (1) 克隆新仓库需要部署环境
  (2) pip/conda安装失败或超时
  (3) HuggingFace模型下载慢
  (4) CUDA版本不匹配导致GPU不可用
  (5) 依赖版本冲突诊断
  (6) 分析README提取安装命令
  (7) 检测代码中缺失的依赖
  
  支持项目类型：PyTorch训练/推理、LLM部署、视频生成、OpenMMLab系列(MMDetection/MMAction等)、YOLO系列、Diffusers等。
  
  工作模式：先自动诊断分析，遇到问题再介入协助。
  
  安全约束：不执行任何删除操作，删除需用户手动执行。
---

# AI科研项目环境部署 (Linux服务器)

**目标平台**: Linux服务器 (Ubuntu/CentOS等)

**安全约束**: 本skill不执行任何删除操作，涉及删除的命令会提示用户手动执行

## 核心工作流程

```
1. 诊断环境 → 2. 分析项目 → 3. 配置镜像 → 4. 智能安装 → 5. 下载模型
```

### 第一步：诊断当前环境

```bash
python scripts/diagnose_env.py
```

输出：Python版本、虚拟环境状态、pip/conda镜像源、GPU信息、CUDA版本、PyTorch状态、已安装的AI框架。

### 第二步：分析项目依赖

```bash
# 完整分析（README + 依赖文件）
python scripts/analyze_repo.py /path/to/project

# 静态扫描代码中的import，检测缺失依赖
python scripts/scan_deps.py /path/to/project
```

检测：requirements.txt、setup.py、pyproject.toml、代码中隐式依赖、项目使用的框架类型。

### 第三步：配置国内镜像源

```bash
# 一键配置所有镜像
python scripts/setup_mirrors.py all --mirror tsinghua

# 或分别配置
python scripts/setup_mirrors.py pip --mirror tsinghua
python scripts/setup_mirrors.py hf
```

### 第四步：智能安装

```bash
# 模拟运行（查看安装计划）
python scripts/smart_install.py /path/to/project --dry-run

# 实际安装
python scripts/smart_install.py /path/to/project

# 生成bash安装脚本
python scripts/smart_install.py /path/to/project --generate-script
```

特性：PyTorch优先、智能排序、断点续传、重试机制(最多3次)、特殊包处理。

### 第五步：下载模型

```bash
# 智能下载（优先ModelScope，失败则HuggingFace）
python scripts/download_model.py model_id

# 指定下载位置
python scripts/download_model.py model_id -o /data/models/model_name

# 查看已缓存模型
python scripts/download_model.py --list-cache
```

---

## 安装顺序策略

按优先级自动排序：

1. **PyTorch核心** (torch, torchvision, torchaudio) - 必须最先安装
2. **基础依赖** (numpy, scipy, pillow, opencv)
3. **ML框架** (transformers, diffusers, accelerate, peft)
4. **OpenMMLab** (mmengine, mmcv, mmdet等) - 使用mim安装
5. **其他依赖**
6. **特殊包** (flash-attn, xformers, bitsandbytes) - 需要特殊处理

---

## 特殊包处理

| 包名 | 处理方式 |
|------|----------|
| flash-attn | 建议使用预编译whl，见 `references/prebuilt-wheels.md` |
| xformers | 版本需与PyTorch匹配 |
| bitsandbytes | 需要CUDA 11.8+ |
| mmcv | 使用mim安装或从官方索引下载预编译whl |

---

## 模型下载策略

```
1. 检查ModelScope是否有该模型
   ↓ 有
   从ModelScope下载
   ↓ 没有/失败
2. 从HuggingFace下载（使用hf-mirror镜像）
   ↓ 失败
3. 提示用户设置代理
```

---

## 错误处理

- **自动重试**: 失败后记录原因，最多重试3次
- **断点续传**: 状态保存在 `.install_state.json`
- **用户介入**: 3次失败后停止，报告问题由用户处理

---

## 脚本索引

| 脚本 | 功能 |
|------|------|
| `diagnose_env.py` | 环境诊断：Python、pip、conda、GPU、CUDA、PyTorch |
| `analyze_repo.py` | 仓库分析：README、依赖文件、框架检测 |
| `scan_deps.py` | 静态分析：扫描代码import，检测缺失依赖 |
| `smart_install.py` | 智能安装：自动排序、断点续传、重试机制 |
| `setup_mirrors.py` | 镜像配置：pip/conda/HuggingFace |
| `check_gpu.py` | GPU/CUDA检查，输出PyTorch安装命令 |
| `download_model.py` | 模型下载：ModelScope优先，位置建议 |

---

## 详细参考文档

| 文档 | 内容 |
|------|------|
| `references/linux-server.md` | Linux服务器特有问题、权限、环境变量、多用户 |
| `references/mirror-sources.md` | 国内镜像源详细配置 |
| `references/cuda-compatibility.md` | CUDA与PyTorch版本兼容表 |
| `references/prebuilt-wheels.md` | flash-attn、xformers等预编译whl索引 |
| `references/common-issues.md` | 常见问题解决方案 |
| `references/project-patterns.md` | 不同项目类型的部署模式 |