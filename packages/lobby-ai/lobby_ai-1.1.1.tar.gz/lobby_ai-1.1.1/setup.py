

from setuptools import find_packages, setup


# Read README for long description
def read_readme():
    with open("README.md", encoding="utf-8") as fh:
        return fh.read()


setup(
    name="lobby-ai",
    version="1.1.1",
    author="Franco",
    author_email="franco@lobby.ai",
    description="🏢 LOBBY - AI concierge service that multiplies your existing CLI tools",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://lobby.directory",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "httpx>=0.24.0",
        "mcp>=1.0.0",
        "pydantic>=2.0.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "billing": ["stripe>=5.0.0", "flask>=2.3.0", "flask-cors>=4.0.0"],
        "interactive": [
            "InquirerPy>=0.3.4",
            "questionary>=2.0.0",
            "prompt-toolkit>=3.0.0,<4.0.0",
        ],
        "all": [
            "stripe>=5.0.0",
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "InquirerPy>=0.3.4",
            "questionary>=2.0.0",
            "prompt-toolkit>=3.0.0,<4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lobby=lobby.cli:main",
            "lobby-mcp=lobby.mcp_server:main_entry",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, cli, orchestration, mcp, claude, gemini, cursor, concierge",
)
