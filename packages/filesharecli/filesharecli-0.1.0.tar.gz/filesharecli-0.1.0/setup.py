from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.1.0'
DESCRIPTION = 'FileShareCLI is a simple yet powerful Python-based CLI tool that lets developers share files and command snippets effortlessly from the terminal.'

# Setting up
setup(
    name="filesharecli",
    version=VERSION,
    author="Aravind Kumar Vemula",
    author_email="30lmas09@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    python_requires='>=3.8',
    url="https://github.com/lmas3009/filesharecli-pip",
    install_requires=['colorama'],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)