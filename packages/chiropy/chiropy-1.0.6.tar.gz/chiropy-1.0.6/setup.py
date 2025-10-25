from setuptools import setup, find_packages
import re

# version
def get_version():
    with open("chiropy/__init__.py") as f:
        match = re.search(r'__version__ = "([^"]+)"', f.read())
        if match:
            return match.group(1)
        raise RuntimeError("Version not found in chiropy/__init__.py")

# long description
with open("README.md", "r") as f:
    long_description = f.read()
    
# install requires
with open("requirements.txt", "r") as f:
    install_requires = f.readlines()

setup(
    name="chiropy",
    version=get_version(),
    description="CHIROpy is a Gaussian binding tool for analyze chiroptical properties.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shota Inoue",
    entry_points={
        "console_scripts": [
            "chiropy = chiropy.main:main",
        ],
    },
    url="https://github.com/s-inoue0108/chiropy",
    license="MIT",
    include_package_data=True,
    packages=find_packages(),
    install_requires=install_requires,
    python_requires=">= 3.10, < 3.12",
)

