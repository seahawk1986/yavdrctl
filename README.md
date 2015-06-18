````
usage: yavdrctl [-h] [--argsdir ARGSDIR] [--availdir AVAILDIR] [-v] CMD ...

controls vdr argument files

positional arguments:
  CMD
    list               list configuration files
    enable             create symlink for configuration file(s)
    disable            remove symlink(s) in ARGSDIR
    edit               edit configuration file(s)

optional arguments:
  -h, --help           show this help message and exit
  --argsdir ARGSDIR    read files from given directory instead of ARGSDIR
  --availdir AVAILDIR  read files from given directory instead of AVAILDIR
  -v, --version        output version information and exit

/usr/local/bin/yavdrctl adds/removes symlinks or lists the available or active plugins for vdr.
If ARGSDIR is not specified, /usr/local/bin/yavdrctl tries to read it using pkg-config.

Default ARGSDIR is /etc/vdr/conf.d
Default AVAILDIR is ARGSDIR/../conf.avail

available CMD arguments:

	list
		usage: yavdrctl list [-h] [--enabled | --disabled | -o OUTPUT]

		optional arguments:
		  -h, --help            show this help message and exit
		  --enabled             print a sorted list of all configuration files from
		                        ARGSDIR
		  --disabled            print a sorted list of all configuration files from
		                        AVAILDIR which are not symlinked to ARGSDIR
		  -o OUTPUT, --output OUTPUT
		                        output format (default: table):
		                        classic|table|plaintable|json

	enable
		usage: yavdrctl enable [-h] [-p PRIORITY] [-f] [--all] [file [file ...]]

		positional arguments:
		  file                  create a symlink in ARGSDIR pointing to the file in
		                        AVAILDIR

		optional arguments:
		  -h, --help            show this help message and exit
		  -p PRIORITY, --priority PRIORITY
		                        set priority for plugin(s).
		  -f, --force           force creation, even if there is an exiting file
		  --all                 apply to all config files

	disable
		usage: yavdrctl disable [-h] [--all] [-f] [file [file ...]]

		positional arguments:
		  file         delete symlink in ARGSDIR pointing to the file in AVAILDIR

		optional arguments:
		  -h, --help   show this help message and exit
		  --all        apply to all config file symlinks
		  -f, --force  delete config, even if it is a file, not a symlink

	edit
		usage: yavdrctl edit [-h] file [file ...]

		positional arguments:
		  file        configuration file(s) to edit

		optional arguments:
		  -h, --help  show this help message and exit
````
