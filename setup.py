from glob import glob
from setuptools import setup, find_packages

setup(
    name='webduino-generator',
    version='0.1',
    url='https://github.com/StoneLabs/webduino-generator',
    author='Levy Ehrstein',
    author_email='levyehrstein@googlemail.com',
    description='Python program to automatically generate source code for an arduino web server',
    packages=["webduino_generator"],
    package_data={"webduino_generator": ["templates/*"]},
    include_package_data=True,
    entry_points = {
        'console_scripts': ['webduino-generator=webduino_generator.generator:main'],
    },
    install_requires=[],
)