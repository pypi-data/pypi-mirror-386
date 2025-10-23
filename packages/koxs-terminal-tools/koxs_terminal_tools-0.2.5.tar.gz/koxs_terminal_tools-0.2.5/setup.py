from setuptools import setup, find_packages

setup(
    name="koxs-terminal-tools",
    version="0.2.5",  # 更新版本
    author="koxs", 
    author_email="2931209205@qq.com",
    description="Cryptography utility tools for terminal applications",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    
    # 关键修改：包含所有 .py 文件
    packages=find_packages(),  # 自动查找所有包
    include_package_data=True,
    
    install_requires=[
        "pycryptodome>=3.10.1",
        "cryptography>=3.4.8",
    ],
    python_requires=">=3.7",
)