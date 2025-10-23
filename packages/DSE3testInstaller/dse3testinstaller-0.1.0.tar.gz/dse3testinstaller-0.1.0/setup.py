from setuptools import setup, find_packages

setup(
    name="DSE3testInstaller",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "DSE3testInstaller": ["mytool.exe"],
    },
    author="Krishna kanth",
    author_email="krishnakanth6768@gmail.com",
    description="A package that includes a standalone EXE",
    long_description="Put your long description here.",
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
