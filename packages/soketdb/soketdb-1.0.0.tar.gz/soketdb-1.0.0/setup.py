from setuptools import setup, find_packages

setup(
    name="soketdb",
    version="1.0.0",
    author="Alex Austin",
    author_email="benmap40@gmail.com",
    description=(
        "SoketDB — a zero-setup, AI-smart JSON database built for developers who value speed, simplicity, "
        "and offline capability. It enables instant data storage, natural language querying, and optional "
        "cloud-backed persistence — all in one self-contained system."
    ),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pythos-team/soketdb",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "huggingface_hub",
        "sqlparse",
        "requests",
        "redis",
        "dropbox",
        "boto3",
        "google-auth-oauthlib",
        "google-auth-httplib2",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
    ],
    keywords=[
        "database",
        "json",
        "sql",
        "ai",
        "nlp",
        "offline",
        "lightweight",
        "local-storage",
        "cloud-sync",
        "huggingface",
        "google-drive",
    ],
)