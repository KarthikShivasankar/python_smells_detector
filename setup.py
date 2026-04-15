from setuptools import setup, find_packages

setup(
    name="code_quality_analyzer",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "astroid",
        "networkx",
        "pyyaml",
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "analyze_code_quality=code_quality_analyzer.main:analyze_project",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to detect code smells, architectural smells, and structural smells in Python projects",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code_quality_analyzer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        'dev': [
            'pytest',
            'sphinx',
            'sphinx-rtd-theme',
        ],
    },
)