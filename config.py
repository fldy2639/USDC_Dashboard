#!/usr/bin/env python3
"""
配置模块 - 统一管理区块链学习项目的环境变量和API配置

所有API密钥和配置都应通过此模块读取，禁止在其他文件中直接访问 .env
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_etherscan_api_key():
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("错误：未配置 ETHERSCAN_API_KEY")
        print("请在 .env 文件中添加：ETHERSCAN_API_KEY=your_key_here")
        print("获取API密钥：https://etherscan.io/apis")
        sys.exit(1)
    return api_key


def get_alchemy_api_key():
    api_key = os.getenv("ALCHEMY_API_KEY")
    if not api_key:
        print("错误：未配置 ALCHEMY_API_KEY")
        print("请在 .env 文件中添加：ALCHEMY_API_KEY=your_key_here")
        print("获取API密钥：https://www.alchemy.com/")
        sys.exit(1)
    return api_key


def get_alchemy_rpc_url():
    api_key = get_alchemy_api_key()
    return f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
