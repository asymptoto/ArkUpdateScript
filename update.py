#!/usr/bin/env python3

from distutils.log import debug
import logging
import os
import binascii
import platform
import struct
import arkkit
import subprocess
import requests
import re
import shutil
import sys

def create_mod_file(path, name, id):
    with open(os.path.join(path, 'mod.info'), 'rb') as f_mod:
        modfile = binascii.hexlify(f_mod.read())
    with open(os.path.join(path, 'modmeta.info'), 'rb') as meta:
        metafile = binascii.hexlify(meta.read())

    out = binascii.hexlify(struct.pack('<I', id))
    out += b'00000000'
    out += binascii.hexlify(struct.pack('<I', len(name)+1))
    out += binascii.hexlify(str.encode(name))
    out += b'00'
    out += binascii.hexlify(struct.pack('<I', 1 + len('../../../ShooterGame/Content/Mods/') + len(str(id))))
    out += binascii.hexlify(str.encode('../../../ShooterGame/Content/Mods/'))
    out += binascii.hexlify(str.encode(str(id)))
    out += modfile[modfile.index(b'00010000'):-16]
    out += b'33FF22FF0200000001'
    out += metafile

    with open(os.path.join(path, '{}.mod'.format(mod)), 'wb') as f:
        f.write(binascii.unhexlify(out))


def unpack(path):
    for curdir, subdirs, files in os.walk(path):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext == '.z':
                src = os.path.join(curdir, file)
                dst = os.path.join(curdir, name).replace('WindowsNoEditor'+os.sep, '')
                uncompressed = os.path.join(curdir, file + '.uncompressed_size')
                arkkit.unpack(src, dst)
                os.remove(src)
                if os.path.isfile(uncompressed):
                    os.remove(uncompressed)


update_game = False

if len(sys.argv) > 1:
    if sys.argv[1] == '--update_game':
        update_game = True
        print('Doing full game update')
    else:
        print('Usage: \n\t./update.py [--update_game]')
        exit(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('settings.ini', 'r') as f:
    opts = dict()
    for line in f:
        opt, arg = line.split('=')
        opts[opt] = arg.strip().replace('~', os.environ.get('HOME'))

if 'steam_dir' in opts:
    print('Using steam directory {}'.format(opts["steam_dir"]))
    steamcmd_path = os.path.join(opts['steam_dir'], 'steamcmd.sh')
else:
    print('You need to specify the steam directory in settings.ini')

if os.path.exists(steamcmd_path) and os.path.isfile(steamcmd_path):
    print('Found steamcmd.sh in {}'.format(opts["steam_dir"]))
else:
    print('Could not find steamcmd.sh in {}'.format(opts["steam_dir"]))
    exit(1)

if 'ark_dir' in opts and opts['ark_dir'] != '':
    print('Using ark directory {}'.format(opts["ark_dir"]))
    ark_dir = opts['ark_dir']
else:
    print('You need to specify the ark directory in settings.ini')
    exit(1)

mods = []
if os.path.exists(ark_dir):
    if os.path.isdir(ark_dir):
        game_settings = os.path.join(ark_dir, 'ShooterGame', 'Saved', 'Config', '{}Server'.format(platform.system()), 'GameUserSettings.ini')
        if os.path.exists(game_settings):
            with open(game_settings, 'r') as f:
                for line in f:
                    if line.startswith('ActiveMods='):
                        mods = line.strip().replace('ActiveMods=', '').split(',')
                        print('Installing {} mods from config: {}'.format(len(mods), ', '.join(mods)))
                        break
                else:
                    print('Could not find ActiveMods setting in GameUserSettings.ini\nSkipiping mod installation')
        else:
            print('Could not find GameUserSettings.ini\nSkipping mod installation')
    else:
        print('{} exists but is not a directory'.format(ark_dir))
        exit(1)
else:
    print('Directory {} does not exist, trying to create it'.format(ark_dir))
    try:
        os.mkdir(ark_dir)
        print('Successfully created directory {}'.format(ark_dir))
        print('Forcing ark server installation')
        update_game = True
    except Exception as ex:
        print('An error occoured while trying to create the directory:\n{}'.format(ex))
        exit(1)

cmd = ""
if update_game:
    cmd=[steamcmd_path, '+force_install_dir {}'.format(os.path.abspath(ark_dir)), '+login anonymous', '+app_update 376030 validate'] + list('+workshop_download_item 346110 {}'.format(mod) for mod in mods) + ['+quit']
else:
    if len(mods) > 0:
        cmd=[steamcmd_path, '+login anonymous'] + list('+workshop_download_item 346110 {}'.format(mod) for mod in mods) + ['+quit']
    else:
        print('Nothing to update')
        exit(0)

subprocess.check_call(cmd)

workshop_dir = os.path.join(os.path.abspath(os.environ.get('HOME')), 'steam', 'steamapps', 'workshop', 'content', '346110')
mod_dir = os.path.join(ark_dir, 'ShooterGame', 'Content', 'Mods')

logging.disable(logging.INFO)

for mod in mods:
    path_in_mods = os.path.join(mod_dir, mod)
    path_in_workshop = os.path.join(workshop_dir, mod)
    mod_file_path_workshop = os.path.join(path_in_workshop, '{}.mod'.format(mod))
    mod_file_path_mods = os.path.join(mod_dir, '{}.mod'.format(mod))
    def install_mod():
        response = requests.get('https://steamcommunity.com/sharedfiles/filedetails/?id={}'.format(mod))
        title = re.search(r"<title>Steam Workshop::(?P<Title>.*)<\/title>", response.content.decode('UTF-8')).group('Title')
        print('Installing {}'.format(title))
        create_mod_file(os.path.join(workshop_dir, mod), title, int(mod))
        shutil.move(mod_file_path_workshop, mod_dir)
        shutil.copytree(path_in_workshop, path_in_mods)
        if os.path.exists(os.path.join(path_in_mods, 'LinuxNoEditor')):
            shutil.rmtree(os.path.join(path_in_mods, 'LinuxNoEditor'))
        print('Unpacking {}'.format(title))
        unpack(path_in_mods)
        shutil.rmtree(os.path.join(path_in_mods, 'WindowsNoEditor'))
        print('Finished installing {}'.format(title))
    if os.path.exists(path_in_mods):
        if os.path.getmtime(path_in_mods) < os.path.getmtime(path_in_workshop):
            shutil.rmtree(path_in_mods)
            os.remove(mod_file_path_mods)
            install_mod()
        else:
            print('Skipped installation of {}'.format(mod))
    else:
        install_mod()
    
print('Server files successully updated!')