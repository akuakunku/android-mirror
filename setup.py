from setuptools import setup, find_packages
import os
import sys

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

# Tambahkan opsi untuk build executable
setup(
    name="android-mirror",
    version="1.0.0",
    author="Chesko",
    author_email="chesko@example.com",
    description="Android screen mirroring tool similar to scrcpy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akuakunku/android-mirror",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Capture",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "android-mirror=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "android_mirror": ["resources/**/*"],
    },
    # Opsi untuk PyInstaller
    options={
        'build_exe': {
            'packages': ['os', 'sys', 'subprocess', 'threading', 'time', 
                        'PyQt5', 'cv2', 'numpy', 'pynput', 'yaml', 'watchdog'],
            'include_files': [
                ('scrcpy', 'scrcpy'),
                ('config.yaml', 'config.yaml'),
            ]
        }
    }
)