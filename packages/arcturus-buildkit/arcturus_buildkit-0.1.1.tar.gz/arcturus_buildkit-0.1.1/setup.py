from setuptools import setup, find_packages

setup(
    name="arcturus-buildkit",
    version="0.1.1",
    author="FlameZI0",
    author_email="abdulrehmanshoaib136@gmail.com",
    description="Lightweight NLP and supervised ML chatbot framework in pure Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    include_package_data=True,  
    install_requires=[],   
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
