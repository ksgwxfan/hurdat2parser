from setuptools import setup
 
with open("README.md", "r") as fh: 
    readme = fh.read() 

setup(
    name = 'hurdat2parser',
    version = '2.0.0',
    author = 'Kyle S. Gentry',
    author_email = 'KyleSGentry@outlook.com',
    url = 'http://github.com/ksgwxfan/hurdat2parser',
    description = 'Interpret Hurricane Data contained in HURDAT2',
    long_description = readme,
    long_description_content_type = "text/markdown",
    license = 'MIT',
    packages = ['hurdat2parser'],
    zip_safe = False,
    classifiers=[
        "Programming Language :: Python :: 3", 
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    install_requires=['pyshp', 'geojson'],
    python_requires='>=3.5',
    keywords="hurricane hurdat2 meteorology weather"
)