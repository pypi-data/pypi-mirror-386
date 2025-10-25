from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hjq",          # PyPI显示的名称
    version="0.0.1",            # 版本号
    author="huang jingqi",
    author_email="huangjingqi@163.com",
    description="A simple example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my_package",
    packages=find_packages(),   # 自动发现所有包
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",    # Python版本要求
    install_requires=[],        # 依赖库，如["requests>=2.25.1"]
)
