from setuptools import setup, find_packages

setup(
    name="pqbit",
    version="1.4.0",
    author="Kito Hamachi",
    author_email="kitohamachi@hotmail.com",
    description="Post-quantum mesh VPN library with offline wallet generation via Falcon-1024, Dilithium5 and SHA3-512",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kitohamachi/pqbit",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "pypqc>=0.0.6.2",
        "pyshark>=0.6",
        "scapy>=2.5.0",
        "wg-meshconf>=2.5.1",
        "wireguard>=1.0.2",
        "wireguard4netns>=0.1.6",
        "pytest>=8.4.2",
        "PyYAML>=6.0",
        "PySocks>=1.7.1",
        "qrcode[pil]>=7.4.2",
        "cffi>=2.0.0",
        "pycparser>=2.23",
        "logging4>=0.0.2"
    ],
    entry_points={
        "console_scripts": [
            "pqbit = pqbit.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
