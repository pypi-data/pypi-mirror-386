"""
Smart Packet Sniffer Setup Script
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-packet-sniffer",
    version="1.0.0",
    author="Harsh Gupta",
    author_email="tech.savvy.harsh@gmail.com",
    description="Advanced network security monitoring with real-time threat detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshu07-collab/smart-packet-sniffer",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "scapy>=2.5.0",
        "flask>=3.0.0",
        "flask-socketio>=5.3.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "plotly>=5.17.0",
        "scikit-learn>=1.3.0",
        "psutil>=5.9.0",
        "requests>=2.31.0",
        "python-dateutil>=2.8.2"
    ],
    entry_points={
        "console_scripts": [
            "packet-sniffer=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/**/*"],
    },
)