from setuptools import setup, find_packages

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile["packages"], r=False)
test_requirements = convert_deps_to_pip(pfile["dev-packages"], r=False)

setup(
    name="burnysc2",
    packages=find_packages(exclude=["examples*", "examples"]),
    version="4.11.2",
    description="A StarCraft II API Client for Python 3",
    license="MIT",
    author="BurnySc2",
    author_email="gamingburny@gmail.com",
    url="https://github.com/Burnysc2/python-sc2",
    keywords=["StarCraft", "StarCraft 2", "StarCraft II", "AI", "Bot"],
    setup_requires=["pipenv"],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Real Time Strategy",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
