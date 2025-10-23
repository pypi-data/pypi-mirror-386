from setuptools import setup, find_packages

setup(
    name="gestor_notas",
    version="1.0.1",
    author="Aurisssss",
    author_email="aurisssss@protonmail.com",
    description="Un gestor de notas en consola con persistencia mediante Pickle.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aurisssssdev/gestor_notas",
    project_urls={
        "PyPI": "https://pypi.org/project/gestor-notas/",
        "Bug Tracker": "https://github.com/aurisssss/gestor_notas/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
)

