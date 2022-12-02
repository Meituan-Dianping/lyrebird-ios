from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lyrebird-ios',
    version='0.3.12',
    packages=['lyrebird_ios'],
    url='https://github.com/meituan/lyrebird-ios',
    author='HBQA',
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    zip_safe=False,
    classifiers=(
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
    ),
    entry_points={
        'lyrebird_plugin': [
            'ios = lyrebird_ios.manifest'
        ]
    },
    install_requires=[
        'lyrebird>=2.10.3',
        'facebook-wda==1.4.3',
        'tidevice==0.6.12'
    ],
    extras_require={
        'dev': [
            "autopep8",
            "pylint",
            "pytest"
        ]
    }
)
