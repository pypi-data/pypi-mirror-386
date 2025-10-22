from setuptools import setup, find_packages

from xmlgenerator import __version__

setup(
    name='xmlgenerator',
    version=__version__,
    packages=find_packages(exclude=("tests", "tests.*")),
    entry_points={
        'console_scripts': [
            'xmlgenerator=xmlgenerator.bootstrap:main'
        ],
    },
    install_requires=[
        'lxml',
        'xmlschema',
        'Faker',
        'rstr',
        'PyYAML',
        'shtab'
    ],
    author='Alexey Akimov',
    author_email='lex.akimov23@gmail.com',
    description='Generates XML documents from XSD schemas',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lexakimov/xmlgenerator',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
