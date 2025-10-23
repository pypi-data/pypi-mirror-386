from setuptools import setup, find_packages

def readme():
  with open('README.md', 'r') as f:
    return f.read()

setup(
  name='arit777',
  version='0.1',
  author='Olegs Verhodubs',
  author_email='oleg.verhodub@inbox.lv',
  description='This is a prototype package for generating rules from raw text',
  long_description=readme(),
  long_description_content_type='text/markdown',
  packages=find_packages(),
  license='Apache-2.0',
  classifiers=[
    'Programming Language :: Python :: 3.13',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent'
  ],
  python_requires='>=3.13'
)