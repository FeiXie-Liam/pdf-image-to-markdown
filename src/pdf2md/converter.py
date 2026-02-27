"""PDF解析转换模块"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz  # pymupdf
import ollama
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from pdf2md.settings import settings

console = Console()


class Converter:
    """PDF转换器"""

    def __init__(
        self,
        ollama_host: Optional[str] = None,
        model: Optional[str] = None,
        dpi: Optional[int] = None,
    ):
        self.ollama_host = ollama_host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        self.dpi = dpi or settings.IMAGE_DPI

        # 配置Ollama客户端
        self.client = ollama.Client(host=self.ollama_host)

    def extract_pages(self, pdf_path: Path) -> list[bytes]:
        """
        提取PDF每页为图片

        Args:
            pdf_path: PDF文件路径

        Returns:
            图片字节列表
        """
        images = []

        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 将页面渲染为图片
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                # 转换为PNG字节
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)

        return images

    def analyze_page(
        self, image_bytes: bytes, page_num: int, debug: bool = False
    ) -> str:
        """
        使用Ollama多模态模型分析单页内容

        Args:
            image_bytes: 图片字节数据
            page_num: 页码
            debug: 是否开启debug模式（流式输出）

        Returns:
            Markdown格式的内容
        """
        image_base64 = base64.b64encode(image_bytes).decode()

        prompt = """请分析这张图片的内容，将其转换为Markdown格式。
要求：
1. 保持原文结构和层次
2. 标题使用对应的Markdown标题级别
3. 列表使用Markdown列表格式
4. 保留关键信息，忽略页面装饰元素（如导航栏、广告等）
5. 如果是代码块，使用对应的代码格式
6. 如果有表格，转换为Markdown表格
7. 不要添加任何解释性文字，只输出转换后的内容"""

        try:
            if debug:
                # 流式输出模式
                console.print(f"\n[bold cyan]━━━ 第{page_num}页 流式输出 ━━━[/bold cyan]")
                stream = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    images=[image_base64],
                    stream=True,
                )
                full_response = []
                for chunk in stream:
                    text = chunk.get("response", "")
                    if text:
                        print(text, end="", flush=True)
                        full_response.append(text)
                print()  # 换行
                console.print(f"[bold cyan]━━━ 第{page_num}页 完成 ━━━[/bold cyan]\n")
                return "".join(full_response)
            else:
                # 非流式模式
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    images=[image_base64],
                )
                return response["response"]
        except Exception as e:
            console.print(f"[red]分析第{page_num}页时出错: {e}[/red]")
            return f"\n[错误: 第{page_num}页解析失败]\n"

    def convert_pdf(
        self,
        pdf_path: Path,
        category: str = "",
        show_progress: bool = True,
        debug: bool = False,
    ) -> str:
        """
        转换PDF为Markdown

        Args:
            pdf_path: PDF文件路径
            category: 分类名称
            show_progress: 是否显示进度条
            debug: 是否开启debug模式（流式输出，实时显示进度）

        Returns:
            完整的Markdown内容
        """
        console.print(f"[blue]正在处理: {pdf_path.name}[/blue]")

        if debug:
            console.print("[yellow]Debug模式已启用，将实时输出模型响应[/yellow]")
            show_progress = False  # debug模式下不显示进度条

        # 提取所有页面
        pages = self.extract_pages(pdf_path)

        if not pages:
            console.print(f"[yellow]警告: {pdf_path.name} 没有页面[/yellow]")
            return ""

        # 分析每一页
        page_contents = []

        if show_progress:
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            )
            with progress:
                task = progress.add_task("分析页面", total=len(pages))
                for i, page in enumerate(pages, 1):
                    content = self.analyze_page(page, i, debug=debug)
                    page_contents.append(content)
                    progress.update(task, advance=1)
        else:
            for i, page in enumerate(pages, 1):
                content = self.analyze_page(page, i, debug=debug)
                page_contents.append(content)

        # 生成Markdown
        markdown = self._generate_markdown(pdf_path, category, page_contents)

        return markdown

    def _generate_markdown(
        self,
        pdf_path: Path,
        category: str,
        page_contents: list[str],
    ) -> str:
        """
        生成完整的Markdown文档

        Args:
            pdf_path: PDF文件路径
            category: 分类名称
            page_contents: 每页内容列表

        Returns:
            完整的Markdown内容
        """
        # 从文件名提取标题
        title = pdf_path.stem
        if title.startswith("FireShot Capture "):
            # 尝试提取更有意义的标题
            parts = title.split(" - ", 1)
            if len(parts) > 1:
                title = parts[1]

        # 构建Markdown
        lines = [
            f"# {title}",
            "",
            "> **元信息**",
            f"> - 来源: {pdf_path.stem}",
            f"> - 分类: {category or '未分类'}",
            f"> - 转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # 添加所有页面内容
        for i, content in enumerate(page_contents, 1):
            if len(page_contents) > 1:
                lines.append(f"<!-- 第{i}页 -->")
            lines.append(content.strip())
            lines.append("")

        # 添加页脚
        lines.extend(
            [
                "---",
                "",
                "*本文档由自动化脚本生成*",
            ]
        )

        return "\n".join(lines)

    def check_connection(self) -> bool:
        """
        检查Ollama服务是否可用

        Returns:
            是否连接成功
        """
        try:
            models = self.client.list()
            console.print(f"[green]已连接到Ollama服务: {self.ollama_host}[/green]")

            # 检查模型是否存在
            model_names = [m["model"] for m in models.get("models", [])]
            if self.model in model_names:
                console.print(f"[green]模型 {self.model} 已就绪[/green]")
            else:
                console.print(f"[yellow]警告: 模型 {self.model} 未找到[/yellow]")
                console.print(f"[yellow]可用模型: {', '.join(model_names)}[/yellow]")
                console.print(f"[yellow]请运行: ollama pull {self.model}[/yellow]")

            return True
        except Exception as e:
            console.print(f"[red]无法连接到Ollama服务: {e}[/red]")
            return False
