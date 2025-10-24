from setuptools import setup, find_packages

setup(
    name="easygui-wrap",       # your package name
    version="0.11.5",
    author="Thesmal",
    author_email="stickma6@gmail.com",
    description="Stylish, hybrid callback GUI wrapper for Python (Tkinter & DearPyGui)",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "dearpygui>=2.0"  # optional
    ],
)
