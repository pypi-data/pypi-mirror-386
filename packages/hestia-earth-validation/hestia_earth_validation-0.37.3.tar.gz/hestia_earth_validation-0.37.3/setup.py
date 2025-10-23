from setuptools import find_namespace_packages, setup

from hestia_earth.validation.version import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()


with open("requirements.txt", "r") as fh:
    REQUIRES = fh.read().splitlines()


setup(
    name='hestia_earth_validation',
    version=VERSION,
    description='HESTIA Data Validation library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Guillaume Royer',
    author_email='guillaumeroyer.mail@gmail.com',
    license='MIT',
    url='https://gitlab.com/hestia-earth/hestia-data-validation',
    keywords=['hestia', 'data', 'validation'],
    packages=find_namespace_packages(include=['hestia_earth.*']),
    include_package_data=True,
    python_requires='>=3',
    classifiers=[],
    install_requires=REQUIRES,
    scripts=['bin/hestia-validate-data'],
    extras_require={
        "models": ["hestia-earth-models>=0.75.1"],
        "spatial": ["hestia-earth-earth-engine>=0.6.0"],
        "distribution": ["hestia-earth-distribution>=0.3.1"]
    }
)
