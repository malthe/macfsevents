import os

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


ext_modules = [
    Extension(
        name="_fsevents",
        sources=["_fsevents.c", "compat.c"],
        extra_link_args=[
            "-framework",
            "CoreFoundation",
            "-framework",
            "CoreServices",
        ],
    ),
]

setup(
    name="MacFSEvents",
    version="0.8.4",
    description=(
        "Thread-based interface to file system observation " "primitives."
    ),
    long_description="\n\n".join((read("README.rst"), read("CHANGES.rst"))),
    license="BSD",
    data_files=[("", ["compat.h", "LICENSE.txt", "CHANGES.rst"])],
    author="Malthe Borch",
    author_email="mborch@gmail.com",
    url="https://github.com/malthe/macfsevents",
    cmdclass=dict(build_ext=build_ext),
    ext_modules=ext_modules,
    platforms=["Mac OS X"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: C",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
    ],
    zip_safe=False,
    test_suite="tests",
    py_modules=["fsevents"],
)
