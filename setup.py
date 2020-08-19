# encoding=utf-8

import io
import os
import re

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

kwds = {}

# Read version from aservice/__init__.py
pat = re.compile(r"__version__\s*=\s*(\S+)", re.M)
wd = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(wd, "ahserver", "__init__.py"), encoding="utf-8") as rf:
    data = rf.read()
    kwds["version"] = eval(pat.search(data).group(1))

if os.path.exists("README.rst"):
    with io.open("README.rst", encoding="utf-8") as rf:
        kwds["long_description"] = rf.read()

h2parser = Extension(
    name="ahserver.http2.h2parser",
    sources=[
        "ahparser/src/alphabet.c",
        "ahparser/src/msgbuf.c",
        "ahparser/src/parser.c",
        "ahparser/src/splitter.c",
        "ahparser/src/strbuf.c",
        "ahparser/src/strlen.c",
        "ahserver/http2/h2parser.pyx",
    ],
    include_dirs=["ahparser/include"],
    extra_compile_args=["-fno-strict-aliasing", "-g", "-O0"],
)

setup(
    name="ahserver",
    description="a simple http server.",
    author="James Yin",
    author_email="ywhjames@hotmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "Operating System :: OS Independent",
        "Programming Language :: Cython",
        "Programming Language :: Cython :: 3",
    ],
    packages=find_packages(exclude=["test.py"]),
    ext_modules=cythonize(h2parser),
    install_requires=["six"],
    extras_require={"uvloop": ["uvloop"]},
    entry_points={"console_scripts": ["ahsgi=ahserver.wsgi.main:main"]},
    **kwds
)
