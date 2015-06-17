try:
    from . arguments import Argparser
except:
    from arguments import Argparser
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile

from io import StringIO


class VDRCTL():
    version = '0.0.1'
    progname = sys.argv[0]
    special_priorities = {
        'dynamite': 90
    }
    # some shell format and color strings
    OKBLUE = '\033[94m'
    BRIGHTRED = '\033[1;31m'
    BRIGHTGREEN = '\033[1;32m'
    ENDC = '\033[0m'
    # match priority and plugin name
    # for either pluginname.conf or [0-9]+-pluginname.conf
    config_re = re.compile("^(\d*(?=-))?-?(\w[\S]*(?=\.conf))")
    name_re = re.compile("^(\d*(?=-))?-?(\w[\S]*)")
    default_priority = 50
    table_template = (
        "{priority: >{prio_width}} {name: <{name_width}} "
        "{config: <{config_width}} {origin}"
    )
    table_template_enabled = (
        "{priority: >{prio_width}} \033[1;32m{name: <{name_width}} "
        "{config: <{config_width}}\033[0m {origin}"
    )
    table_template_disabled = (
        "{priority: >{prio_width}} \033[1;31m{name: <{name_width}} "
        "{config: <{config_width}}\033[0m {origin}"
    )
    table_template_dead_link = (
        "{priority: >{prio_width}} \033[1;35m{name: <{name_width}} "
        "{config: <{config_width}} dead symlink!\033[0m"
    )
    template_classic_enabled = (
        "{name: <{name_width}} \033[1;32m{status}\033[0m")
    template_classic_disabled = (
        "{name: <{name_width}} \033[1;31m{status}\033[0m")
    template_classic = "{name: <{name_width}} {status}"

    # formatting options
    prio_width = 4
    name_width = 16
    config_width = 24
    line_width = 84

    def __init__(self):
        actions = {
            None: self.list_configs,
            'list': self.list_configs,
            'enable': self.enable_plugins,
            'disable': self.disable_plugins,
            'edit': self.call_editor
        }
        self.output_str = StringIO()
        self.output_list = []
        self.json_encoder = json.JSONEncoder()
        self.header_printed = False
        self.args = Argparser(self).args
        if not self.args.availdir:
            self.args.availdir = os.path.realpath(
                "{}/../conf.avail".format(self.args.argsdir))
        self.active_config_list = self.get_configs(self.args.argsdir)
        self.availdir_config_list = self.get_configs(self.args.availdir)
        self.get_available_config_list()
        if not "output" in self.args:
            self.args.output = "classic"
        if self.args.version:
            self.print_version()
        elif "command" in self.args:
            if not 'enabled' in self.args:
                self.args.enabled = False
            if not 'disabled' in self.args:
                self.args.disabled = False
            actions[self.args.command]()

    def get_available_config_list(self):
        self.available_config_list = self.availdir_config_list
        for config in self.active_config_list:
            if not config['is_link']:
                self.available_config_list.append(config)

    def classic_line(self, name, status, islink, name_width):
        if status and islink:
            _status = "enabled"
            template = self.template_classic_enabled
        elif status:
            _status = "static"
            template = self.template_classic
        elif not status:
            _status = "disabled"
            template = self.template_classic_disabled
        return template.format(name=name, status=_status,
                               name_width=name_width)

    def table_line(self, priority, name, config, origin, enabled=None):
        if self.args.output == "table":
            if enabled is None:
                template = self.table_template
            elif not origin:
                template = self.table_template_dead_link
            elif enabled is True:
                template = self.table_template_enabled
            elif enabled is False:
                template = self.table_template_disabled
        elif self.args.output == "plaintable":
            template = self.table_template
        return template.format(
            priority=priority,
            name=name,
            config=config,
            origin=origin,
            prio_width=self.prio_width,
            name_width=self.name_width,
            config_width=self.config_width
        )

    def make_header(self, title=None):
        """print formatted tile and table header"""
        if title:
            print(title)
            print("=" * self.line_width)
        print(self.header)
        #print("-"*80)
        print(
            self.table_line(
                "-" * self.prio_width,
                "-" * self.name_width,
                "-" * self.config_width,
                "-" * (self.line_width - (
                    self.prio_width + self.name_width + self.config_width))
            )
        )

    def print_version(self):
        print("vdrctl version", self.version)

    def color_text(self, color, text):
        return color + text + self.ENDC

    def print_header(self):
        self.header = self.table_line(
            priority="prio",
            name="name",
            config=os.path.join(self.args.argsdir, ""),
            origin="original file",
        )
        self.make_header()

    def output(self, config_list):
        config_list = sorted(config_list,
                             key=lambda k: (k['priority'],
                                            k['name'])
                             )
        output_dict = {
            "table": self.output_table,
            "plaintable": self.output_table,
            "classic": self.output_classic,
            "json": self.output_json
        }
        output_dict[self.args.output](config_list)

    def output_table(self, config_list):
        if not self.header_printed:
            self.print_header()
            self.header_printed = True
        for config in config_list:
            print(
                self.table_line(
                    priority=config['priority'],
                    name=config['name'],
                    config=(config['filename'] if config['enabled']
                            else "disabled"),
                    origin=config['origin'],
                    enabled=config['enabled']
                )
            )

    def output_classic(self, config_list):
        if not self.header_printed:
            print(self.template_classic.format(
                name="NAME", status="STATE", name_width=self.name_width))
            self.header_printed = True
        for config in config_list:
            print(
                self.classic_line(
                    name=config['name'],
                    status=config['enabled'],
                    islink=config['is_link'],
                    name_width=self.name_width,
                )
            )

    def output_json(self, config_list):
        self.output_list.append(config_list)

    def extract_priority_and_name(self, filename):
        """extract priority and name from filename"""
        m = self.config_re.match(filename)
        priority, name = m.groups()
        if priority is None or priority == 'None':
            priority = self.default_priority
        else:
            priority = int(priority)
        return priority, name

    def get_configs(self, directory):
        """read all *.conf files from conf_dir and add their properties
        to a list"""
        config_list = []
        os.chdir(directory)
        for cfg in fnmatch.filter(os.listdir(directory), "*.conf"):
            if os.path.islink(cfg):
                is_link = True
                origin = os.path.relpath(os.path.realpath(cfg))
                if not os.path.exists(origin):
                    origin = ""
            elif os.path.isfile(cfg):
                is_link = False
                origin = os.path.join(directory, cfg)
            else:
                continue
            is_enabled = False
            if directory == self.args.argsdir or any(
                    (True for i in self.active_config_list
                     if os.path.samefile(
                         os.path.join(self.args.argsdir, i['origin']), origin)
                     )):
                is_enabled = True
            priority, name = self.extract_priority_and_name(cfg)
            config_list.append(
                {
                    "priority": priority,
                    "name": name,
                    "filename": cfg,
                    "is_link": is_link,
                    "origin": origin,
                    "enabled": is_enabled
                }
            )
        return config_list

    def disabled_configs(self):
        disabled_configs = list(filter(lambda x: x['enabled'] is False,
                                self.availdir_config_list))
        return disabled_configs

    def get_priority_and_name(self, path):
        """extract priority and name from filename"""
        m = self.name_re.match(path)
        priority, name = m.groups()
        if priority is None or priority == 'None':
            priority = self.default_priority
        else:
            priority = int(priority)
        name = name.rstrip('.conf')
        return priority, name

    def match_name_with_config_list(self, name, priority, config_list):
        matches = list(filter(lambda c: name == c['name'], config_list))
        matches = sorted(matches, key=lambda c: abs(priority - c['priority']),
                         reverse=False)
        if matches:
            return matches[0]
        else:
            False

    def list_configs(self):
        sys.stdout = self.output_str
        if not self.args.disabled:
            self.output(self.active_config_list)

        if not self.args.enabled:
            self.output(self.disabled_configs())
        sys.stdout = sys.__stdout__
        if self.args.output in ("table", "plaintable", "classic"):
            print(self.output_str.getvalue())
        elif self.args.output == "json":
            print(self.json_encoder.encode(self.output_list))

    def enable_plugins(self):
        if self.args.all:
            self.args.file = []
            for config in self.availdir_config_list:
                if not config['enabled']:
                    self.args.file.append(config['filename'])

        for plugin_cfg in self.args.file:
            prio, name = self.get_priority_and_name(plugin_cfg)
            #print(prio, name)
            config_to_enable = self.match_name_with_config_list(
                name, prio,
                self.availdir_config_list)
            if not config_to_enable:
                print("could not enable %s, no matching file found" %
                      plugin_cfg)
                continue
            origin = config_to_enable['origin']
            if prio and not self.args.priority:
                if name in self.special_priorities:
                    priority = self.special_priorities[name]
                else:
                    priority = prio
            elif "priority" in self.args:
                priority = self.args.priority
            else:
                    priority = self.default_priority
            os.chdir(self.args.argsdir)
            target = os.path.relpath(os.path.join(
                self.args.argsdir, "{}-{}.conf".format(priority, name)
            ), os.path.dirname(origin))
            origin = os.path.relpath(origin, os.path.dirname(target))
            try:
                #print("Linking %s to %s" % (origin, target))
                os.symlink(origin, target)
            except OSError:
                exit("Could not create symlink from {} to {}".format(
                     plugin_cfg, target))

    def disable_plugins(self):
        if self.args.all:
            os.chdir(self.args.argsdir)
            for config in self.active_config_list:
                if config['is_link'] or self.args.force:
                    os.unlink(config['filename'])
            return

        for plugin_cfg in self.args.file:
            prio, name = self.get_priority_and_name(plugin_cfg)
            config_to_disable = self.match_name_with_config_list(
                name, prio,
                self.active_config_list)
            if not config_to_disable:
                print("could not disable %s, no matching file found" %
                      plugin_cfg)
            os.chdir(self.args.argsdir)
            try:
                if os.path.islink(
                        config_to_disable['filename']) or self.args.force:
                    os.unlink(config_to_disable['filename'])
                else:
                    print("%s is not a symlink. use --force to delete it" %
                          config_to_disable['origin'])
            except:
                print("Could not remove synlink %s" %
                      config_to_disable['filename'])

    def call_editor(self):
        if "EDITOR" in os.environ:
            editor = os.environ['EDITOR']
        else:
            editor = "vi"
        files_to_edit = []
        for file in self.args.file:
            prio, name = self.get_priority_and_name(file)
            config = self.match_name_with_config_list(
                name, prio, self.available_config_list)
            if config and config['name'] != 'vdr':
                print("editing", config['origin'])
                try:
                    vdr_help = subprocess.check_output(
                        ['vdr', '-P', config['name'], '-h']
                    ).decode()
                    search_string = "\n" + config['name']
                    start_pos = vdr_help.find(search_string)
                    if start_pos > 0:
                        description = vdr_help[start_pos:].replace(
                            '\n', '\n#yavdrctl: ')
                except Exception as e:
                    print(e, "\n", "could not get arguments from vdr")

            elif config and config['name'] == 'vdr':
                try:
                    vdr_help = subprocess.check_output(
                        ['vdr', '-h']
                    ).decode()
                    search_string = '\nPlugins: vdr -P"name [OPTIONS]"'
                    end_pos = vdr_help.find(search_string)
                    if end_pos > 0:
                        description = ('\n#yavdrctl: ' +
                                       vdr_help[:end_pos].replace(
                                           '\n', '\n#yavdrctl: ')
                                       )
                except:
                    print(e, "\n", "could not get help text from vdr")
            else:
                print("no configuration file for %s found" % file)
                continue
            with tempfile.NamedTemporaryFile(mode="wt", delete=False) as t, \
                    open(config['origin'], 'rt') as c:
                files_to_edit.append((t.name, config['origin']))
                for line in c:
                    t.write(line)
                if description:
                    t.write(description)

        cmd = [editor]
        cmd.extend((c[0] for c in files_to_edit))
        subprocess.call(cmd, env=os.environ)
        for tmpfile, origin in files_to_edit:
            with open(tmpfile, 'rt') as t, open(origin, 'wt') as c:
                for line in t:
                    if not line.startswith("#yavdrctl: ") or len(line) < 2:
                        c.write(line)
            os.unlink(tmpfile)


def main():
    VDRCTL()

if __name__ == '__main__':
    main()
