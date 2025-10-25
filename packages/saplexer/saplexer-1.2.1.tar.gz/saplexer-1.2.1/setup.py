from setuptools import setup, find_packages

setup(
    name="saplexer",
    version="1.2.1",
    author="SeventyThree",
    author_email="73@gmail.com",
    description="A simple and efficient package to display text files from folders A and B.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)