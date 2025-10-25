from setuptools import setup, find_packages

setup(
    name="spst",
    version="0.1.0",
    description="A package that prints Python code",
    author="joint-suresh",
    author_email="jointsuresh@outlook.com",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "spst = spst.__main__:main",
        ],
    },
    install_requires=[],  # Add dependencies if needed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
