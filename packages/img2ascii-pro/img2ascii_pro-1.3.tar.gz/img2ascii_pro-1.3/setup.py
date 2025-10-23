from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="img2ascii_pro",
    version="1.3",
    author="Mohamed Elsayed",
    author_email="ms.moh.dev@gmail.com",
    description="Convert images to colored ASCII art (text + HTML)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MohamedElsayed-debug/img2ascii-pro",
    packages=find_packages(),
    install_requires=[
        "Pillow"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
    project_urls={
    "Source": "https://github.com/MohamedElsayed-debug/img2ascii-pro",
    },

    entry_points={
        'console_scripts': [
            'img2ascii_pro=img2ascii_pro.__main__:main',
        ],
    },
)