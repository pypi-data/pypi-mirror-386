"""
Setup script for OrbitalsAI Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="orbitalsai",
    version="1.0.0",
    author="OrbitalsAI",
    author_email="support@orbitalsai.com",
    description="A simple and powerful Python SDK for the OrbitalsAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/orbitalsai/orbitalsai-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "aiohttp>=3.8.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    keywords="ai, transcription, audio, speech, african languages, srt, subtitles",
    project_urls={
        "Bug Reports": "https://github.com/orbitalsai/orbitalsai-python-sdk/issues",
        "Source": "https://github.com/orbitalsai/orbitalsai-python-sdk",
        "Documentation": "https://docs.orbitalsai.com",
    },
)
