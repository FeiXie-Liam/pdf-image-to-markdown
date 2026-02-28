"""命令行入口"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table

from pdf2md import __version__
from pdf2md.converter import Converter
from pdf2md.output import OutputManager
from pdf2md.scanner import Scanner
from pdf2md.settings import settings

app = typer.Typer(help="PDF文档转Markdown自动化工具")
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"pdf2md version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", callback=version_callback, help="显示版本号"
    ),
):
    """PDF文档转Markdown自动化工具"""
    pass


@app.command()
def scan():
    """扫描目录结构并保存"""
    scanner = Scanner()

    console.print("[bold blue]扫描目录结构...[/bold blue]")
    structure = scanner.scan_directory()

    # 打印目录树
    scanner.print_tree(structure)

    # 保存结构
    scanner.save_structure()

    # 显示统计
    stats = scanner.get_stats()
    console.print(f"\n[green]统计: {stats['directories']} 个目录, {stats['pdf_files']} 个PDF文件[/green]")


@app.command()
def convert(
    pdf_path: str = typer.Argument(..., help="PDF文件相对路径"),
    output: str = typer.Option(None, "-o", "--output", help="输出文件路径"),
    debug: bool = typer.Option(False, "-d", "--debug", help="Debug模式：实时流式输出模型响应"),
):
    """转换单个PDF文件"""
    scanner = Scanner()
    converter = Converter()
    output_manager = OutputManager()

    # 检查Ollama连接
    if not converter.check_connection():
        console.print("[red]请确保Ollama服务正在运行[/red]")
        raise typer.Exit(1)

    # 解析PDF路径
    source_path = scanner.source_dir / pdf_path
    if not source_path.exists():
        console.print(f"[red]文件不存在: {source_path}[/red]")
        raise typer.Exit(1)

    # 获取分类
    relative = source_path.relative_to(scanner.source_dir)
    category = relative.parts[0] if len(relative.parts) > 1 else ""

    # 转换
    markdown = converter.convert_pdf(source_path, category, debug=debug)

    if not markdown:
        console.print("[red]转换失败[/red]")
        raise typer.Exit(1)

    # 确定输出路径
    if output:
        output_path = Path(output)
    else:
        output_path = output_manager.create_output_structure(relative)

    # 写入文件
    if output_manager.write_markdown(markdown, output_path):
        console.print(f"[green]转换成功: {output_path}[/green]")
    else:
        raise typer.Exit(1)


@app.command()
def convert_all(
    workers: int = typer.Option(settings.MAX_WORKERS, "-w", "--workers", help="并发数"),
    resume: bool = typer.Option(True, "--resume/--no-resume", help="是否断点续传"),
    debug: bool = typer.Option(False, "-d", "--debug", help="Debug模式：实时流式输出模型响应（自动使用单线程）"),
):
    """批量转换所有PDF文件"""
    scanner = Scanner()
    converter = Converter()
    output_manager = OutputManager()

    # debug模式强制使用单线程，避免输出混乱
    if debug:
        workers = 1
        console.print("[yellow]Debug模式：使用单线程处理[/yellow]")

    # 检查Ollama连接
    if not converter.check_connection():
        console.print("[red]请确保Ollama服务正在运行[/red]")
        raise typer.Exit(1)

    # 获取PDF列表
    pdf_files = scanner.get_pdf_list()
    console.print(f"[blue]发现 {len(pdf_files)} 个PDF文件[/blue]")

    if not pdf_files:
        console.print("[yellow]没有找到PDF文件[/yellow]")
        return

    # 断点续传
    if resume:
        processed = output_manager.get_processed_files()
        pdf_files = [f for f in pdf_files if str(f.relative_to(scanner.source_dir)) not in processed]
        console.print(f"[blue]待处理 {len(pdf_files)} 个文件（已跳过 {len(processed)} 个已处理文件）[/blue]")

    if not pdf_files:
        console.print("[green]所有文件已处理完成[/green]")
        return

    # 并发处理
    def process_pdf(pdf_path: Path) -> tuple[Path, bool, str | None]:
        try:
            relative = pdf_path.relative_to(scanner.source_dir)
            category = relative.parts[0] if len(relative.parts) > 1 else ""

            markdown = converter.convert_pdf(pdf_path, category, show_progress=not debug, debug=debug)
            if not markdown:
                return pdf_path, False, "转换结果为空"

            output_path = output_manager.create_output_structure(relative)
            success = output_manager.write_markdown(markdown, output_path)

            return pdf_path, success, None if success else "写入文件失败"
        except Exception as e:
            return pdf_path, False, str(e)

    console.print(f"[blue]使用 {workers} 个并发处理...[/blue]")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("转换进度", total=len(pdf_files))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_pdf, pdf): pdf for pdf in pdf_files}

            for future in as_completed(futures):
                pdf_path, success, error = future.result()
                relative = pdf_path.relative_to(scanner.source_dir)
                output_manager.log_process(pdf_path, success, error)

                if success:
                    console.print(f"[green]✓[/green] {relative}")
                else:
                    console.print(f"[red]✗[/red] {relative}: {error}")

                progress.update(task, advance=1)

    # 保存日志和打印报告
    output_manager.save_process_log()
    output_manager.print_report()


@app.command()
def index():
    """生成索引文件"""
    scanner = Scanner()
    output_manager = OutputManager()

    pdf_files = scanner.get_pdf_list()
    if not pdf_files:
        console.print("[yellow]没有找到PDF文件[/yellow]")
        return

    output_manager.generate_index(pdf_files)


@app.command()
def check():
    """检查Ollama服务状态"""
    converter = Converter()
    converter.check_connection()


@app.command()
def stats():
    """显示统计信息"""
    scanner = Scanner()
    output_manager = OutputManager()

    # 扫描统计
    scan_stats = scanner.get_stats()

    # 处理统计
    processed = output_manager.get_processed_files()
    total_pdfs = scan_stats["pdf_files"]
    processed_count = len(processed)

    table = Table(title="项目统计")
    table.add_column("项目", style="cyan")
    table.add_column("数量", justify="right")

    table.add_row("分类目录", str(scan_stats["directories"]))
    table.add_row("PDF文件总数", str(total_pdfs))
    table.add_row("已处理", str(processed_count))
    table.add_row("待处理", str(total_pdfs - processed_count))

    if total_pdfs > 0:
        progress_pct = processed_count / total_pdfs * 100
        table.add_row("完成进度", f"{progress_pct:.1f}%")

    console.print(table)


if __name__ == "__main__":
    app()
