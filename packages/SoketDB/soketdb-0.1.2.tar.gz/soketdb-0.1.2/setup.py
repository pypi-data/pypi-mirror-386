from setuptools import setup, find_packages

setup(
    name="SoketDB",
    version="0.1.2",
    description=(
        "Soket Database — a fast, lightweight JSON-based database that eliminates the need for complex setup. It’s built for developers who want instant data storage, natural language querying, and secure local or cloud-backed persistence — all in one self-contained system."
    ),
    author="Alex Austin",
    author_email="benmap40@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "huggingface_hub",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)