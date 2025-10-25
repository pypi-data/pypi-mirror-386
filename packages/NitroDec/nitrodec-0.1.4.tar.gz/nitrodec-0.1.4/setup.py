from setuptools import setup, find_packages

setup(
    name="NitroDec",
    version="0.1.4",
    packages=find_packages(),
    install_requires=[
        "starlette[full]",
        "uvicorn"
    ],
    description="Decorator For Starlette, FastAPI style Decorators",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="@Nactire",
    author_email="yuvrajmodz@gmail.com",
    url="https://github.com/yuvrajmodz/NitroDec",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)