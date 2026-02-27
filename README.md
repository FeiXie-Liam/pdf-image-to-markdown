# PDF教程文档转Markdown自动化工具

将PDF教程文档（图片格式）自动转换为结构化的Markdown文件，保持原有目录结构。

## 功能特性

- 自动扫描目录结构，识别所有PDF文件
- 使用Ollama多模态模型（qwen3-vl）直接理解图片内容
- 保持原有目录结构输出Markdown文件
- 支持断点续传，中断后可继续处理
- 并发处理，提升转换效率
- 自动生成索引文件和统计报告

## 环境要求

- Python 3.13+
- Ollama服务（需提前安装并拉取多模态模型）

## 快速开始

### 1. 安装依赖

```bash
cd codes
uv sync
```

### 2. 配置Ollama

```bash
# 拉取多模态模型（推荐，中文效果好）
ollama pull qwen3-vl:8b

# 或使用其他模型
ollama pull llava:13b

# 启动Ollama服务
ollama serve
```

### 3. 配置环境变量（可选）

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置（如使用远程Ollama服务）
# OLLAMA_HOST=http://192.168.1.100:11434
```

## 使用方法

### 扫描目录结构

```bash
uv run python main.py scan
```

输出示例：
```
哥飞教程
├── adsense
│   └── FireShot Capture 005 - xxx.pdf
├── 新手入门
│   └── FireShot Capture 051 - xxx.pdf
└── ...

统计: 10 个目录, 120 个PDF文件
```

### 转换单个PDF

```bash
uv run python main.py convert "新手入门/FireShot Capture 051 - xxx.pdf"
```

### 批量转换所有PDF

```bash
# 默认使用3个并发
uv run python main.py convert-all

# 指定并发数
uv run python main.py convert-all --workers 5

# 禁用断点续传（重新处理所有文件）
uv run python main.py convert-all --no-resume
```

### 生成索引文件

```bash
uv run python main.py index
```

### 检查Ollama服务状态

```bash
uv run python main.py check
```

### 查看统计信息

```bash
uv run python main.py stats
```

输出示例：
```
       项目统计
┏━━━━━━━━━━━━━┳━━━━┓
┃ 项目        ┃ 数量 ┃
┡━━━━━━━━━━━━━╇━━━━┩
│ 分类目录    │   10 │
│ PDF文件总数 │  120 │
│ 已处理      │   85 │
│ 待处理      │   35 │
│ 完成进度    │ 70.8% │
└─────────────┴──────┘
```

## 配置说明

环境变量配置（`.env` 文件）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OLLAMA_HOST` | Ollama服务地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | 多模态模型名称 | `qwen3-vl:8b` |
| `SOURCE_DIR` | PDF源目录 | `../` |
| `OUTPUT_DIR` | Markdown输出目录 | `./output` |
| `IMAGE_DPI` | PDF提取图片DPI | `150` |
| `MAX_WORKERS` | 并发处理数 | `3` |

## 输出格式

转换后的Markdown文件格式：

```markdown
# 文档标题

> **元信息**
> - 来源: FireShot Capture 051
> - 分类: 新手入门
> - 转换时间: 2026-02-27 10:30:00

---

[转换后的正文内容]

---

*本文档由自动化脚本生成*
```

## 目录结构

```
codes/
├── config/              # 配置模块
│   ├── __init__.py
│   └── settings.py
├── src/                 # 核心模块
│   ├── __init__.py
│   ├── scanner.py       # 目录扫描
│   ├── converter.py     # PDF转换
│   └── output.py        # 输出管理
├── docs/                # 文档
│   └── design.md
├── output/              # 输出目录
│   ├── adsense/         # 按原目录结构输出
│   ├── 新手入门/
│   ├── structure.json   # 目录结构
│   └── README.md        # 索引文件
├── main.py              # CLI入口
├── pyproject.toml
└── .env.example
```

## 常见问题

### Q: Ollama连接失败？

确保Ollama服务正在运行：
```bash
ollama serve
```

如果使用远程服务，检查 `OLLAMA_HOST` 配置是否正确。

### Q: 模型未找到？

先拉取模型：
```bash
ollama pull qwen3-vl:8b
```

### Q: 转换速度慢？

- 增加并发数：`uv run python main.py convert-all --workers 5`
- 使用GPU加速的Ollama服务
- 使用更快的模型（如较小参数量的模型）

### Q: 如何跳过已处理的文件？

默认启用断点续传，直接运行：
```bash
uv run python main.py convert-all
```

## 依赖 

- [pymupdf](https://pymupdf.readthedocs.io/) - PDF处理
- [ollama](https://github.com/ollama/ollama-python) - Ollama Python SDK
- [rich](https://github.com/Textualize/rich) - 终端美化
- [typer](https://typer.tiangolo.com/) - CLI框架

## License

MIT
