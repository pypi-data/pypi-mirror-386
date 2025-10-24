from setuptools import setup

# Read long description from file (optional, but recommended)
with open("long_des.txt", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='salangdev',  # PyPI package name (must be unique)
    version='1.0.1',
    description='SaLangDev - A tiny educational programming language with simple syntax (digit, one_letter, letters, outcome)',
    long_description=long_description,
    long_description_content_type='text/markdown',  # For proper PyPI formatting
    py_modules=['salangdev'],  # Your main Python module must be named salangdev.py
    entry_points={
        'console_scripts': [
            'salangdev=salangdev:main',  # Creates a command `salangdev` in terminal
        ],
    },
    author='Salman Fareed Chishty',
    license='MIT',
    keywords='language interpreter education salang programming',
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Education',
        'Topic :: Software Development :: Interpreters',
    ],
)