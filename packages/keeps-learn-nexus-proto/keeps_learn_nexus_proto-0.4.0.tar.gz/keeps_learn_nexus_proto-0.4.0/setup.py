import os

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='keeps-learn-nexus-proto',
    version='0.4.0',
    description='Shared Protocol Buffer definitions for Nexus microservices',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Keeps',
    author_email='dev@keeps.com',
    url='https://github.com/Keeps-Learn/nexus-proto',
    license='MIT',
    packages=find_packages(),
    package_data={
        '': ['**/*.proto'],
    },
    include_package_data=True,
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries',
        'Topic :: Communications',
    ],
    keywords='grpc protobuf proto microservices',
)

