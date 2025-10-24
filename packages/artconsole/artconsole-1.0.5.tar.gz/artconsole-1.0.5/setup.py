from setuptools import setup, find_packages

def readme():
    with open('README.md', 'r') as file:
        return file.read()

setup(
    name = 'artconsole',
    version = '1.0.5',
    author = 'Dima M. Shirokov',
    author_email = 'D.Shirokov05@yandex.ru',
    description = 'This is a simple library for outputting to the console or receiving simple ASCII art as a string.',
    long_description = readme(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/1123581321345589144233377610/artconsole',
    packages = find_packages(),
    classifiers = [
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    project_urls = {
        'GitHub': 'https://github.com/1123581321345589144233377610'
    },
    python_requires = '>=3.6'
)