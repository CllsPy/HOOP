from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="HOOP",
    version="v1",
    author="Cll & RM",
    packages=find_packages(),
    install_requires = requirements,
)