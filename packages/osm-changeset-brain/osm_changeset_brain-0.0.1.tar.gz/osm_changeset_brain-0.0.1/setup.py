import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osm_changeset_brain",
    version="0.0.1",
    author="Mateusz Konieczny",
    author_email="matkoniecz@tutanota.com",
    description="countervandalism changeset analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="https://github.com/matkoniecz/example_python_package", TODO
    packages=setuptools.find_packages(),
    license = "AGPL-3.0-only",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    # for dependencies syntax see https://python-packaging.readthedocs.io/en/latest/dependencies.html
) 
