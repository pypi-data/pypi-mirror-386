from setuptools import setup, find_packages

# قراءة محتوى README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="imad213insta",
    version="213.2",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "imad213insta = imad213insta.imad:main",
        ]
    },
    # إضافة وصف طويل من README.md
    long_description=long_description,
    long_description_content_type="text/markdown",
)