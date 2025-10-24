from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="exelock",
    version="1.0.1",
    author="pengmin",
    author_email="877419534@qq.com",
    description="A simple library to prevent multiple instances of a program from running",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    keywords="single instance lock prevent duplicate",
    url="https://github.com/yourusername/exelock",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/exelock/issues",
        "Source": "https://github.com/yourusername/exelock",
    },
)