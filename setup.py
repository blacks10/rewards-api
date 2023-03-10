
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kleo-rewards",
    version="0.0.1",
    author="Kleomedes Dev Team",
    author_email="",
    description="Kleomedes rewards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
