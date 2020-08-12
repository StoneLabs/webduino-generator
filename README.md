# Webduino Generator
Python program to automatically create arduino webserver from folder.
Supports basically all file types. For example: html, js, css, images, and arbitrary binaries.
Also supports coding cpp functions inside the website files (see input/*.cpp) for example.

# Usage

```
$ git clone https://github.com/StoneLabs/webduino-generator
$ cd webduino-generator/
$ pip install .
$ webduino-generator input
$ arduino output/main/main.ino

Or use arduino-cli to compile and upload directly from the shell (linux only)
$ ./uploader.sh
```

### Note
Project is WIP. Tested on Windows (PS) and Linux.
