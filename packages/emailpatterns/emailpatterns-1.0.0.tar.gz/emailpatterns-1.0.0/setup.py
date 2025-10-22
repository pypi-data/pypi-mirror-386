from setuptools import setup, find_packages

setup(
    name='emailpatterns',  # must be unique on PyPI
    version='1.0.0',
    packages=find_packages(),
    description='Shared Email Pattern Generator',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Pulak Pattanayak',
    author_email='pulak.pattanayak@gmail.com',
    url='https://github.com/pupattan/emailpatterns',
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
