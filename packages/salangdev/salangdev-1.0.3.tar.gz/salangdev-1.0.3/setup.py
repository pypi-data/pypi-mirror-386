from setuptools import setup

with open("long_des.txt", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='salangdev',
    version='1.0.3',
    description='SaLangDev - A tiny educational programming language (digit, one_letter, letters, outcome)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['salangdev'],
    entry_points={
        'console_scripts': [
            'salangdev=salangdev:main',
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
