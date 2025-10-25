from setuptools import setup, find_packages
import os

# Baca README dengan encoding UTF-8
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="streamlit_launcher",
    version="3.2.7",
    author="Dwi Bakti N Dev",
    author_email="dwibakti76@gmail.com",
    description="Analisis Date Scient Simple and Instant Streamlit Launcher AI Complite analisis Model",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/royhtml",
    project_urls={
        "Profile": "https://profiledwibaktindev.netlify.app/",
        "ich.io": "https://royhtml.itch.io/",
        "Facebook": "https://www.facebook.com/Royhtml",
        "Webtoons": "https://www.webtoons.com/id/canvas/mariadb-hari-senin/episode-4-coding-championship/viewer?title_no=1065164&episode_no=4",
        "Global komik": "https://globalcomix.com/read/dc7f0116-7187-49a0-a27b-62b6c81eb435/1?utm_medium=GCMobileReaderApp&utm_source=share-release&utm_campaign=Royy&utm_term=122186",
        "Portofolio": "https://portofolio-dwi-bakti-n-dev-liard.vercel.app/"
    },
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        "pillow>=8.0",
        "pyinstaller>=4.0",
        "pyqt5>=5.15",
    ],
    entry_points={
        "gui_scripts": [
            "streamlit_launcher=streamlit_launcher.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "webscan": ["*.ico", "*.png"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
