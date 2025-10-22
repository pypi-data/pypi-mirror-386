from setuptools import setup, find_packages

setup(
    name="StegoImageX",
    version="0.0.1",
    author="ATHALLAH RAJENDRA PUTRA JUNIARTO",
    author_email="athallahwork50@gmail.com",
    description="StegoImageX v10.0 — Advanced AES-encrypted, Hash-verified, Dynamic-Position, Compressed Steganography Library.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Athallah1234/StegoImageX",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Pillow>=9.0.0",
        "pycryptodome>=3.10.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires=">=3.7",
)
