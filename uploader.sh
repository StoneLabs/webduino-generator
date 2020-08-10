echo Listing available devices:
arduino-cli board list
echo -n "Please enter port: "
read __WEBDUINO_PORT 

echo -n "Please enter FQBN for target board: "
read __WEBDUINO_FQBN

echo -e "\nCompiling..."
arduino-cli compile --fqbn $__WEBDUINO_FQBN output/main

echo -e "\nUploading..."
echo "sudo arduino-cli upload -p $__WEBDUINO_PORT --fqbn $__WEBDUINO_FQBN output/main"
sudo arduino-cli upload -p $__WEBDUINO_PORT --fqbn $__WEBDUINO_FQBN output/main