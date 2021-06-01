# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='CPPS',
    version='0.1.0',
    description='Cloud Sisal',
    long_description=readme,
    author='Alex Malishev',
    author_email='alex.m.work@yandex.ru',
    url='https://github.com/alexm',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

