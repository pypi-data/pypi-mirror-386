from setuptools import setup, find_packages

setup(
    name="himpunanmatdis",
    version="1.0.0",
    author="Nama Kamu",
    author_email="email@example.com",
    description="Implementasi konsep Himpunan untuk Matematika Diskrit (tanpa menggunakan set bawaan).",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/himpunanmatdis",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
