import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cookbase",
    version="0.1.0",
    author="Hernán Blanco Landa",
    author_email="hblanco@pm.me",
    description=(
        "A platform to validate, store and manage cooking recipes based on the JSON "
        "Cookbase Format."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hblanko/cookbase",
    packages=setuptools.find_packages(),
    install_requires=[
        "attrs == 19.3.0",
        "jsonschema == 3.2.0",
        "networkx == 2.4",
        "paramiko == 2.7.1",
        "pymongo == 3.10.1",
        "requests == 2.21.0",
        "ruamel.yaml == 0.16.10",
        "uritools == 3.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
