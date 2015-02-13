from __future__ import unicode_literals
from distutils.core import setup
from setuptools import find_packages

setup(
    name='django-mintapi',
    version='0.1.0',
    author='Drew Worthey',
    author_email='drew@drewworthey.com',
    packages=['django_mint'],
    url='https://github.com/zabracks/django-mintapi',
    license='MIT license, see LICENSE.txt',
    description='Use Mint.com transaction history and account information in Django projects',
    long_description=open('README.txt').read(),
    zip_safe=False,

    requires=[
        'mintapi==1.7',
        'pandas==0.15.2',
    ]
)