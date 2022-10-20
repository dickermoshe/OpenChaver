from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openchaver_client",
    version='0.4.1',
    author="Moshe Dicker",
    author_email='mail@openchaver.com',
    description="An open source alternative to WebChaver.",
    url='https://github.com/dickermoshe/OpenChaver',
    license='GNU General Public License v3.0',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'alembic==1.8.1', 'banal==1.0.6', 'certifi==2022.9.24',
        'charset-normalizer==2.1.1', 'click==8.1.3', 'colorama==0.4.5',
        'coloredlogs==15.0.1', 'dataset==1.5.2', 'Flask==2.2.2',
        'flatbuffers==22.9.24', 'greenlet==1.1.3.post0', 'humanfriendly==10.0',
        'idna==3.4', 'itsdangerous==2.1.2', 'Jinja2==3.1.2', 'Mako==1.2.3',
        'MarkupSafe==2.1.1', 'marshmallow==3.18.0', 'mpmath==1.2.1',
        'mss==6.1.0', 'numpy==1.23.4', 'onnxruntime==1.12.1',
        'opencv-python==4.6.0.66', 'oschmod==0.3.12', 'packaging==21.3',
        'Pillow==9.2.0', 'protobuf==4.21.8', 'psutil==5.9.3',
        'pyparsing==3.0.9', 'pyreadline3==3.4.1', 'pywin32==304',
        'requests==2.28.1', 'SQLAlchemy==1.4.42', 'sympy==1.11.1',
        'urllib3==1.26.12', 'Werkzeug==2.2.2'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'openchaver = openchaver.__main__:cli',
        ],
    },
    python_requires=">=3.10",
)
