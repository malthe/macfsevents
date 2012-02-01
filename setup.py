import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

ext_modules = [
    Extension(name = '_fsevents',
              sources = ['_fsevents.c'],
              extra_link_args = ["-framework","CoreFoundation",
                               "-framework","CoreServices"],
             ),
    ]

setup(name = "MacFSEvents",
      version = "0.2.5",
      description = "Thread-based interface to file system observation primitives.",
      long_description = "\n\n".join((read('README.rst'), read('CHANGES.rst'))),
      license = "BSD",
      author = "Malthe Borch",
      author_email = "mborch@gmail.com",
      cmdclass = dict(build_ext=build_ext),
      ext_modules = ext_modules,
      platforms = ["Mac OS X"],
      classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: C',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Filesystems',
      ],
      zip_safe=False,
      test_suite="tests",
      py_modules=['fsevents'],
     )
