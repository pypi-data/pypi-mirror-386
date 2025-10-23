"""Setup script for PyAnsysV23"""

from setuptools import setup, find_packages

setup(
    name="PyAnsysV23",
    version="0.23.0",
    packages=find_packages(),
    python_requires=">=3.7",
    author="PyAnsys Contributors",
    description="Virtual SpaceClaim API V23 library for Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7+",
    ],
)
