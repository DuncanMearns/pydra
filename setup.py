import setuptools

setuptools.setup(
    name="pydra-experiment-control",
    version="0.1.1",
    author="Duncan Mearns",
    author_email="duncan.mearns@bi.mpg.de",
    description="Pydra provides a framework for building experiment controllers with python",
    install_requires=[
        "matplotlib",
        "numpy",
        "pandas",
        "pyqtgraph",
        "pyzmq"
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.8'
)
