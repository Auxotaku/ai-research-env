---
name: ai-research-env
description: |
  AI科研项目环境部署助手，加速你的每次探索，让科研专注于研究本身，而非环境配置。
  
  解决PyTorch/深度学习项目的环境配置痛点：国内网络镜像源配置、GPU/CUDA检测与兼容性、依赖冲突解决、HuggingFace/ModelScope模型权重下载、GitHub仓库README自动分析、静态依赖扫描检测缺失包、环境配置报告生成。
  
  触发场景：
  (1) 克隆新仓库需要部署环境
  (2) pip/conda安装失败或超时
  (3) HuggingFace模型下载慢
  (4) CUDA版本不匹配导致GPU不可用
  (5) 依赖版本冲突诊断
  (6) 分析README提取安装命令
  (7) 检测代码中缺失的依赖
  (8) 需要环境配置报告
  
  支持项目类型：PyTorch训练/推理、LLM部署、视频生成（Wan/LTX等）、OpenMMLab系列(MMDetection/MMAction等)、YOLO系列、Diffusers等。
  
  工作模式：先自动诊断分析，遇到问题再介入协助。
  
  安全约束：不执行任何删除操作，删除需用户手动执行。
---

# AI科研项目环境部署

**安全约束**: 本skill不执行任何删除操作，涉及删除的命令会提示用户手动执行

## 核心工作流程

```
1. 诊断环境 → 2. 分析项目 → 3. 配置镜像 → 4. 智能安装 → 5. 下载模型 → 6. 生成报告
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

### 第三步：配置国内镜像源

```bash
python scripts/setup_mirrors.py all --mirror tsinghua
```

### 第四步：智能安装

```bash
# 模拟运行
python scripts/smart_install.py /path/to/project --dry-run

# 实际安装（完成后自动生成报告）
python scripts/smart_install.py /path/to/project
```

### 第五步：下载模型

```bash
# 智能下载（先在ModelScope搜索，让用户选择）
python scripts/download_model.py meta-llama/Llama-2-7b-hf

# 直接指定ModelScope模型ID
python scripts/download_model.py --modelscope-id Qwen/Qwen2-7B-Instruct
```

### 第六步：生成环境配置报告

```bash
# 安装完成后自动生成，或手动运行
python scripts/generate_report.py /path/to/project
```

---

## 生成的文件

| 文件 | 说明 |
|------|------|
| `.install_state.json` | 安装状态记录（断点续传） |
| `.install_commands.log` | 安装命令历史（精简版） |
| `.download_history.json` | 模型下载历史 |
| `environment_setup_report.md` | 最终环境配置报告 |

---

## 环境配置报告内容

1. **环境概览** - Python/CUDA版本、虚拟环境、项目类型
2. **安装结果** - 成功/失败的包列表
3. **下载的模型** - 模型ID、来源、本地路径、下载命令
4. **使用指南** - 来自README的运行示例
5. **历史命令** - 精简的安装命令记录

---

## 模型下载策略

```
1. 在ModelScope搜索模型名称
2. 显示搜索结果，让用户选择
3. 选择后从ModelScope下载
4. 失败则从HuggingFace下载（使用hf-mirror镜像）
5. 记录下载命令和位置
```

---

## 脚本索引

| 脚本 | 功能 |
|------|------|
| `diagnose_env.py` | 环境诊断 |
| `analyze_repo.py` | 仓库分析 |
| `scan_deps.py` | 静态依赖扫描 |
| `smart_install.py` | 智能安装、命令记录、报告生成 |
| `setup_mirrors.py` | 镜像配置 |
| `check_gpu.py` | GPU/CUDA检查 |
| `download_model.py` | 模型下载（ModelScope智能搜索） |
| `generate_report.py` | 环境配置报告生成 |

---

## 详细参考文档

| 文档 | 内容 |
|------|------|
| `references/linux-server.md` | Linux服务器特有问题 |
| `references/mirror-sources.md` | 镜像源配置 |
| `references/cuda-compatibility.md` | CUDA兼容性 |
| `references/prebuilt-wheels.md` | 预编译whl索引 |
| `references/common-issues.md` | 常见问题 |
| `references/project-patterns.md` | 项目部署模式 |