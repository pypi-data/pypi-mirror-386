from setuptools import find_packages, setup

setup(
    name='allure-megauploader',
    version='0.0.1',
    description='Upload allure report',
    install_requires=['requests==2.28.1'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'testy': ['allure-megauploader=allure_megauploader']},
    py_modules=['allure_megauploader'],
)
