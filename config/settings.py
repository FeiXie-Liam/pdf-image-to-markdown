"""配置管理模块"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 路径配置
    SOURCE_DIR: str = "../"  # 源目录（PDF所在）
    OUTPUT_DIR: str = "./output"  # 输出目录
    EXCLUDE_DIRS: list[str] = ["codes", ".git"]

    # Ollama配置
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3-vl:8b"

    # PDF处理配置
    IMAGE_DPI: int = 150  # 提取图片DPI

    # 并发配置
    MAX_WORKERS: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# 全局配置实例
settings = Settings()
