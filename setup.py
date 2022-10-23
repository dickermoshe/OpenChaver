from setuptools import setup, find_packages
from openchaver.__about__ import (__version__, __author__, __author_email__,
                                  __license__, __url__)
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openchaver_client",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description="An open source alternative to WebChaver.",
    url=__url__,
    license=__license__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'click==8.1.3', 'Flask==2.2.2', 'marshmallow==3.18.0', 'mss==6.1.0',
        'numpy==1.23.4', 'onnxruntime==1.12.1', 'opencv_python==4.6.0.66',
        'oschmod==0.3.12', 'peewee==3.15.3', 'Pillow==9.2.0', 'psutil==5.9.3',
        'pywin32==304', 'requests==2.28.1'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'openchaver = openchaver.__main__:cli',
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
    ],
)
