import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gamlset",
    version="0.1.0",
    author="byundojin",
    author_email="byundojin0216@gmail.com",
    description="Type집합을 만드는 라이브러리 입니다.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gamultong/gamlset",
    packages=setuptools.find_packages(exclude=["tests", "tests.*", "example", "example.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Typing :: Typed",
    ],
    python_requires=">=3.9",
    extras_require={
        "dev": [],
    },
    package_data={
        "gamlset": ["py.typed"],
    },
    include_package_data=True,
)
