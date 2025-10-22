from setuptools import setup, find_packages

setup(
    name="2048-river",
    version="0.1.1",
    py_modules=["main_launcher"],
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "2048-river=main_launcher:main", 
        ],
    },
)
