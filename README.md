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
$ wgen open

Or compile and upload directly (requires arduino-cli to be installed)
$ wgen compile
$ wgen upload
```

# Projects
Aside from build a random folder you can create a project. By default a simple hello world program will be created.
```
$ wgen init
$ wgen build
$ wgen open
```

# Supported devices?
At the moment the templates only support WiFiNina based connections. Tested only on Arduino nano 33 iot. Should be fairly easy to adapt the templates for ethernet based devices though.


```
$ wgen init
$ nano templates/main.ino
```

# How to place code in loop() or init()?
The inputs files do not support loop() or init() code (as you might have seen from the example in this repository). However it is quite trivial to add code to loop() or init(). To do this simply edit the template generated with your project.

```
$ wgen init
$ nano templates/main.ino
$ wgen build

And compile and upload directly (requires arduino-cli to be installed)
$ wgen compile
$ wgen upload
```

# Windows support?
Aside from `wgen compile` and `wgen upload` all commands should work regardless of your operating system. Even compile and upload should work if you manage to install `arduino-cli` on windows. However, this is not tested.

# Other gotchas?
I highly recommend not using includes inside input .cpp files. The cpp input files are packed in a namespace during the build. Importing inside the namespace might cause large sketches. The same goes for global variables shared between input files. However, it is quite simple to work around this. Simply edit the template as described above.

# Documentation?
Not yet. Might use github wiki at some point.

### Note
Project is WIP.