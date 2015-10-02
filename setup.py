"""\
Tools for managing IDR data.
"""

from distutils.core import setup


NAME = "pyidr"
DESCRIPTION = __doc__
URL = "https://github.com/openmicroscopy/idr-metadata"
CLASSIFIERS = [
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Intended Audience :: Science/Research",
]


setup(
    name=NAME,
    description=DESCRIPTION,
    url=URL,
    classifiers=CLASSIFIERS,
    packages=["pyidr"],
)
