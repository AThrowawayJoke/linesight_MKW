from setuptools import setup, find_packages

def read_requirements(filename):
    with open(filename, 'r') as f:
        requirements = f.read().splitlines()
    return requirements

setup(
    name='linesight-MKW',
    description='Trackmania AI with reinforcement learning.',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.10.0,<3.13.0', # ensure all packages are installed with correct python version
    install_requires=read_requirements('requirements_pip.txt') + read_requirements('requirements_conda.txt'),
    packages=find_packages(include=["MKW_rl", "config_files"]),
    extras_require={
        "doc": ["sphinx", "sphinx_rtd_theme", "sphinxcontrib.youtube"],
    },
)
