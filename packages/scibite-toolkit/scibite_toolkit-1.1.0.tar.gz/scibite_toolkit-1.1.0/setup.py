import setuptools

VERSION = "1.1.0"

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='scibite_toolkit',
                 version=VERSION,
                 description='scibite-toolkit - python library for calling SciBite applications: TERMite, TExpress, SciBite Search, CENtree and Workbench. The library also enables processing of the JSON results from such requests',
                 url='https://github.com/elsevier-health/scibite-toolkit',
                 install_requires=[
                     "bs4",
                     "pandas",
                     "openpyxl",
                     "requests",
                     "sphinx",
                     "sphinx-js",
                     "rst2pdf"
                 ],
                 extras_require={},
                 author='SciBite',
                 author_email='help@scibite.com',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 license='Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License',
                 packages=setuptools.find_packages(),
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "Operating System :: OS Independent",
                 ],
                 data_files=[("", ["LICENSE.txt"])],
                 zip_safe=False)
