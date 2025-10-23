from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lmp-sdk",
    version="1.1.0",
    author="LMP SDK Team",
    description="推理服务 Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lixiang/lmp-sdk-python",
    packages=find_packages(),
    package_dir={"": "."},  # 包在当前目录
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",  # 添加 3.11 和 3.12 支持
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        # 移除 dataclasses，Python 3.7+ 已内置
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ]
    }
)