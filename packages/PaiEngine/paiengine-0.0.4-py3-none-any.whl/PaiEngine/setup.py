from setuptools import setup, find_packages
from pathlib import Path
from PaiEngine import Attribute

current_folder = Path(__file__).parent
packages_folder = find_packages(where=str(current_folder))

setup(
    name="PaiEngine",
    version=Attribute.version,
    packages=packages_folder,
    install_requires=[
        "pygame>=2.0.0"
    ],
    description="PaiEngine - simple GUI engine",
    long_description=(current_folder / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Pai100707",
    url="https://github.com/Pai100707/PaiEngine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
