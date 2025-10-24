import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="TallyTools",
    version="0.1.0",
    author="Rishikesh Mahajan",
    author_email="rishimahajan2410@gmail.com",
    description="A Python utility library for Tally operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rishikeshgmahajan/TallyTools", 
    license="MIT",
    packages=setuptools.find_packages(exclude=["test*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[],
)


