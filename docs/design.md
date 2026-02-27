# PDF教程文档转Markdown自动化方案

## 1. 项目概述

### 1.1 目标
将当前目录下120个PDF教程文档（图片格式）自动转换为结构化的Markdown文件，保持原有目录结构。

### 1.2 现状分析
- **PDF数量**: 120个
- **目录结构**: 9个分类目录
  - adsense
  - 养网站防老
  - 哥飞小课堂
  - 挖掘需求
  - 新手入门
  - 案例分析
  - 经验
  - 进阶教程
  - 高手分享
- **PDF特点**: FireShot Capture网页截图，每页是一张图片

## 2. 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主控制流程                              │
│                    (main.py)                                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  目录扫描模块  │    │  PDF解析模块   │    │  输出管理模块  │
│ (scanner.py)  │───▶│ (converter.py)│───▶│ (output.py)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   保存目录树   │    │ 提取PDF页面   │    │  生成Markdown  │
│   获取PDF列表  │    │ 多模态LLM理解 │    │  保持目录结构  │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 3. 核心处理流程

```
PDF文件 → 按页提取图片 → Ollama多模态模型理解每页内容 → 合并生成Markdown
```

**关键点**:
- PDF每页本身就是一张图片，直接提取即可
- 使用Ollama多模态模型（qwen3-vl）直接理解图片内容
- 无需传统OCR，LLM直接输出结构化Markdown

## 4. 核心模块设计

### 4.1 目录扫描模块 (scanner.py)

```python
# 主要功能
- scan_directory(): 递归扫描目录，获取所有PDF文件
- save_structure(): 将目录结构保存为JSON
- get_pdf_list(): 返回待处理的PDF文件列表（排除codes目录）
```

### 4.2 PDF解析模块 (converter.py)

```python
# 主要功能
- extract_pages(): 使用pymupdf提取PDF每页为图片
- analyze_page(): 调用Ollama多模态模型分析图片内容
- convert_pdf(): 整合所有页面内容，生成完整Markdown
```

### 4.3 输出管理模块 (output.py)

```python
# 主要功能
- create_output_structure(): 创建与源目录相同的输出结构
- write_markdown(): 写入Markdown文件
- generate_index(): 生成总索引文件
```

## 5. 依赖清单

```toml
[project]
dependencies = [
    "pymupdf>=1.24.0",        # PDF处理，提取页面图片
    "pillow>=10.0.0",         # 图片处理
    "ollama>=0.4.0",          # Ollama Python SDK
    "pydantic>=2.0.0",        # 数据验证
    "pydantic-settings>=2.0.0", # 配置管理
    "rich>=13.0.0",           # 终端输出美化
    "typer>=0.9.0",           # CLI框架
]
```

## 6. Ollama配置

### 6.1 拉取多模态模型
```bash
# 推荐：中文效果好
ollama pull qwen3-vl:8b

# 或者
ollama pull llava:13b
```

### 6.2 启动Ollama服务
```bash
# 本地启动
ollama serve

# 或远程服务器启动（监听所有端口）
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## 7. 项目结构

```
codes/
├── docs/
│   └── design.md           # 本设计文档
├── src/
│   ├── __init__.py
│   ├── scanner.py          # 目录扫描
│   ├── converter.py        # PDF转换（核心）
│   └── output.py           # 输出管理
├── config/
│   └── settings.py         # 配置管理
├── output/                  # Markdown输出目录（保持原结构）
│   ├── adsense/
│   ├── 新手入门/
│   └── ...
├── main.py                  # 主入口
├── pyproject.toml
└── .env                     # 环境变量配置
```

## 8. 配置设计

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 路径配置
    SOURCE_DIR: str = "../"           # 源目录（PDF所在）
    OUTPUT_DIR: str = "./output"       # 输出目录
    EXCLUDE_DIRS: list = ["codes", ".git"]

    # Ollama配置
    OLLAMA_HOST: str = "http://localhost:11434"  # 远程地址如 http://192.168.1.100:11434
    OLLAMA_MODEL: str = "qwen3-vl:8b"  # 多模态模型

    # PDF处理配置
    IMAGE_DPI: int = 150              # 提取图片DPI

    # 并发配置
    MAX_WORKERS: int = 3

    class Config:
        env_file = ".env"
```

## 9. 使用流程

```bash
# 1. 安装依赖
cd codes
uv sync

# 2. 配置Ollama地址（如需远程）
echo "OLLAMA_HOST=http://192.168.1.100:11434" > .env

# 3. 确保Ollama已拉取多模态模型
ollama pull qwen3-vl:8b

# 4. 扫描目录结构
uv run python main.py scan

# 5. 转换单个PDF
uv run python main.py convert "新手入门/FireShot Capture 051 - xxx.pdf"

# 6. 批量转换全部
uv run python main.py convert-all

# 7. 生成索引
uv run python main.py index
```

## 10. Ollama Vision调用示例

```python
import ollama
import base64

def analyze_page(image_bytes: bytes) -> str:
    """使用Ollama多模态模型分析单页内容"""
    image_base64 = base64.b64encode(image_bytes).decode()

    response = ollama.generate(
        model="qwen3-vl:8b",
        prompt="""请分析这张图片的内容，将其转换为Markdown格式。
要求：
1. 保持原文结构和层次
2. 标题使用对应的Markdown标题级别
3. 列表使用Markdown列表格式
4. 保留关键信息，忽略页面装饰元素
5. 如果是代码块，使用对应的代码格式""",
        images=[image_base64],
    )

    return response['response']
```

## 11. Markdown输出格式

```markdown
# 出海工具网站，从需求挖掘到网站制作全流程

> **元信息**
> - 来源: FireShot Capture 051
> - 分类: 新手入门
> - 转换时间: 2026-02-27

## 正文内容

[LLM理解并转换后的内容]

---

*本文档由自动化脚本生成*
```

## 12. 错误处理与断点续传

- 记录已处理文件，支持断点续传
- 单文件失败不影响整体流程
- 生成处理报告（成功/失败列表）

## 13. 实施步骤

1. **Phase 1**: 项目骨架
   - 配置pyproject.toml依赖
   - 实现目录扫描

2. **Phase 2**: 核心转换
   - PDF页面提取为图片
   - Ollama多模态模型集成
   - Markdown生成

3. **Phase 3**: 批量处理
   - 并发处理
   - 进度显示
   - 断点续传

---

*文档版本: v1.2*
*更新时间: 2026-02-27*
