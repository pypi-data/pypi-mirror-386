import os
from io import open
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fobj:
    long_description = fobj.read()

requires = [
    "click",
]

setup(
    name="rot-codec",
    version="0.1.2",
    description="rot5, rot13, rot18, rot47 codecs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="rRR0VrFP",
    maintainer="rRR0VrFP",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=["rot-codec", "gif"],
    requires=requires,
    install_requires=requires,
    packages=find_packages("."),
    py_modules=["rot_codec"],
    entry_points={
        "console_scripts": [
            "rot-codec = rot_codec:rot_cli",
        ]
    },
)
