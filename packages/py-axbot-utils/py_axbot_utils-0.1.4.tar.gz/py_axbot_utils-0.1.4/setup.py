# setup.py
from setuptools import setup, find_packages

setup(
    name="py_axbot_utils",  # Replace with your package name
    version="0.1.4",
    author="AutoXing",
    author_email="someone@autoxing.com",
    description="Utilities for AutoXing Robotics",
    long_description=open("README.md").read(),  # Use long description from README
    long_description_content_type="text/markdown",
    url="https://github.com/AutoxingTech/py_axbot_utils",  # Replace with your package URL
    packages=find_packages(),
    # Explicitly set license and disable auto-including license files in metadata to avoid
    # the unrecognized 'license-file' field on PyPI/Warehouse.
    license="MIT",
    license_files=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
