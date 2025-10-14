# 修改日志

## 2024-12-19

### 修复pyproject.toml配置问题
- **问题**: 使用 `pip install -e .` 时报错，提示发现多个顶级包
- **原因**: pyproject.toml缺少包发现和构建系统配置
- **解决方案**: 
  - 添加了 `[build-system]` 配置
  - 添加了 `[tool.setuptools.packages.find]` 配置，指定只包含 `app*` 包
  - 添加了 `[tool.setuptools.package-data]` 配置，包含静态文件和模板文件
- **修改文件**: `pyproject.toml`

### 创建requirements.txt文件
- **目的**: 为不熟悉pyproject.toml的用户提供传统的依赖安装方式
- **内容**: 包含所有项目依赖及其版本要求
- **修改文件**: `requirements.txt`
