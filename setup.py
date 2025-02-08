from setuptools import setup, find_packages

setup(
    name="data-platform-status",
    version="0.1.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=[
        "requests",
        "azure-identity",
    ],
)
