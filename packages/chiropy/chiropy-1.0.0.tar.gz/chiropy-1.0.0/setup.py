import shutil
from setuptools import setup, find_packages

# long description
with open("README.md", "r") as f:
    long_description = f.read()
    
# install requires
with open("requirements.txt", "r") as f:
    install_requires = f.readlines()

# install openbebel-wheel
if shutil.which("obabel") is None:
    print("openbabel cli not found.")
    install_requires.append("openbabel-wheel == 3.1.1.22")
else:
    print("skip install openbabel-wheel == 3.1.1.22")

setup(
    name="chiropy",
    version="1.0.0",
    description="CHIROpy is a Gaussian binding tool for analyze chiroptical properties.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shota Inoue",
    author_email="inoue.shota@st.kitasato-u.ac.jp",
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
    python_requires=">=3.10",
)

