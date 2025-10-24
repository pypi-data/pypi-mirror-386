from setuptools import setup, find_packages

setup(
    name="webjeux-flash-downloader",
    version="1.4",
    author="Salah eddine Talli",
    author_email="tallisalaheddine@gmail.com",
    description="Download flash games from WebJeux website",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
        "my_package": ["data/flipline_studio.png", "data/Webjeux_games_names.txt"],
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "pillow>=8.0.0",
        "customtkinter>=5.0.0"
    ],
    entry_points={
        "console_scripts": [
            "webjeux-flash-downloader=my_package.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.6",
    license="MIT",
)
