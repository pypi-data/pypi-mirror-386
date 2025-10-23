import argparse
import logging
import os
from git_sanity import __prog_name__
from git_sanity import __version__
from git_sanity.init import init_impl
from git_sanity.clone import clone_impl
from git_sanity.sync import sync_impl
from git_sanity.switch import switch_impl
from git_sanity.branch import branch_impl
from git_sanity.push import push_impl
from git_sanity.command import command_impl

def main():
    logging.info("New Run ==================================================")

    prog = argparse.ArgumentParser(
        prog=__prog_name__, formatter_class=argparse.RawTextHelpFormatter, description=__doc__
    )
    prog.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = prog.add_subparsers(
        title="sub-commands", help="additional help with sub-command -h"
    )
    prog_init = subparsers.add_parser("init", description="Initialize the projects", help="initialize the projects")
    prog_init.add_argument("-u", "--url", dest="url", help="the {} configuration repository".format(__prog_name__))
    prog_init.add_argument("-b", "--branch", dest="branch", help="branch to init")
    prog_init.add_argument("-d", "--directory", dest="directory", default=".", help="the path to init {} configuration repository".format(__prog_name__))
    prog_init.set_defaults(func=init_impl)

    prog_clone = subparsers.add_parser("clone", description="Clone repo(s)", help="clone repo(s)")
    prog_clone.add_argument("-g", "--group", dest="group", default="all", help="group to clone, default all")
    prog_clone.set_defaults(func=clone_impl)

    prog_sync = subparsers.add_parser("sync", description="Sync source project(s) ", help="sync source project(s)")
    prog_sync.add_argument("-g", "--group", dest="group", default="all", help="projects to sync, default all")
    prog_sync.set_defaults(func=sync_impl)

    prog_switch = subparsers.add_parser("switch", description="Switch branches", help="switch branches")
    prog_switch.add_argument("remote", nargs='?', default="origin", help="remote name to switch branches, default origin")
    prog_switch.add_argument("-g", "--group", dest="group", default="all", help="group to switch branches, default all")
    prog_switch_meg = prog_switch.add_mutually_exclusive_group()
    prog_switch_meg.add_argument("-c", "--create", dest="new_branch_name", help="create a new branch named <new-branch> base on origin/HEAD")
    prog_switch_meg.add_argument("-b", "--branch", dest="branch_name", help="branch to switch to")
    prog_switch.set_defaults(func=switch_impl)

    prog_branch = subparsers.add_parser("branch", description="List or delete branches", help="list or delete branches")
    prog_branch.add_argument("list", nargs='?', default="list", help="list branch names")
    prog_branch.add_argument("-g", "--group", dest="group", default="all", help="group to operate, default all")
    prog_branch_meg = prog_branch.add_mutually_exclusive_group()
    prog_branch_meg.add_argument("-d", "--delete", dest="delete", help="delete fully merged branch")
    prog_branch_meg.add_argument("-D", "--DELETE", dest="force_delete", help="delete branch (even if not merged)")
    prog_branch.set_defaults(func=branch_impl)

    prog_cherry_pick = subparsers.add_parser("cherry-pick", description="TODO:add repo(s)", help="TODO:add repo(s)")

    prog_push = subparsers.add_parser("push", description="Update remote refs along with associated objects", help="update remote refs along with associated objects")
    prog_push.add_argument("remote", default="remote", help="remote branch to be pushed")
    prog_push.add_argument("-g", "--group", dest="group", default="all", help="group to push, default all")
    prog_push.add_argument("-f", "--force", dest="force", action='store_true', help="force updates")
    prog_push.set_defaults(func=push_impl)

    prog_command = subparsers.add_parser("command", description="Execute user-defined commands", help="execute user-defined commands")
    prog_command.add_argument("-c", "--command", dest="command_name", help="execute 'command_name'")
    prog_command.add_argument("-l", "--list", dest="list", action='store_true', help="list all user-defined commands")
    prog_command.set_defaults(func=command_impl)

    args = prog.parse_args()
    logging.debug("command args={}".format(args))
    if "func" in args:
        args.func(args)
    else:
        prog.print_help()

if __name__ == "__main__":
    main()