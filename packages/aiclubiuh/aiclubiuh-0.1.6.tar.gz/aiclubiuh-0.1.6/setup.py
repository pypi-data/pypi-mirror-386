from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='aiclubiuh',
    version='0.1.6',
    packages=find_packages(),
    description='Thư viện hỗ trợ cho AI Club IUH',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='htanh',
    author_email='anhkhdl@gmail.com',
    url="https://main.aiclubiuh.com",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        "rich>=13.0.0"
    ],
)
