from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="copymachine-cli",
    version="0.1.0",
    description="Assemble your Copy Machine AI-generated image packs into videos locally using FFmpeg.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Copy Machine",
    url="https://app.getcopymachine.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "tqdm>=4.64.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "copymachine=copymachine.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
