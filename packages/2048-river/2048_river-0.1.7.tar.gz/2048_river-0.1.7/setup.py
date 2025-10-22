from setuptools import setup, find_packages

setup(
    name="2048-river",
    version="0.1.7",
    packages=find_packages(), 
    include_package_data=True,
    install_requires=["requests", "pygame"],
    entry_points={
        "console_scripts": [
            "2048-river=main_launcher:main", 
        ],
    },
)
