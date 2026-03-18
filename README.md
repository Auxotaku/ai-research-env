# AI Research Environment Deployment Skill

AI科研项目环境部署助手，加速你的每次探索，让科研专注于研究本身，而非环境配置。

## 为什么需要这个Skill？

**科研时间宝贵，不该浪费在配环境上。**

自动化的环境配置是全自动科研的关键一环。

克隆一个新仓库 → README过时 → 依赖冲突 → CUDA版本不匹配 → 模型下载失败 → 折腾半天还没开始跑实验

这个Skill帮你自动化解决这些问题，让你快速进入研究状态。

| 功能 | 说明 |
|------|------|
| 环境诊断 | 检测Python、CUDA、GPU、PyTorch状态 |
| 依赖分析 | 扫描代码import，检测缺失依赖 |
| 智能安装 | PyTorch优先，自动排序，断点续传 |
| 镜像配置 | 一键配置pip/conda/HuggingFace国内镜像 |
| 模型下载 | ModelScope优先，自动选择最优下载源 |
| GPU检查 | CUDA兼容性检测，输出正确安装命令 |

## 支持的项目类型

**大语言模型**
- LLaMA系列、Qwen、ChatGLM、Mistral、DeepSeek等
- vLLM、text-generation-inference等推理框架

**视频生成模型**
- Wan系列 (Wan2.1等)
- LTX Video
- CogVideo、Open-Sora等

**图像生成模型**
- Stable Diffusion系列
- FLUX、SDXL等

**传统视觉任务**
- OpenMMLab系列 (MMDetection, MMAction2, MMSegmentation等)
- YOLO系列

**其他PyTorch生态项目**

## 安装

### 方法一：克隆仓库

```bash
cd ~/.agents/skills
git clone https://github.com/Auxotaku/ai-research-env.git
```

### 方法二：下载Release

1. 从 [Releases](https://github.com/Auxotaku/ai-research-env/releases) 下载 `.skill` 文件
2. 解压到 `~/.agents/skills/ai-research-env/`

### 验证安装

重启 Opencode 后，skill 应出现在可用技能列表中。

## 使用方法

### 核心工作流程

```
1. 诊断环境 → 2. 分析项目 → 3. 配置镜像 → 4. 智能安装 → 5. 下载模型
```

### 脚本命令

```bash
# 1. 环境诊断
python scripts/diagnose_env.py

# 2. 分析项目依赖
python scripts/analyze_repo.py /path/to/project
python scripts/scan_deps.py /path/to/project  # 静态扫描缺失依赖

# 3. 配置镜像源
python scripts/setup_mirrors.py all --mirror tsinghua

# 4. 智能安装
python scripts/smart_install.py /path/to/project --dry-run  # 预览
python scripts/smart_install.py /path/to/project            # 执行

# 5. GPU/CUDA检查
python scripts/check_gpu.py

# 6. 下载模型
python scripts/download_model.py meta-llama/Llama-2-7b-hf
python scripts/download_model.py --modelscope Qwen/Qwen-7B-Chat
```

## 安装顺序策略

按优先级自动排序，确保依赖正确安装：

1. **PyTorch核心** - 必须最先安装，避免CUDA版本冲突
2. **基础依赖** - numpy, scipy, pillow, opencv等
3. **ML框架** - transformers, diffusers, accelerate等
4. **OpenMMLab** - 使用mim安装
5. **其他依赖**
6. **特殊包** - flash-attn, xformers, bitsandbytes（需要特殊处理）

## 模型下载策略

```
ModelScope → HuggingFace → hf-mirror镜像 → 提示设置代理
```

优先从ModelScope下载，失败后自动切换源。

## 安全说明

### 重要约束

| 约束 | 说明 |
|------|------|
| **不执行删除操作** | 所有删除命令仅提示，由用户手动执行 |
| **不修改系统配置** | 仅在用户目录操作 |
| **需要用户确认** | 大文件下载、关键操作前会提示确认 |

### 数据安全

- 所有脚本在本地运行，不上传任何数据
- 模型下载到用户指定的缓存目录
- 安装状态保存在项目目录的 `.install_state.json`

### 权限要求

- 需要读取项目目录
- 需要执行pip/conda命令
- 需要网络访问（下载包和模型）

## 风险说明

### 已知风险

| 风险 | 级别 | 说明 | 缓解措施 |
|------|------|------|----------|
| 依赖冲突 | 中 | 不同项目可能需要不同版本的包 | 使用独立虚拟环境 |
| CUDA不兼容 | 中 | PyTorch CUDA版本与系统CUDA不匹配 | 脚本自动检测并提示 |
| 磁盘空间 | 低 | 模型文件可能很大 | 下载前显示预估大小 |
| 网络问题 | 低 | 国内访问HuggingFace可能失败 | 自动使用镜像源 |

### 不适用场景

- 非Python项目
- 需要root权限的系统级安装

### 错误处理

- **自动重试**：失败后最多重试3次
- **断点续传**：安装进度保存在 `.install_state.json`
- **用户介入**：3次失败后停止，报告问题

## 目录结构

```
ai-research-env/
├── SKILL.md                    # Skill定义文件
├── scripts/                    # 可执行脚本
│   ├── diagnose_env.py         # 环境诊断
│   ├── analyze_repo.py         # 仓库分析
│   ├── scan_deps.py            # 静态依赖扫描
│   ├── smart_install.py        # 智能安装
│   ├── setup_mirrors.py        # 镜像配置
│   ├── check_gpu.py            # GPU/CUDA检查
│   └── download_model.py       # 模型下载
└── references/                 # 参考文档
    ├── linux-server.md         # Linux服务器配置
    ├── mirror-sources.md       # 镜像源配置
    ├── cuda-compatibility.md   # CUDA兼容性
    ├── prebuilt-wheels.md      # 预编译whl索引
    ├── common-issues.md        # 常见问题
    └── project-patterns.md     # 项目部署模式
```

## 依赖要求

脚本本身需要：
- Python 3.8+
- 标准库（无需额外安装）

可选依赖（按需安装）：
- `huggingface_hub` - 模型下载
- `modelscope` - ModelScope模型下载
- `tomli` - 解析pyproject.toml (Python < 3.11)
- `pyyaml` - 解析environment.yml

## 常见问题

### Q: 为什么PyTorch要最先安装？

A: PyTorch的CUDA版本必须与系统CUDA匹配。如果先安装其他依赖，可能会安装CPU版本或错误CUDA版本的PyTorch，导致GPU不可用。

### Q: flash-attn安装失败怎么办？

A: flash-attn需要编译或预编译whl。参考 `references/prebuilt-wheels.md` 下载对应版本的预编译包。

### Q: 模型下载太慢怎么办？

A: 脚本会自动使用镜像源。如果仍然慢，可以：
1. 检查ModelScope是否有该模型
2. 设置代理：`export HTTP_PROXY=http://your-proxy:port`

### Q: 如何清除安装状态重新安装？

A: 手动删除项目目录下的 `.install_state.json` 文件。

## 贡献

欢迎提交Issue和Pull Request。

## 许可证

MIT License

## 致谢

本skill的开发参考了以下资源：
- [PyTorch官方文档](https://pytorch.org/)
- [HuggingFace文档](https://huggingface.co/docs)
- [OpenMMLab文档](https://openmmlab.com/)
- 国内各镜像站（清华、阿里云、中科大等）