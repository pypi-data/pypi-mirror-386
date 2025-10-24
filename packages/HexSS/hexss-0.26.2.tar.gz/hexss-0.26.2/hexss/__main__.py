import argparse
import os
import importlib

import hexss
from hexss.constants.terminal_color import *
from hexss import hexss_dir, json_load, json_update
from hexss.config import list_config_files


def show_config(data, keys):
    """Display configuration values based on the keys provided."""
    try:
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                print(f"Key '{'.'.join(keys)}' not found in configuration.")
                return

        if isinstance(data, dict):
            max_key_length = min(max((len(k) for k in data.keys()), default=0) + 1, 15)
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    color = BLUE
                elif isinstance(v, (list, dict)):
                    color = CYAN
                else:
                    color = DARK_GREEN

                value_str = f"'{v}'" if isinstance(v, str) else v
                print(f"{k:{max_key_length}}: {color}{value_str}{END}")

                # for python 3.12
                # print(f"{k:{max_key_length}}: {
                # BLUE if isinstance(v, (int, float)) else
                # CYAN if isinstance(v, (list, dict)) else
                # DARK_GREEN
                # }{f"'{v}'" if isinstance(v, str) else v}{END}")

        else:
            print(data)
    except Exception as e:
        print(f"Error while displaying configuration: {e}")


def update_config(file_name, keys, new_value):
    """Update a JSON configuration file with a new value for the given keys."""
    try:
        file_path = hexss_dir / 'config' / f'{file_name}.json'
        config_data = json_load(file_path)
        data = config_data.get(file_name, config_data)

        # Navigate nested keys and create missing dictionaries
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set new value
        current[keys[-1]] = new_value

        # Persist changes
        json_update(file_path, {file_name: data})

        # Feedback
        if new_value is None:
            val_color = ORANGE
        elif isinstance(new_value, (int, float)):
            val_color = BLUE
        elif isinstance(new_value, (list, dict)):
            val_color = CYAN
        else:
            val_color = DARK_GREEN

        # for python 3.12
        # val_color = (
        #     ORANGE if new_value is None else
        #     BLUE if isinstance(new_value, (int, float)) else
        #     CYAN if isinstance(new_value, (list, dict)) else
        #     DARK_GREEN
        # )
        disp_val = new_value if isinstance(new_value, (int, float, type(None))) else f"'{new_value}'"
        print(f"Updated {'.'.join(keys)} to {val_color}{disp_val}{END}")
    except Exception as e:
        print(f"Error while updating configuration: {e}")


def run_config(args):
    """Handler for the 'config' sub-command."""
    key_parts = (args.key or '').split('.')
    file_name, *keys = key_parts

    if file_name == '':
        list_config = list_config_files()
        if not list_config:
            print('No configuration file found.')
            return

        print('Choose a configuration file:')
        for i, config_file in enumerate(list_config, start=1):
            print(f'({i}) {config_file}')

        try:
            choice = int(input(">> ").strip())
            if choice == 0:
                print("Exiting.")
                return
            elif choice <= len(list_config):
                file_name = list_config[choice - 1]
            else:
                print("Invalid choice. Exiting.")
                return
        except:
            return

    cfg_path = hexss_dir / 'config' / f'{file_name}.json'
    try:
        raw = json_load(cfg_path)
        cfg = raw.get(file_name, raw)
    except FileNotFoundError:
        print(f"Configuration file for '{file_name}' not found.")
        return

    if args.value is None:
        show_config(cfg, keys)
    else:
        if args.text:
            new_val = args.value
        else:
            try:
                new_val = eval(args.value)
            except Exception:
                new_val = args.value
        update_config(file_name, keys, new_val)


def run_install(args):
    """Handler for 'install' command: install one or more packages."""
    mod = importlib.import_module('hexss.python')
    names = args.name or ['hexss']
    mod.install(*names)


def run_upgrade(args):
    """Handler for 'upgrade' command: upgrade one or more packages."""
    mod = importlib.import_module('hexss.python')
    names = args.name or ['hexss']
    mod.upgrade(*names)


def print_env():
    """Print all environment variables."""
    for k, v in os.environ.items():
        print(f'{k:25}: {v}')


def get_details():
    print('--general--')
    print('hostname         :', hexss.hostname)
    print('username         :', hexss.username)
    print('system           :', hexss.system)
    print('proxies          :', hexss.proxies)
    print()
    print('--path--')
    print('hexss dir        :', hexss_dir)
    print('venv             :', hexss.path.get_venv_dir())
    print('python exec      :', hexss.path.get_python_path())
    print('main python exec :', hexss.path.get_main_python_path())
    print('working dir      :', hexss.path.get_current_working_dir())
    print('script dir       :', hexss.path.get_script_dir())


def show_menu():
    options = [
        'camera_server',
        'file_manager_server',

        'upgrade',
        'config',
        'set_proxy_env',
        'unset_proxy_env',

        'details'
    ]
    print("Choose an option:")
    for i, option in enumerate(options, 1):
        print(f"({i:{int(len(options) / 10) + 1}}) {option}")

    try:
        choice = input(">> ").strip()
        choice = int(choice)
        if choice == 0:
            print("Exiting.")
            return

        elif choice <= len(options):
            action = options[choice - 1]
            main_args = [action]

            import sys
            sys.argv = [sys.argv[0]] + main_args
            main()
        else:
            print("Invalid choice. Exiting.")
    except:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog='hexss',
        usage='hexss [-h] [-v] [-u]'
    )
    parser.add_argument(
        '-v', '-V', '--version',
        action='version',
        version=f'%(prog)s {hexss.__version__}, {(hexss.path.get_main_python_path())} {hexss.python_version}',
    )
    parser.add_argument(
        '-u', '-U', '--upgrade',
        action='store_true',
        help='upgrade hexss (same as: hexss upgrade)'
    )

    subparsers = parser.add_subparsers(
        title='positional arguments',
        dest='action',
        required=False,
        metavar=''  # hide the choice list placeholder in help
    )

    # config
    cfg = subparsers.add_parser('config', help='set or show configuration')
    cfg.add_argument('key', nargs='?', help="Config key, e.g. 'proxies' or 'proxies.http'")
    cfg.add_argument('value', nargs='?', help='New value for the key')
    cfg.add_argument('-T', '--text', action='store_true', help='Interpret value as text')
    cfg.set_defaults(func=run_config)

    # camera_server
    cs = subparsers.add_parser(
        'camera_server',
        aliases=['camera-server'],
        help='run the camera server'
    )
    cs.set_defaults(func=lambda args: importlib.import_module('hexss.server.camera_server').run())

    # file_manager_server
    fm = subparsers.add_parser(
        'file_manager_server',
        aliases=['file-manager-server'],
        help='run the file manager server'
    )
    fm.set_defaults(func=lambda args: importlib.import_module('hexss.server.file_manager_server').run())

    # install
    inst = subparsers.add_parser('install', help='install one or more packages')
    inst.add_argument('name', nargs='*', help='package name(s) to install, e.g. numpy')
    inst.set_defaults(func=run_install)

    # upgrade
    upg = subparsers.add_parser('upgrade', help='upgrade one or more packages')
    upg.add_argument('name', nargs='*', help='package name(s) to upgrade, e.g. numpy')
    upg.set_defaults(func=run_upgrade)

    # environ
    env = subparsers.add_parser('environ', aliases=['env'], help='show environment variables')
    env.set_defaults(func=lambda args: print_env())

    # set_proxy_env
    sp_env = subparsers.add_parser('set_proxy_env', help='print commands to set proxy env vars')
    sp_env.set_defaults(func=lambda args: importlib.import_module('hexss.env').set_proxy(persistent=True))
    unsp_env = subparsers.add_parser('unset_proxy_env', help='print commands to unset proxy env vars')
    unsp_env.set_defaults(func=lambda args: importlib.import_module('hexss.env').unset_proxy(persistent=True))

    # hostname
    hn = subparsers.add_parser('hostname', help='get hostname')
    hn.set_defaults(func=lambda args: print(hexss.hostname))

    # username
    un = subparsers.add_parser('username', help='get username')
    un.set_defaults(func=lambda args: print(hexss.username))

    # proxy
    pr = subparsers.add_parser('proxy', help='get proxy settings')
    pr.set_defaults(func=lambda args: print(hexss.proxies))

    # system
    sy = subparsers.add_parser('system', help='get system')
    sy.set_defaults(func=lambda args: print(hexss.system))

    # details
    gc = subparsers.add_parser('details', help='print hexss details')
    gc.set_defaults(func=lambda args: get_details())

    # Parse arguments
    args = parser.parse_args()

    # global -u / --upgrade flag (upgrade hexss)
    if args.upgrade and (args.action is None):
        importlib.import_module('hexss.python').upgrade('hexss')
        return

    # If no arguments are provided, display a menu
    if args.action is None:
        show_menu()
    else:
        args.func(args)


if __name__ == '__main__':
    main()
