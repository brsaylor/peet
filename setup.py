from setuptools import setup, find_packages

setup(name="peet",
      version="1.0.20101012",
      description="Python Experimental Economics Toolkit",
      author="Ben Saylor",
      author_email="anbrs1@uaa.alaska.edu",
      url="http://econlab.uaa.alaska.edu/software.htm",
      install_requires=['wxPython>=2.8.0'],
      packages=find_packages()
      )
