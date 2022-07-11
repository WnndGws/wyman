from setuptools import setup

setup(
    name="wyman",
    version="3.0",
    py_modules=["wyman"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        wyman=wyman:main
    """,
)
