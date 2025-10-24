from setuptools import setup, find_packages, Command
import os
import re


def read_version():
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'squidly/__init__.py')
    with open(path, 'r') as fh:
        return re.search(r'__version__\s?=\s?[\'"](.+)[\'"]', fh.read()).group(1)


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='squidly',
      version=read_version(),
      description='',
      long_description=readme(),
      long_description_content_type='text/markdown',
      author='William Reiger',
      author_email='w.rieger@uq.edu.au',
      url='https://github.com/WRiegs/Squidly',
      license='GPL3',
      project_urls={
          "Bug Tracker": "https://github.com/WRiegs/Squidly/issues",
          "Documentation": "https://github.com/WRiegs/Squidly",
          "Source Code": "https://github.com/WRiegs/Squidly",
      },
      classifiers=[
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
      ],
      keywords=['gene-annotation', 'bioinformatics', 'catalytic-site-prediction'],
      packages=['squidly'],
      include_package_data=True,
      package_data={
          'squidly': ['install.sh'],
      },
      entry_points={
          'console_scripts': [
                'squidly = squidly.__main__:app',

          ]
      },
      install_requires=['pandas>=2.1.4', 'numpy>=1.22.4', 'fair-esm', 'sciutil>=1.0.3', 'typer', 'psutil', 'biopython',
                        'sciutil', 'tqdm', 'enzymetk', 'huggingface_hub'],
      python_requires='>=3.10',
      data_files=[("", ["LICENSE"])]
      )