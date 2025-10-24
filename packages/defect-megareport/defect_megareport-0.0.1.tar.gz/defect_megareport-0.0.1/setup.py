
from setuptools import find_packages, setup

setup(
    name='defect-megareport',
    version='0.0.1',
    description='Plugin to show defect report',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'testy': ['defect-megareport=defect_megareport']},
    py_modules=['defect_megareport'],
)
