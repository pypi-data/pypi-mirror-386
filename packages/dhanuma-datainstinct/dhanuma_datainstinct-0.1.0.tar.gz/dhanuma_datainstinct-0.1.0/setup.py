from setuptools import setup, find_packages

setup(
    name="dhanuma_datainstinct",
    version="0.1.0",
    author="Dhanush",
    author_email="dhanushm.analyst@gmail.com",
    description="A lightweight data profiler for CSV JSON and Excel files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas>=1.3.0","openpyxl>=3.0.0"],
    python_requires=">=3.8",
)
