import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="syosetumaster",
    version="0.1.1",
    author="Hijkstuv",
    author_email="kingcrush1729@gmail.com",
    description="simple crawling + translating project with syosetuka ni narou",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hijkstuv/syosetumaster",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=[
        "selenium==4.24.0",
        "openai==1.95.1",
        "pydantic==2.10.6",
        "python-dotenv==0.21.0",
        "typing-extensions==4.12.2"
    ]
)
