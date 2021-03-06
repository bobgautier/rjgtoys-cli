# `rjgtoys.cli`: Command-line tool components

`rjgtoys.cli` provides support for building CLI tools on top of the
standard Python `argparse` parser library.

It supports:

- Creation of 'command languages' in which diverse operations are given names
  that are short phrases, such as 'make tea';
- Modularisation of parser construction, so that commands that share options
  can share the code to parse and process them;
- New options for processing command line arguments, such as comma-separated lists,
  and set-valued options;
- Assistance with producing help.

Read the documentation at http://rjgtoys.readthedocs.org/projects/cli/
