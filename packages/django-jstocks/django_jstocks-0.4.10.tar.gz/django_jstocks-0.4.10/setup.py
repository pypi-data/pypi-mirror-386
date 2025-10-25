from setuptools import find_packages  # type: ignore
from distutils.core import setup  # type: ignore


def parse_requirements(filename, session=False):
    """load requirements from a pip requirements file"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


install_requires = parse_requirements("requirements.txt", session=False)
packages = find_packages(exclude=["*.venv", "*.venv.*", "venv.*", "venv"])

setup(
    name="django-jstocks",
    version="0.4.10",
    author="Jani Kajala",
    author_email="kajala@gmail.com",
    packages=packages,
    include_package_data=True,
    url="https://github.com/kajala/django-jstocks",
    license="Copyright (C) Jani Kajala. All rights reserved",
    description="Library for managing shares issuance",
    long_description=open("README.md").read(),
    zip_safe=True,
    install_requires=install_requires,
)
