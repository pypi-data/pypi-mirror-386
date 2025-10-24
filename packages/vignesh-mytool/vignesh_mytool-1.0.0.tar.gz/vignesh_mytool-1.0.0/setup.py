from setuptools import setup

setup(
    name="vignesh-mytool",          # package name
    version="1.0.0",
    packages=["mytool"],    # must match folder name
    entry_points={
        "console_scripts": [
            "mytool=mytool.main:main"  # command=name of package.function
        ]
    }
)

