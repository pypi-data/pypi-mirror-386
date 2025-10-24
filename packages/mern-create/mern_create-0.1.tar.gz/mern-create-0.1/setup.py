from setuptools import setup

setup(
    name="mern-create",
    version="0.1",
    packages=["mern"],
    include_package_data=True,
    install_requires=[],  # No Python dependencies
    entry_points={
        "console_scripts": [
            "mern = mern.cli:main"
        ]
    },
    package_data={"mern": ["mern.sh"]},  # include the bash script
)

