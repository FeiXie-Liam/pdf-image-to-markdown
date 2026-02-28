"""目录扫描模块"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.tree import Tree

from pdf2md.settings import settings

console = Console()


class Scanner:
    """目录扫描器"""

    def __init__(self, source_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.source_dir = Path(source_dir or settings.SOURCE_DIR).resolve()
        self.output_dir = Path(output_dir or settings.OUTPUT_DIR).resolve()
        self.exclude_dirs = settings.EXCLUDE_DIRS

    def scan_directory(self) -> dict:
        """
        递归扫描目录，获取所有PDF文件

        Returns:
            目录树结构字典
        """
        structure = {"name": self.source_dir.name, "type": "directory", "children": []}

        def scan_recursive(path: Path, tree_node: dict):
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return

            for item in items:
                # 跳过排除目录
                if item.name in self.exclude_dirs:
                    continue

                if item.is_dir():
                    child_node = {"name": item.name, "type": "directory", "children": []}
                    tree_node["children"].append(child_node)
                    scan_recursive(item, child_node)
                elif item.suffix.lower() == ".pdf":
                    tree_node["children"].append(
                        {"name": item.name, "type": "file", "path": str(item.relative_to(self.source_dir))}
                    )

        scan_recursive(self.source_dir, structure)
        return structure

    def get_pdf_list(self) -> list[Path]:
        """
        获取所有PDF文件列表

        Returns:
            PDF文件路径列表
        """
        pdf_files = []

        for item in self.source_dir.rglob("*.pdf"):
            # 检查是否在排除目录中
            relative_path = item.relative_to(self.source_dir)
            if any(part in self.exclude_dirs for part in relative_path.parts):
                continue
            pdf_files.append(item)

        return sorted(pdf_files)

    def save_structure(self, output_file: str = "structure.json") -> Path:
        """
        将目录结构保存为JSON文件

        Args:
            output_file: 输出文件名

        Returns:
            保存的文件路径
        """
        structure = self.scan_directory()
        output_path = self.output_dir / output_file

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        console.print(f"[green]目录结构已保存到: {output_path}[/green]")
        return output_path

    def print_tree(self, structure: Optional[dict] = None):
        """
        打印目录树结构

        Args:
            structure: 目录结构字典，如为None则扫描
        """
        if structure is None:
            structure = self.scan_directory()

        tree = Tree(f"[bold blue]{structure['name']}[/bold blue]")

        def add_nodes(tree_node, children):
            for child in children:
                if child["type"] == "directory":
                    branch = tree_node.add(f"[bold yellow]{child['name']}[/bold yellow]")
                    if "children" in child:
                        add_nodes(branch, child["children"])
                else:
                    tree_node.add(f"[green]{child['name']}[/green]")

        add_nodes(tree, structure.get("children", []))
        console.print(tree)

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            包含目录数和PDF文件数的字典
        """
        structure = self.scan_directory()

        def count_items(node: dict) -> tuple[int, int]:
            dirs = 0
            files = 0

            for child in node.get("children", []):
                if child["type"] == "directory":
                    dirs += 1
                    sub_dirs, sub_files = count_items(child)
                    dirs += sub_dirs
                    files += sub_files
                else:
                    files += 1

            return dirs, files

        dirs, files = count_items(structure)
        return {"directories": dirs, "pdf_files": files}
