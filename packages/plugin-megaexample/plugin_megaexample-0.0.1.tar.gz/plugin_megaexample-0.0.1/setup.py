
from setuptools import find_packages, setup

setup(
    name='plugin-megaexample',
    version='0.0.1',
    description='Example of testy plugin',
    install_requires=['openpyxl==3.1.1'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'testy': ['plugin-megaexample=plugin_megaexample']},
)
