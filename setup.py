# encoding=utf-8

import re
import io
import os

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

kwds = {}

# Read version from aservice/__init__.py
pat = re.compile(r'__version__\s*=\s*(\S+)', re.M)
wd = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(wd, 'ahserver', '__init__.py'), encoding='utf-8') as rf:
    data = rf.read()
    kwds["version"] = eval(pat.search(data).group(1))

if os.path.exists("README.rst"):
    with io.open('README.rst', encoding='utf-8') as rf:
        kwds["long_description"] = rf.read()

h2parser = Extension(
    name="ahserver.http2.h2parser",
    sources=[
        "src/ahparser/alphabet.c", "src/ahparser/strbuf.c",
        "src/ahparser/msgbuf.c", "src/ahparser/parser.c",
        "ahserver/http2/h2parser.pyx"
    ],
    include_dirs=["src"]
)

setup(
    name="ahserver",
    description="a simple http server.",
    author="Weihe Yin",
    author_email="weihe.yin@istarshine.com",
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Utilities',

        'Operating System :: OS Independent',

        'Programming Language :: Cython',
        'Programming Language :: Cython :: 3',
    ],

    packages=find_packages(),
    ext_modules=cythonize(h2parser),
    install_requires=['uvloop'],
    extras_require={},
    entry_points={},

    **kwds
)
