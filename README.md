<img alt="GitHub issues" src="https://img.shields.io/github/issues/StoneLabs/webduino-generator?style=flat-square"> <img alt="GitHub watchers" src="https://img.shields.io/github/watchers/StoneLabs/webduino-generator?style=flat-square"> <img alt="GitHub stars" src="https://img.shields.io/github/stars/StoneLabs/webduino-generator?style=flat-square"> <img alt="PyPI" src="https://img.shields.io/pypi/v/webduino-generator?style=flat-square"> <img alt="Maintenance" src="https://img.shields.io/maintenance/yes/2020?style=flat-square">

<img src="https://www.distrelec.de/Web/WebShopImages/landscape_large/3-/01/Arduino-ABX00027-30150883-01.jpg" align="right" width="200" />

# Webduino Generator
Python program to automatically create arduino webserver from folder.
Supports basically all file types. For example: html, js, css, images, and arbitrary binaries.
Also supports coding cpp functions inside the website files (see input/*.cpp) for example.

# Installation
```
$ sudo pip install webduino-generator
```

# Usage
The following will build the demo website included in this repository.
```
$ git clone https://github.com/StoneLabs/webduino-generator
$ cd webduino-generator/
$ wgen generate input
$ arduino main/main.ino

Or use arduino-cli to compile and upload directly from the shell (linux only)
$ ./uploader.sh
```

# Projects
Aside from build a random folder you can create a project. By default a simple hello world program will be created.
```
$ wgen init
$ wgen build
$ arduino output/main/main.ino
```

### Note
Project is WIP. Tested on Windows (PS) and Linux.
