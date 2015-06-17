#!/usr/bin/python3
from setuptools import setup
setup(name="yavdrctl",
      version='0.0.1',
      author="Alexander Grothe",
      author_email="seahawk1986@gmx.de",
      description=("a replacement for vdrctl in python3"
                   "with additional bells and whistles"),
      packages=['yavdrctl'],
      entry_points={
          'console_scripts': [
              'yavdrctl = yavdrctl:main',
          ],
      },
      )
