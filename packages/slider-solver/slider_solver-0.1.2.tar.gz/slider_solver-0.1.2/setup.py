from setuptools import setup, find_packages

setup(
    name="slider_solver",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "Pillow"
    ],
    python_requires=">=3.8",
    author="MiChen",
    author_email="rmcyyds@q.com",
    description="Universal Slider CAPTCHA Gap Detection",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/slider_solver",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
