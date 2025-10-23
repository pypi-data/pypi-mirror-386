from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name="guispark",
    version="0.0.2",
    author="Lronardo",
    author_email="leonardonery616@gmail.com",
    description="Crie interfaces gráficas Python em segundos! ⚡",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.4.0",
        "PyQt6-WebEngine>=6.4.0",
    ],
    keywords=["python", "gui", "pyqt", "interface", "desktop", "app", "quick", "spark"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    project_urls={
        "Homepage": "https://github.com/seuusuario/guispark",
        "Bug Tracker": "https://github.com/seuusuario/guispark/issues",
    },
)