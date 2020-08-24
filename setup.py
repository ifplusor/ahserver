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

ahparser = Extension(
    name="ahserver.server.parser.ahparser",
    sources=[
        "ahparser/src/alphabet.c",
        "ahparser/src/hpack.c",
        "ahparser/src/huffman.c",
        "ahparser/src/index.c",
        "ahparser/src/msgbuf.c",
        "ahparser/src/parser.c",
        "ahparser/src/splitter.c",
        "ahparser/src/strbuf.c",
        "ahparser/src/strlen.c",
        "ahserver/server/parser/ahparser.pyx",
    ],
    include_dirs=["ahparser/include"],
    extra_compile_args=["-fno-strict-aliasing", "-g", "-O0"],
    language="c",
)

h2ext = Extension(
    name="ahserver.server.parser.*",
    sources=["ahserver/server/parser/*.pyx"],
    include_dirs=["ahparser/include"],
    extra_compile_args=["-fno-strict-aliasing", "-g", "-O0"],
    language="c",
)

setup(
    name="ahserver",
    description="a simple http server.",
    author="James Yin",
    author_email="ywhjames@hotmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: C",
        "Programming Language :: Cython",
        "Programming Language :: Cython :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["example"]),
    ext_modules=cythonize([ahparser, h2ext]),
    install_requires=["six"],
    extras_require={"uvloop": ["uvloop"], "asgi": ["asgiref"]},
    entry_points={
        "console_scripts": ["ahasgi=ahserver.application.asgi.main:main", "ahwsgi=ahserver.application.wsgi.main:main"]
    },
    license="BSD",
    keywords=["web server", "wsgi", "asgi", "http2"],
    zip_safe=False,
    **kwds
)
