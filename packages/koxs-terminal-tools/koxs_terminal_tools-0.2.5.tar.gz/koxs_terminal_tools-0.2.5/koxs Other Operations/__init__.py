"""
crypto_utils - 多功能加密工具模块
支持多种加密算法：AES, RSA, DES, 3DES, ChaCha20, 以及哈希函数和数字签名

版本: 1.0.0
作者: koxs
"""

from .crypto_utils import CryptoUtils

# 定义公开的API
__all__ = [
    'CryptoUtils',
]

# 模块版本
__version__ = '1.0.0'
__author__ = 'koxs'
__email__ = '2931209205@qq.com'

# 导入时显示欢迎信息（可选）
print(f"加载 crypto_utils 版本 {__version__}")