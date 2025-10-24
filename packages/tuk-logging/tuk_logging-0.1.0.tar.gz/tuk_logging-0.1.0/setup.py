#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import setuptools
from pathlib import Path

NAME = "tuk-logging"
DESCRIPTION = "TUK Logging Package"

CSD = Path(__file__).parent.resolve()
PATH_SRC = CSD / "src"
PATH_DOC = CSD / "doc"
PATH_TEST = CSD / "test"
PATH_REQUIREMENTS = CSD / "requirements.txt"
PATH_LICENSE = CSD / "LICENSE"
PATH_README = CSD / "README.md"


sys.path.insert(0, PATH_SRC.as_posix())
import tuk.logging as pkg



def _get_requirements():
    if not PATH_REQUIREMENTS.exists():
        return []
    with open(PATH_REQUIREMENTS, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def _get_long_description():
    if not PATH_README.exists():
        return ""
    with open(PATH_README, encoding='utf-8') as f:
        return f.read()



setuptools.setup(
    name=NAME,
    description=DESCRIPTION,
    long_description=_get_long_description(),
    long_description_content_type="text/markdown",
    version=pkg.__version__,
    license=pkg.__license__,
    author=pkg.__author__,
    author_email="dont@email.me",
    url=pkg.__url__,
    project_urls={
        "Bug Reports": pkg.__url__ + "/issues",
        "Source": pkg.__url__,
    },
    package_dir={"": PATH_SRC.as_posix()},
    packages=setuptools.find_namespace_packages(where=PATH_SRC.as_posix()),
    python_requires=">=3.11",
    install_requires=_get_requirements(),
    keywords=["logging", "log", "tuk"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ]
)

