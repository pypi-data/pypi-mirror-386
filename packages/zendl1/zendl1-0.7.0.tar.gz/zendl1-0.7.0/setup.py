from setuptools import setup, find_packages

setup(
    name="zendl1",
    version="0.7.0",
    packages=find_packages(),
    include_package_data=True,
    description="A simple example package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="zenitsu",
    python_requires=">=3.6",
)
