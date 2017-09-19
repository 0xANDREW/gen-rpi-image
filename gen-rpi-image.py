#!/usr/bin/env python2

import argparse
import os
import shutil
import subprocess
import re
import tempfile
import time

WPA_TEXT = '''
network={
ssid="%s"
psk="%s"
}
'''

NETWORK_TEXT = '''
auto wlan0
allow-hotplug wlan0
iface wlan0 inet dhcp
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
iface default inet dhcp
'''

def file_replace(filename, pattern, repl):
    with open(filename) as f:
        contents = f.read()

    contents = contents.replace(pattern, repl)

    with open(filename, 'w') as f:
        f.write(contents)

def kpartx_wait(loop_devs):
    while not set(loop_devs) <= set(os.listdir('/dev/mapper')):
        time.sleep(0.5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', required=True, help='Hostname')
    parser.add_argument('-k', required=True, help='Path to public key')
    parser.add_argument('-s', required=True, help='WiFi SSID')
    parser.add_argument('-p', required=True, help='WiFi password')
    parser.add_argument('-b', required=True, help='Path to base image')
    parser.add_argument('--write', help='Write to device')

    args = parser.parse_args()

    work_dir = '%s/rpi-gen/%s' % (tempfile.gettempdir(), args.n)
    boot_path = '%s/boot' % work_dir
    mount_path = '%s/rootfs' % work_dir
    image_path = '%s/rpi.img' % work_dir

    print work_dir

    try:
        os.makedirs(mount_path)
    except:
        pass

    try:
        os.makedirs(boot_path)
    except:
        pass

    # Copy base image
    print 'Copying base image to %s' % image_path
    shutil.copyfile(args.b, image_path)

    # Mount image
    print 'Mounting partitions at %s' % work_dir
    output = subprocess.check_output('kpartx -av %s' % image_path, shell=True)
    loop_devs = re.findall('add map (\w+)', output)
    kpartx_wait(loop_devs)

    os.system('mount /dev/mapper/%s %s' % (loop_devs[1], mount_path))
    os.system('mount /dev/mapper/%s %s' % (loop_devs[0], boot_path))

    # Start SSH on boot
    print 'Enabling SSH on boot'
    open('%s/ssh' % boot_path, 'w').close()

    # Disable SSH password
    print 'Disabling SSH password'
    file_replace(
        '%s/etc/ssh/sshd_config' % mount_path, 
        '#PasswordAuthentication yes',
        'PasswordAuthentication no'
    )

    # Write hostname
    print 'Writing hostname (%s)' % args.n
    with open('%s/etc/hostname' % mount_path, 'w') as f:
        f.write(args.n)

    file_replace('%s/etc/hosts' % mount_path, 'raspberrypi', args.n)

    # Write WiFi creds
    print 'Writing WiFi creds (%s:%s)' % (args.s, args.p)
    with open('%s/etc/wpa_supplicant/wpa_supplicant.conf' % mount_path, 'a') as f:
        f.write(WPA_TEXT % (args.s, args.p))

    # Setup network
    print 'Setting up network interfaces'
    ifaces_path = '%s/etc/network/interfaces' % mount_path
    with open(ifaces_path, 'a') as f:
        f.write(NETWORK_TEXT)

    # Append SSH key
    print 'Writing SSH key'
    try:
        os.makedirs('%s/home/pi/.ssh' % mount_path)
    except:
        pass

    with open(args.k) as f:
        pub_key = f.read()

    ssh_path = '%s/home/pi/.ssh' % mount_path
    keys_path = '%s/authorized_keys' % ssh_path
    with open(keys_path, 'w') as f:
        f.write(pub_key)

    os.system('chmod 600 %s' % keys_path)
    os.system('chmod 700 %s' % ssh_path)
    os.system('chown -R 1000:1000 %s' % ssh_path)

    # Unmount image
    print 'Unmounting partitions at %s' % work_dir
    os.system('umount %s' % mount_path)
    os.system('umount %s' % boot_path)
    os.system('kpartx -dv %s' % image_path)

    if args.write:
        print 'Writing image to %s' % args.write
        os.system('dd if=%s of=%s bs=512K' % (image_path, args.write))

