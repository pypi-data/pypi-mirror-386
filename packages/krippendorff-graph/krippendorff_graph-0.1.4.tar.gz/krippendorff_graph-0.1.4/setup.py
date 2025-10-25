from setuptools import setup
import os
# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
#print(os.listdir())
#with open('requirements.txt') as f:
requirements = ['pandas', 'scikit-learn', 'requests', 'networkx', 'tqdm', 'numpy']

setup(
    name='krippendorff-graph',
    version='0.1.4',
    description='A Python package for computing krippendorffs alpha for graph (modified from https://github.com/grrrr/krippendorff-alpha/blob/master/krippendorff_alpha.py)',
    url='https://anonymous.4open.science/r/BE2B/',
    author='anonymous author',
    author_email='anonymous@email.com',
    license='Apache 2 License',
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=["krippendorff_graph"]
)
