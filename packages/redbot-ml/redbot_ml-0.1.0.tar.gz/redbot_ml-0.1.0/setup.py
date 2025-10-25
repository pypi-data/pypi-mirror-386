from setuptools import setup, find_packages

setup(
    name="redbot_ml",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "opencv-python",
        "torch",
        "torchvision",
        "Pillow",
        "scikit-learn",
        "scikit-image",
        "mahotas",
        "albumentations",
        "matplotlib",
        "joblib"
    ],
    description="Redbot ML module for image processing and anomaly detection",
    author="Your Name",
    python_requires=">=3.8",
)
