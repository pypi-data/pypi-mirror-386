"""
PyDataGrid - A powerful data grid library for Python applications
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pydatagrid",
    version="1.0.0",
    author="PyDataGrid Team",
    author_email="info@pydatagrid.com",
    description="A powerful data grid library with sorting, filtering, pagination, and export features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pydatagrid",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Flask>=2.0.0",
        "flask-cors>=3.0.0",
    ],
    include_package_data=True,
    package_data={
        "pydatagrid": [
            "templates/*.html",
            "static/css/*.css",
            "static/js/*.js",
        ],
    },
)
