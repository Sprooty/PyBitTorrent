from setuptools import setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='PyBitTorrent',
    version='0.7.0',
    author='Gaffner',
    author_email='gefen102@gmail.com',
    url="https://github.com/gaffner/PyBitTorrent",
    packages=['PyBitTorrent'],
    description='Download torrent files according to BitTorrent specifications',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'bitstring~=4.0.1',
        'rich~=12.6.0',
        'requests~=2.22.0',
    ]
)