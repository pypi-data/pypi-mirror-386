from setuptools import setup, find_packages

setup(
    name="easygui_wrap",
    version="1.0.6",
    author="Zaik",
    author_email="stickma6@gmail.com",
    description="A beginner-friendly, stylish GUI wrapper for Python using DearPyGui.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/thesmal",
    packages=find_packages(),
    install_requires=[
        "dearpygui>=2.0.0"
    ],
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    include_package_data=True,
    keywords="gui easygui_wrap dearpygui python",
)
