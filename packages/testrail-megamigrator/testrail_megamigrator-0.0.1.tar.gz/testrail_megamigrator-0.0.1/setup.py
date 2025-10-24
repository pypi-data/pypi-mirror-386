
from setuptools import find_packages, setup

setup(
    name='testrail-megamigrator',
    version='0.0.1',
    description='Plugin to migrate your data from testrail',
    install_requires=[
        'tqdm==4.64.1',
        'aiohttp==3.8.3',
        'aiofiles==22.1.0',
        'factory-boy==3.2.1'
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'testy': ['testrail-megamigrator = testrail_megamigrator']},
    py_modules=['testrail_megamigrator'],
)
