"""Bundle up packages from cidc_api for use in other services."""

from setuptools import setup

with open("requirements.modules.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

from cidc_api import __version__

setup(
    name="nci_cidc_api_modules",
    description="SQLAlchemy data models and configuration tools used in the NCI CIDC API",
    python_requires=">=3.13",
    install_requires=requirements,
    license="MIT license",
    packages=[
        "cidc_api.config",
        "cidc_api.models",
        "cidc_api.shared",
        "cidc_api.models.files",
    ],
    url="https://github.com/NCI-CIDC/cidc-api-gae",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=__version__,
    zip_safe=False,
)
