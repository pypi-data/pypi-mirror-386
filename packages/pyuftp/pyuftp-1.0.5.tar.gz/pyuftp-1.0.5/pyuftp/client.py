""" Main client class """

import pyuftp.base, pyuftp.cp, pyuftp.share, pyuftp.utils, pyuftp._version

import platform, sys

_commands = {
            "authenticate": pyuftp.base.Auth,
            "checksum": pyuftp.utils.Checksum,
            "cp": pyuftp.cp.Copy,
            "find": pyuftp.utils.Find,
            "info": pyuftp.base.Info,
            "issue-token": pyuftp.base.IssueToken,
            "ls": pyuftp.utils.Ls,
            "mkdir": pyuftp.utils.Mkdir,
            "rcp": pyuftp.cp.RemoteCopy,
            "rm": pyuftp.utils.Rm,
            "share": pyuftp.share.Share,
        }

def get_command(name):
    return _commands.get(name)()

def show_version():
    print("PyUFTP commandline client for UFTP (UNICORE FTP) "
          "%s, https://www.unicore.eu" % pyuftp._version.get_versions().get('version', "n/a"))
    print("Python %s" % sys.version)
    print("OS: %s" % platform.platform())


def help():
    s = """PyUFTP commandline client for UFTP (UNICORE FTP) %s, https://www.unicore.eu
Usage: pyuftp <command> [OPTIONS] <args>
The following commands are available:""" % pyuftp._version.get_versions().get('version', "n/a")
    print(s)
    for cmd in _commands:
        print (f" {cmd:20} - {get_command(cmd).get_synopsis()}")
    print("Enter 'pyuftp <command> -h' for help on a particular command.")

def run(args):
    _help = ["help", "-h", "--help"]
    if len(args)<1 or args[0] in _help:
        help()
        return
    _version = ["version", "-V", "--version"]
    if args[0] in _version:
        show_version()
        return

    command = None
    cmd = args[0]
    for k in _commands:
        if k.startswith(cmd):
            command = get_command(k)
            break
    if command is None:
        raise ValueError(f"No such command: {cmd}")
    command.run(args[1:])

def main():
    """
    Main entry point
    """
    run(sys.argv[1:])

if __name__ == "__main__":
    main()
