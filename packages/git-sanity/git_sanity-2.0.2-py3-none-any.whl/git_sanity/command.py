import logging
import os
from git_sanity import __config_root_dir__
from git_sanity import __config_file_name__
from git_sanity.utils import run
from git_sanity.utils import get_config_dir
from git_sanity.utils import load_user_config
from git_sanity.utils import get_user_config

def list_commands():
    logging.info("user-defined commands:")
    config_root_dir = os.path.join(get_config_dir(), __config_root_dir__)
    for command in get_user_config(load_user_config(), "commands"):
        print(command)


def execute_command(command_name):
    config_root_dir = os.path.join(get_config_dir(), __config_root_dir__)
    for command in get_user_config(load_user_config(), "commands"):
        if command_name in command:
            run(command[command_name], workspace=config_root_dir)
            break
    else:
        logging.error("the command `{}` is not defined in {}:commands.".format(command_name, os.path.join(config_root_dir, __config_file_name__)))
        exit(1)


def command_impl(args):
    if args.list:
        list_commands()
    else:
        execute_command(args.command_name)
