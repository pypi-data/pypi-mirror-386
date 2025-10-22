"""
    Setup file for git-sanity.
"""

from setuptools import setup, find_packages

setup(
    name="git-sanity",
    version="2.0.0",
    package_dir={"":"src"},
    packages=find_packages(where="src"),
    license="MIT",
    description="Manage multiple git repos with sanity",
    long_description=None,
    long_description_content_type="text/markdown",
    url="https://github.com/yuqiaoyu/git-sanity",
    platforms=["linux", "osx", "win32"],
    keywords=["git", "manage multiple repositories", "cui", "command-line"],
    author="yuqiaoyu",
    author_email="yu_junqiang@qq.com",
    entry_points={"console_scripts": ["git-sanity = git_sanity.__main__:main"]},
    python_requires="~=3.10",
    install_requires=["argcomplete"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Terminals",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    include_package_data=True,
)
