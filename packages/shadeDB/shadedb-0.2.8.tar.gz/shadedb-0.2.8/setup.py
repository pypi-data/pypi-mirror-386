from setuptools import setup, find_packages

setup(
    name="shadeDB",
    version="0.2.8",
    description="A lightweight, class-oriented database server with a CLI wrapper for instant querying on any device.Store, update, fetch, and remove structured data with a single command. Designed for speed and simplicity, it’s perfect for embedded systems, mobile devices, developer tools, and quick local services.",
    author="Shade",
    author_email="adesolasherifdeen3@gmail.com",
    entry_points={
        "console_scripts": [
          "shadeDB=shadeDB.cli:main",
          "scdb=shadeDB.cli:main"
        ]
    },
    include_package_data=True,
    python_requires='>=3.8',
    license="MIT",
    classifiers=[
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "Topic :: Database :: Database Engines/Servers",
    ],
    project_urls={
        "GitHub": "https://github.com/harkerbyte",
        "Facebook": "https://facebook.com/harkerbyte",
        "Whatsapp" : "https://whatsapp.com/channel/0029Vb5f98Z90x2p6S1rhT0S",
        "Youtube" : "https://youtube.com/@harkerbyte",
        "Instagram": "https://instagram.com/harkerbyte",
        "X" : "https://x.com/shade_ofx"
    },
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)