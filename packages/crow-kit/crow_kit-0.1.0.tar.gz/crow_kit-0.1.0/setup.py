from setuptools import setup, find_packages

setup(
    name="crow-kit",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "selenium>=4.0.0",
        "beautifulsoup4>=4.12.0",
        "webdriver-manager>=3.8.5"
    ],
    python_requires='>=3.8',
    description="A lightweight Python toolkit for wrapper generation and data extraction (CroW framework).",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hmjamil/CroW/crow-kit",
    author="Kallol Naha",
    author_email="kallolnaha@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
