import argparse
import subprocess
import os
import textwrap


class Argparser():

    def __init__(self, parent):
        self.parent = parent
        self.args = self.get_args()
        if not self.args.availdir:
            self.args.availdir = os.path.realpath(
                "{}/../conf.avail".format(self.args.argsdir))

    def get_vdr_pkgconfig_var(self, var=None):
        if var:
            try:
                output = subprocess.check_output(
                    ["pkg-config", "--variable", var, "vdr"],
                    env=os.environ).decode().strip()
            except:
                output = ""
        if len(output) > 0:
            return output

    def get_argsdir(self):
        argsdir = self.get_vdr_pkgconfig_var(var='argsdir')
        if argsdir:
            return argsdir
        else:
            return '/etc/vdr/conf.d'

    def get_args(self):
        """create argument parser and help text"""
        epilog = """\
    {p} adds/removes symlinks or lists the available or active plugins for vdr.
    If ARGSDIR is not specified, {p} tries to read it using pkg-config.

    Default ARGSDIR is /etc/vdr/conf.d
    Default AVAILDIR is ARGSDIR/../conf.avail
        """
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="controls vdr argument files\n",
            epilog=textwrap.dedent(epilog.format(p=self.parent.progname)),
            add_help=False
        )

        # optional Arguments for vdrctl
        parser.add_argument("-h", "--help", action=_HelpAction,
                            help="show this help message and exit")
        parser.add_argument(
            "--argsdir", default=self.get_argsdir(),
            help="read files from given directory instead of ARGSDIR")
        parser.add_argument(
            "--availdir", default=None,
            help="read files from given directory instead of AVAILDIR")
        parser.add_argument(
            "-v", "--version", action="store_true",
            help="output version information and exit")

        # Add subparser for possible commands
        cmd_parsers = parser.add_subparsers(
            dest="command", metavar="CMD")
        sub_cmd_list = cmd_parsers.add_parser(
            "list", help="list configuration files")
        # list --enabled and --disabled are mutually exclusive
        sub_list_group = sub_cmd_list.add_mutually_exclusive_group()
        sub_list_group.add_argument(
            "--enabled", action="store_true", default=False,
            help="print a sorted list of all configuration files from ARGSDIR")
        sub_list_group.add_argument(
            "--disabled", action="store_true", default=False,
            help="print a sorted list of all configuration files from AVAILDIR"
                 " which are not symlinked to ARGSDIR")
        sub_list_group.add_argument(
            "-o", "--output", default="table",
            help=("output format (default: table): "
                  "classic|table|plaintable|text|json")
        )
        # add arguments for "enable" command
        sub_cmd_enable = cmd_parsers.add_parser(
            "enable", help="create symlink for configuration file(s)")
        sub_cmd_enable.add_argument(
            "-p", "--priority", type=int,
            help="set priority for plugin(s).")
        sub_cmd_enable.add_argument(
            "-f", "--force", action="store_true",
            help="force creation, even if there is an exiting file")
        sub_cmd_enable.add_argument(
            "--all", action="store_true",
            help="apply to all config files")
        sub_cmd_enable.add_argument(
            "file", nargs="*", default=[],
            help="""\
            create a symlink in ARGSDIR pointing to the file in AVAILDIR""")
        # add arguments for "disable" command
        sub_cmd_disable = cmd_parsers.add_parser(
            "disable", help="remove symlink(s) in ARGSDIR")
        sub_cmd_disable.add_argument(
            "--all", action="store_true",
            help="apply to all config file symlinks")
        sub_cmd_disable.add_argument(
            "-f", "--force", action="store_true",
            help="delete config, even if it is a file, not a symlink")
        sub_cmd_disable.add_argument(
            "file", nargs="*", default=[],
            help="delete symlink in ARGSDIR pointing to the file in AVAILDIR")
        # add arguments for "edit" command
        sub_cmd_edit = cmd_parsers.add_parser(
            "edit", help="edit configuration file(s)")
        sub_cmd_edit.add_argument(
            "file", nargs="+", default=[],
            help="configuration file(s) to edit")

        return parser.parse_args()


class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            print("\navailable CMD arguments:\n")
            for choice, subparser in subparsers_action.choices.items():
                print("\t{}".format(choice))
                print(textwrap.indent(subparser.format_help(), "\t\t"))

        parser.exit()
