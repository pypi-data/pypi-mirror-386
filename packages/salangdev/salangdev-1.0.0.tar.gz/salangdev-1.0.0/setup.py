from setuptools import setup

# Read long description from file
with open("long_des.txt", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='salangdev',
    version='1.0.0',
    description='salangdev - A tiny educational programming language with simple syntax (digit, one_letter, letters, outcome)',
    long_description=long_description,
    long_description_content_type='text/markdown',  # important for PyPI formatting
    py_modules=['salangdev'],  # your main file must be named salangdev.py
    entry_points={
        'console_scripts': [
            'salangdev=salangdev:main',  # match module and command name
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