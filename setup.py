'''A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
'''

# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ligament',
    version='0.0.0.dev',
    description='A grunt-like build system for python',
    url='http://github.com/Adjective-Object/ligament',
    author='Adjective-Object',
    author_email='mhuan13@gmail.com',
    license='Apache 2',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7'],

    keywords='ligament grunt build automation',
    install_requires=['watchdog>=0.8.3', 'colorama>=0.3.3'],

    packages=['ligament', 'ligament_fs',
              'ligament_precompiler_template'],
    entry_points={
        'console_scripts': [
            'ligament=ligament:main']}
)
