# gen-rpi-image
Generates a minimally working image from a stock one (I've been using Raspbian Jessite lite).
- Enables SSH on boot
- Sets hostname
- Disables SSH password
- Adds default WiFi credentials
- Adds SSH key

## Usage
```
usage: gen-rpi-image.py [-h] -n N -k K -s S -p P -b B [--write WRITE]

optional arguments:
  -h, --help     show this help message and exit
  -n N           Hostname
  -k K           Path to public key
  -s S           WiFi SSID
  -p P           WiFi password
  -b B           Path to base image
  --write WRITE  Write to device
```
