import setuptools
import os
import shutil
from setuptools import Command
import requests

with open("README.md", "r") as fh:
    long_description = fh.read()


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        if os.path.exists('upplib.egg-info'):
            shutil.rmtree('upplib.egg-info')


def get_version():
    response = requests.get("https://pypi.org/pypi/upplib/json")
    if response.status_code == 200:
        latest_version = response.json()["info"]["version"]
    else:
        raise Exception("unable to obtain the latest version of the library")

    version_parts = list(map(int, latest_version.split('.')))
    for i in reversed(range(len(version_parts))):
        if version_parts[i] < 9:
            version_parts[i] += 1
            break
        else:
            version_parts[i] = 0
    return '.'.join(map(str, version_parts))


version = get_version()

setuptools.setup(
    name="upplib",
    version=version,
    author="Luck",
    author_email="wantwaterfish@gmail.com",
    description="util",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=[
        "openpyxl>=3.1.2",
        "xlrd>=2.0.1",
        "bs4>=0.0.2",
        "aliyun-log-python-sdk>=0.9.32",
        "huaweicloudsdkcore>=3.1.166",
        "huaweicloudsdklts>=3.1.166",
        "requests>=2.32.3",
        "PyMySQL>=1.1.0",
        "pyarrow>=16.0.0",
        "sqlparse>=0.5.0",
        "redis>=6.4.0",
        "pandas>=2.2.2"
    ],
    license="MIT",
    cmdclass={
        'clean': CleanCommand
    }
)
