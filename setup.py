from glob import glob
from setuptools import setup, find_packages

setup(
    name='webduino-generator',
    version='0.3',
    license='UNLICENSE',
    url='https://github.com/StoneLabs/webduino-generator',
    author='Levy Ehrstein',
    author_email='levyehrstein@googlemail.com',
    description='Python program to automatically generate source code for an arduino web server',
    long_description='Python program to automatically create arduino webserver from folder.\nSupports basically all file types. For example: html, js, css, images, and arbitrary binaries.',
    packages=["webduino_generator"],
    package_data={"webduino_generator": ["templates/*", "demo/*"]},
    include_package_data=True,
    entry_points={
        'console_scripts': ['webduino-generator=webduino_generator.entrypoint:main'],
    },
    install_requires=["jinja2", "rich"],
)