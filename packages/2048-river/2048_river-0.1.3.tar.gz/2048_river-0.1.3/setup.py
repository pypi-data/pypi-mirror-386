from setuptools import setup

setup(
    name="2048-river",
    version="0.1.3",
    py_modules=["main_launcher"],
    install_requires=["requests", "pygame"],
    entry_points={
        "console_scripts": [
            "2048-river=main_launcher:main", 
        ],
    },
    include_package_data=True,
)
