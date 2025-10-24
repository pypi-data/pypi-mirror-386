from setuptools import setup, find_packages
from Cython.Build import cythonize

def is_requirement(line):
    return not (line.strip() == "" or line.strip().startswith("#"))

with open('README.md') as readme_file:
    README = readme_file.read()

with open("requirements.txt") as f:
    REQUIREMENTS = [line.strip() for line in f if is_requirement(line)]

setup(
    name="whitespacetokenizer",
    version='1.0.4',
    description='Fast python whitespace tokenizer wtitten in cython.',
    long_description_content_type="text/markdown",
    long_description=README,
    license='The Unlicense',
    ext_modules=cythonize("whitespacetokenizer/*.pyx", language_level="3", language="c++"),
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    author='Martin Dočekal',
    keywords=['tokenizer', 'whitespace'],
    url='https://github.com/mdocekal/whitespacetokenizer',
    python_requires='>=3.10',
    install_requires=REQUIREMENTS,
)
