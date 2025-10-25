from setuptools import setup, find_packages
from pathlib import Path

NAME = "tigerodm"  # PyPI normalizes to lowercase
VERSION = "0.0.0a1"

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name=NAME,
    version=VERSION,
    description="Placeholder package to reserve the 'tigerodm' name. Official releases coming soon.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TigerODM authors",
    python_requires=">=3.8",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    keywords=["orange", "data mining", "ai", "rag", "llm", "tigerodm"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Build Tools",
    ],
    url="https://example.com/tigerodm",
    project_urls={
        "Homepage": "https://example.com/tigerodm",
        "Source": "https://example.com/tigerodm/source",
        "Tracker": "https://example.com/tigerodm/issues",
    },
    entry_points={
        "console_scripts": [
            "tigerodm=tigerodm.__main__:main",
        ]
    },
    # No install_requires for placeholder
    install_requires=[],
    zip_safe=False,
)
