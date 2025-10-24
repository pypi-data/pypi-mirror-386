from pathlib import Path

import setuptools

VERSION = "0.0.1"

NAME = "hallelujah"

INSTALL_REQUIRES = [
    "numpy>=2.2.1",
    "scipy>=1.15.0",
    "networkx[default]>=3.4.2"
]

setuptools.setup(
    name=NAME,
    version=VERSION,
    description="Compute the Approximate Vertex Cover for undirected graph encoded in DIMACS format.",
    url="https://github.com/frankvegadelgado/hallelujah",
    project_urls={
        "Source Code": "https://github.com/frankvegadelgado/hallelujah"
    },
    author="Frank Vega",
    author_email="vega.frank@gmail.com",
    license="MIT License",
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
    ],
    python_requires=">=3.12",
    # Requirements
    install_requires=INSTALL_REQUIRES,
    packages=["hallelujah"],
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'pray = hallelujah.app:main',
            'test_pray = hallelujah.test:main',
            'batch_pray = hallelujah.batch:main'
        ]
    }
)