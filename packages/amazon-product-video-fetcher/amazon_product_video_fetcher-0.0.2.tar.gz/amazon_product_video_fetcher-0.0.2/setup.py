import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="amazon-product-video-fetcher",
    version="0.0.2",
    author="Liran Bratt",
    author_email="brattlirannin@gmail.com",
    description="A Small tool to Extract and Download m3u8 videos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LiranBratt2121/amazon-product-video-fetcher",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)