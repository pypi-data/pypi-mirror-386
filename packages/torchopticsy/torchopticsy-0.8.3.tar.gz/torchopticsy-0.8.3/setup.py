import pathlib
import setuptools

setuptools.setup(
    name="torchopticsy",
    version="0.8.3",
    description="PyTorch-based optics caculation",
    long_description=pathlib.Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="YuningYe",
    author_email="1956860113@qq.com",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["torch", "opencv-python", "matplotlib"],
    include_package_data=True,
)
