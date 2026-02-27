"""PDF教程文档转Markdown自动化工具"""

__version__ = "0.1.0"

from pdf2md.converter import Converter
from pdf2md.output import OutputManager
from pdf2md.scanner import Scanner
from pdf2md.settings import Settings, settings

__all__ = ["Scanner", "Converter", "OutputManager", "Settings", "settings"]
