"""输出管理模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from pdf2md.settings import settings

console = Console()


class OutputManager:
    """输出管理器"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or settings.OUTPUT_DIR).resolve()
        self.source_dir = Path(settings.SOURCE_DIR).resolve()
        self.process_log: dict[str, dict] = {}

    def create_output_structure(self, relative_path: Path) -> Path:
        """
        创建与源目录相同的输出结构

        Args:
            relative_path: 源文件的相对路径

        Returns:
            输出文件路径
        """
        # 保持相对目录结构，改变扩展名
        output_path = self.output_dir / relative_path.with_suffix(".md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def write_markdown(self, content: str, output_path: Path) -> bool:
        """
        写入Markdown文件

        Args:
            content: Markdown内容
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            console.print(f"[red]写入文件失败 {output_path}: {e}[/red]")
            return False

    def generate_index(self, pdf_files: list[Path]) -> Path:
        """
        生成总索引文件

        Args:
            pdf_files: PDF文件列表

        Returns:
            索引文件路径
        """
        index_path = self.output_dir / "README.md"

        # 按目录分组
        categories: dict[str, list[Path]] = {}
        for pdf in pdf_files:
            relative = pdf.relative_to(self.source_dir)
            if len(relative.parts) > 1:
                category = relative.parts[0]
            else:
                category = "根目录"
            if category not in categories:
                categories[category] = []
            categories[category].append(pdf)

        # 生成索引内容
        lines = [
            "# PDF教程文档索引",
            "",
            f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 目录",
            "",
        ]

        # 添加分类
        for category in sorted(categories.keys()):
            files = sorted(categories[category])
            lines.append(f"### {category} ({len(files)}个文件)")
            lines.append("")

            for pdf in files:
                relative = pdf.relative_to(self.source_dir)
                md_path = relative.with_suffix(".md")
                title = pdf.stem
                if title.startswith("FireShot Capture "):
                    parts = title.split(" - ", 1)
                    if len(parts) > 1:
                        title = parts[1]
                lines.append(f"- [{title}]({md_path})")

            lines.append("")

        # 添加统计信息
        lines.extend(
            [
                "---",
                "",
                "## 统计信息",
                "",
                f"- 总分类数: {len(categories)}",
                f"- 总文档数: {len(pdf_files)}",
            ]
        )

        # 写入文件
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        console.print(f"[green]索引文件已生成: {index_path}[/green]")
        return index_path

    def log_process(
        self,
        pdf_path: Path,
        success: bool,
        error: Optional[str] = None,
    ):
        """
        记录处理状态

        Args:
            pdf_path: PDF文件路径
            success: 是否成功
            error: 错误信息
        """
        key = str(pdf_path.relative_to(self.source_dir))
        self.process_log[key] = {
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

    def save_process_log(self) -> Path:
        """
        保存处理日志

        Returns:
            日志文件路径
        """
        log_path = self.output_dir / "process_log.json"

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.process_log, f, ensure_ascii=False, indent=2)

        return log_path

    def print_report(self):
        """打印处理报告"""
        success_count = sum(1 for v in self.process_log.values() if v["success"])
        fail_count = len(self.process_log) - success_count

        table = Table(title="处理报告")
        table.add_column("状态", style="cyan")
        table.add_column("数量", justify="right")

        table.add_row("成功", str(success_count), style="green")
        table.add_row("失败", str(fail_count), style="red")
        table.add_row("总计", str(len(self.process_log)), style="bold")

        console.print(table)

        # 显示失败的文件
        if fail_count > 0:
            console.print("\n[red]失败的文件:[/red]")
            for path, info in self.process_log.items():
                if not info["success"]:
                    console.print(f"  - {path}: {info.get('error', '未知错误')}")

    def get_processed_files(self) -> set[str]:
        """
        获取已处理的文件列表

        Returns:
            已处理文件路径集合
        """
        log_path = self.output_dir / "process_log.json"
        if not log_path.exists():
            return set()

        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)

        return {path for path, info in log.items() if info["success"]}
