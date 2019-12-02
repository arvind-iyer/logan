from setuptools import setup, find_packages

setup(
    version="1.0.1",
    name="logan",
    package_dir={"": "src"},
    package_data={"": ["data/*"]},
    packages=find_packages(where="src"),
    install_requires=[""],
)
