# !/bin/bash

rm -rf build
rm -rf dg_itest.egg-info
rm -rf dist
#
#python setup.py sdist
#python setup.py bdist_wheel
#twine upload dist/*

# 1. 确保工作目录干净
git status

# 2. 创建并推送标签
#git tag v0.0.30
#git push github --tags

# 安装最新工具
pip install --upgrade build twine

# 检查生成的版本号
python -c "import setuptools_scm; print(setuptools_scm.get_version(local_scheme='no-local-version'))"

# 构建包
python -m build

# 检查包元数据
twine check dist/*

# 上传到PyPI
twine upload dist/*