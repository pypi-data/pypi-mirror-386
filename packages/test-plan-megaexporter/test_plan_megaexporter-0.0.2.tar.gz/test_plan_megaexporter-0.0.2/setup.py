
from setuptools import find_packages, setup

setup(
    name='test_plan_megaexporter',
    version='0.0.2',
    description='Export test plan and cases to PDF',
    install_requires=['reportlab'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'testy': ['test-plan-megaexporter=test_plan_megaexporter']},
    py_modules=['test_plan_megaexporter'],
)
