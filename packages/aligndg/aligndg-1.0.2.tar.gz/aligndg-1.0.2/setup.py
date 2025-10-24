from setuptools import Command, find_packages, setup

__lib_name__ = "aligndg"
__lib_version__ = "1.0.2"
__description__ = "Alignment of distant slices of spatially resolved transcriptomics with graph learning model"
__url__ = "https://github.com/xkmaxidian/AlignDG"
__author__ = "Yu Wang"
__author_email__ = "yuwangxdu@163.com"
__license__ = "MIT"
__keywords__ = ["Spatial transcriptomics", "Slice alignment", "Slice integration", "Optimal transport"]
__requires__ = [
    "scanpy>=1.9.3",
    "numpy>=1.24.0",
    "pandas>=1.5.0",
    "anndata>=0.9.0",
    "matplotlib>=3.7.1",
    "scipy>=1.11.2",
    "scikit-learn>=1.2.2",
    "psutil>=5.9.0",
    "cloudpickle>=2.2.0",
    "tqdm>=4.65.0",
    "leidenalg>=0.10.1",
    "networkx>=3.2.0",
    "docrep>=0.3.2",
    "jax>=0.6.0",
    "ott-jax[neural]>=0.5.0",
    "torch>=2.0.1",
    "torch-geometric>=2.3.1",
    "wrapt>=1.13.2",
    "rich>=13.5.0",
    "plotly",
    "pyyaml",
    "torch-geometric",
    "torch-cluster",
    "torch-scatter",
    "torch-sparse",
]

setup(
    name=__lib_name__,
    version=__lib_version__,
    description=__description__,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    license=__license__,
    packages=find_packages(),
    install_requires=__requires__,
    zip_safe=False,
    include_package_data=True,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]

)