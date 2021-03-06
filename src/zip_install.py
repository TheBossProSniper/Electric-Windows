from logger import log_info
from Classes.Metadata import Metadata
from Classes.PortablePacket import PortablePacket
from timeit import default_timer as timer
from extension import write, write_debug
from colorama import Fore
from zip_utils import *
import os
import sys

home = os.path.expanduser('~')


def install_portable(packet: PortablePacket, metadata: Metadata):
    if find_existing_installation(f'{packet.extract_dir}@{packet.latest_version}'):
        log_info(
            f'Detected an existing installation of {packet.display_name}', metadata.logfile)
        write(
            f'Found Existing Installation Of {packet.display_name}', 'bright_yellow', metadata)
        continue_installation = confirm(
            f'Would you like to reinstall {packet.display_name}?')
        if not continue_installation:
            sys.exit()

    if packet.dependencies:
        log_info(
            f'Installing dependencies for {packet.display_name}', metadata.logfile)
        install_dependencies(packet, metadata)

    changes_environment = False
    shortcuts = packet.shortcuts
    extract_dir = packet.extract_dir
    write_debug(
        f'Downloading {packet.json_name}{packet.file_type} from {packet.url}', metadata)
    log_info(
        f'Downloading {packet.json_name}{packet.file_type} from {packet.url}', metadata.logfile)
    show_progress_bar = not metadata.silent and not metadata.no_progress

    if isinstance(packet.url, str):
        download(packet, packet.url, packet.file_type, rf'{home}\electric\\' + f'{packet.extract_dir}@{packet.latest_version}',
                 metadata, show_progress_bar=show_progress_bar, is_zip=True)

        if packet.checksum:
            verify_checksum(
                rf'{home}\electric\\' + f'{packet.extract_dir}@{packet.latest_version}{packet.file_type}', packet.checksum, metadata)

        unzip_dir = unzip_file(f'{packet.extract_dir}@{packet.latest_version}' +
                               packet.file_type, f'{extract_dir}@{packet.latest_version}', packet.file_type, metadata)

    elif isinstance(packet.url, list):
        for idx, url in enumerate(packet.url):
            if idx == 0:
                download(packet, url['url'], '.zip', rf'{home}\electric\\' + f'{packet.extract_dir}@{packet.latest_version}',
                         metadata, show_progress_bar=show_progress_bar, is_zip=True)
                unzip_dir = unzip_file(
                    f'{packet.extract_dir}@{packet.latest_version}' + '.zip', extract_dir, url['file-type'], metadata)

            else:
                write(
                    f'Downloading {url["file-name"]}{url["file-type"]}', 'cyan', metadata)
                download(packet, url['url'], url['file-type'],
                         rf'{home}\electric\extras\{packet.extract_dir}@{packet.latest_version}\\{url["file-name"]}', metadata, show_progress_bar=False, is_zip=False)

    if packet.pre_install:
        log_info('Executing pre install code', metadata.logfile)
        if packet.pre_install['type'] == 'powershell':
            packet.pre_install['code'] = [l.replace('<dir>', unzip_dir.replace(
                '\\\\', '\\')) for l in packet.pre_install['code']]

            packet.pre_install['code'] = [l.replace('<extras>', rf'{home}\electric\extras\{packet.extract_dir}@{packet.latest_version}'.replace(
                '\\\\', '\\')) for l in packet.pre_install['code']]

            if not os.path.isdir(rf'{home}\electric\temp\Scripts'):
                try:
                    os.mkdir(rf'{home}\electric\temp')
                except:
                    # temp directory already exists
                    pass

                os.mkdir(rf'{home}\electric\temp\Scripts')

            with open(rf'{home}\electric\temp\Scripts\temp.ps1', 'w+') as f:
                for line in packet.pre_install['code']:
                    f.write(f'\n{line}')
            os.system(
                rf'powershell -executionpolicy bypass -File {home}\electric\temp\Scripts\temp.ps1')
            write('Successfully Executed Pre-Install Code',
                  'bright_green', metadata)

        if packet.pre_install['type'] in ['bat', 'cmd']:
            packet.pre_install['code'] = [l.replace('<dir>', unzip_dir.replace(
                '\\\\', '\\')) for l in packet.pre_install['code']]

            packet.pre_install['code'] = [l.replace('<extras>', rf'{home}\electric\extras\{packet.extract_dir}@{packet.latest_version}'.replace(
                '\\\\', '\\')) for l in packet.pre_install['code']]

            if not os.path.isdir(rf'{home}\electric\temp\Scripts'):
                try:
                    os.mkdir(rf'{home}\electric\temp')
                except:
                    # temp directory already exists
                    pass

                os.mkdir(rf'{home}\electric\temp\Scripts')

            with open(rf'{home}\electric\temp\Scripts\temp.bat', 'w+') as f:
                for line in packet.pre_install['code']:
                    f.write(f'\n{line}')
            os.system(
                rf'{home}\electric\temp\Scripts\temp.bat')
            write('Successfully Executed Pre-Install Code',
                  'bright_green', metadata)

        if packet.pre_install['type'] == 'python':
            code = ''''''.join(l + '\n' for l in packet.pre_install['code'])

            exec(code)

    if packet.chdir:
        dir = packet.chdir.replace('<version>', packet.latest_version)
        unzip_dir += f'\\{dir}\\'

    if packet.bin and isinstance(packet.bin, list):
        for binary in packet.bin:
            if isinstance(binary, str):
                shim_dir = unzip_dir
                shim = ''.join(binary.split('.')[:-1])
                shim_ext = binary.split('.')[-1]
                if '\\' in binary:
                    shim = ''.join(binary.split('\\')[-1])
                    shim = ''.join(shim.split('.')[:-1])
                    shim_ext = binary.split('.')[-1]
                    shim_dir += ' '.join(binary.split('\\')
                                         [:-1]).replace(' ', '\\')

                shim = shim.replace('<version>', packet.latest_version)
                shim_dir = shim_dir.replace('<version>', packet.latest_version)

                start = timer()
                generate_shim(f'{shim_dir}', shim, shim_ext)
                end = timer()
                write(
                    f'{Fore.LIGHTCYAN_EX}Successfully Generated {shim} Shim In {round(end - start, 5)} seconds{Fore.RESET}', 'white', metadata)
            else:
                val = binary['file-name']
                shim_dir = unzip_dir
                shim = ''.join(val.split('.')[:-1])
                shim_ext = val.split('.')[-1]

                if '\\' in val:
                    shim = ''.join(val.split('\\')[-1])
                    shim = ''.join(shim.split('.')[:-1])
                    shim_ext = val.split('.')[-1]
                    shim_dir += ' '.join(val.split('\\')
                                         [:-1]).replace(' ', '\\')

                shim = shim.replace('<version>', packet.latest_version)
                shim_dir = shim_dir.replace('<version>', packet.latest_version)
                val = val.replace('<version>', packet.latest_version)

                start = timer()
                generate_shim(f'{shim_dir}', val.split(
                    '\\')[-1].split('.')[0], shim_ext, overridefilename=binary['shim-name'])
                end = timer()
                write(
                    f'{Fore.LIGHTCYAN_EX}Successfully Generated {binary["shim-name"]} Shim In {round(end - start, 5)} seconds{Fore.RESET}', 'white', metadata)

    if shortcuts:
        for shortcut in shortcuts:
            shortcut_name = shortcut['shortcut-name']
            file_name = shortcut['file-name']
            log_info(
                f'Creating shortcuts for {packet.display_name}', metadata.logfile)
            create_start_menu_shortcut(unzip_dir, file_name, shortcut_name)

    if packet.set_env:
        if isinstance(packet.set_env, list):
            changes_environment = True
            for obj in packet.set_env:
                log_info(
                    f'Setting environment variables for {packet.display_name}', metadata.logfile)
                write(
                    f'Setting Environment Variable {obj["name"]}', 'bright_green', metadata)
                set_environment_variable(obj['name'], obj['value'].replace(
                    '<install-directory>', unzip_dir).replace('\\\\', '\\'))
        else:
            changes_environment = True

            log_info(
                f'Setting environment variables for {packet.display_name}', metadata.logfile)
            write(
                f'Setting Environment Variable {packet.set_env["name"]}', 'bright_green', metadata)

            set_environment_variable(packet.set_env['name'], packet.set_env['value'].replace(
                '<install-directory>', unzip_dir).replace('\\\\', '\\'))

    if changes_environment:
        log_info(
            'Detected change in PATH variable. Requesting `refreshenv` to be run', metadata.logfile)
        write(
            f'{Fore.LIGHTGREEN_EX}The PATH environment variable has changed. Run `refreshenv` to refresh your environment variables.{Fore.RESET}', 'white', metadata)

    if packet.post_install:
        log_info('Executing post installation code', metadata.logfile)

        for line in packet.post_install:
            exec(line.replace('<install-directory>', unzip_dir).replace('<extras>',
                 rf'{home}\electric\extras\{packet.extract_dir}@{packet.latest_version}'))

    if packet.install_notes:
        log_info('Found Installation Notes, Writing To Console.',
                 metadata.logfile)
        display_notes(packet, unzip_dir, metadata)

    write(
        f'Successfully Installed {packet.display_name}', 'bright_magenta', metadata)
