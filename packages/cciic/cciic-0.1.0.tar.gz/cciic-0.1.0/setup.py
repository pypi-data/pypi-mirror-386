"""
cciic包安装配置
"""

from setuptools import setup, find_packages
import os

# 读取requirements文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cciic",
    version="0.1.0",
    description="cc1024程序员日快乐！！！",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Desktop Environment :: Window Managers",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    package_data={
        "cciic": [
            "assets/music/*.mp3",
            "assets/images/*.gif",
        ],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "cciic=cciic.__main__:main",
        ],
    },
    keywords="music, gif, animation, 哈基米, momo, 耄耋",
)
