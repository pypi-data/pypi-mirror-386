from setuptools import setup, find_packages
import os

# 读取 README
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A comprehensive cryptography utility library"

setup(
    name="koxs-terminal-tools",
    version="0.2.4",
    author="koxs",
    author_email="2931209205@qq.com",
    description="Cryptography utility tools for terminal applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pycryptodome>=3.10.1",
        "cryptography>=3.4.8",
    ],
    python_requires=">=3.7",
    # 移除 license 分类器避免警告
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8", 
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)