import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '1.0.5'
DESCRIPTION = '做的一些工具包'
LONG_DESCRIPTION = '该工具包包含以下模块：1.方便调试和可筛选输出信息的Debug模块2.可以快速更改字符串颜色的Color模块'

# Setting up
setup(
    name="yliuetools",
    version=VERSION,
    author="yLIue",
    author_email="2138347243@qq.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    keywords=['python'],
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ]
)