from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calcli",
    version="1.0.0",
    author="Tola Oyelola",
    author_email="tola@ootola.com",
    description="A simple, elegant terminal calculator with interactive mode",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tolaoyelola/calcli",
    py_modules=["calcli"],
    entry_points={
        "console_scripts": [
            "calcli=calcli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "colorama>=0.4.3",
        "pyperclip>=1.8.2",
    ],
)