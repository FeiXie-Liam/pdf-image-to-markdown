 使用 uv 打包发布

  1. 安装构建工具

  uv tool install build
  uv tool install twine

  uv tool install 会将工具安装到独立环境，全局可用。

  2. 构建
uv
  uv build

  uv 自带 uv build 命令，会生成 dist/ 目录下的 .tar.gz 和 .whl 文件。

  3. 上传到 PyPI

  uv tool install twine
  twine upload dist/*

  或者用 uv publish（需要 uv 0.27+）：
  uv publish

  完整流程

  # 构建
  uv build

  # 先测试安装
  uv run pip install dist/pdf_to_markdown-0.1.0-py3-none-any.whl --force-reinstall

  # 上传到 TestPyPI 测试
  uv publish --publish-url https://test.pypi.org/legacy/

  # 正式发布到 PyPI
  uv publish

  uv publish 会自动从环境变量或命令行参数读取 Token：
  # 设置 Token（推荐用环境变量）
  export UV_PUBLISH_TOKEN=pypi-xxxxxx
  uv publish