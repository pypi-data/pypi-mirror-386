# china-union-lotto

## 概述
一个双色球的MCP Server项目

## 参考
https://zhuanlan.zhihu.com/p/1914511215515923435

## 开发
```shell
uv init
uv venv
.venv/Scripts/activate

uv add fastmcp

python -m build

uv pip install build twine

# 新上传
python -m twine upload ./dist/*

# 更新



uvx china-union-lotto

# TODO


```
