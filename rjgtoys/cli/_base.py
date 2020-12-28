"""

API Reference
=============

The :class:`~rjgtoys.cli.Command` base class
--------------------------------------------

.. autoclass:: Command


The :class:`~rjgtoys.cli.Tool` base class
-----------------------------------------

.. autoclass:: Tool


Argument Actions
----------------

These implement the :class:`argparse.Action` interface, and can therefore
be passed as the ``action`` parameter to :meth:`argparse.ArgumentParser.add_argument`

.. autoclass:: CommaList
.. autoclass:: add_to_set

Exceptions
----------

.. autoexception:: HelpNeeded
.. autoexception:: SpecificationError


Internals
---------

.. autofunction:: resolve

Parser building methods and the :attr:`arguments` attribute
===========================================================

By default, unless you override the :meth:`rjgtoys.cli.Command.add_arguments` method
in your own subclass, the parser for your command is built by calling a number of
methods whose names are listed in the attribute (usually, *class* attribute)
called :attr:`arguments`.

This attribute can be either an iterable returning a sequence of strings, or a single
comma-separated string (which will be split by :meth:`~rjgtoys.cli.Command.add_arguments`).

Each name in the :attr:`arguments` sequence is used to form a method name by prepending
``_arg_`` to it, and the method is called with the parser under construction as
a parameter.   So 'arg' methods tend to look like this::

    class MyCommand(Command):
        \"""Part of a subless definition\"""

        def _arg_name(self, p):
            p.add_argument(
                '--name',
                type=str,
                help="Name of person to greet",
                default=self.DEFAULT_NAME)
            )

The method is called for its side-effect on the parser object passed in; the return
value is ignored.

To use the above, you'd write something like this::

    class HelloCommand(MyCommand):

        arguments = 'name'

        def run(self, args):
            print(f"Hello, {args.name}")

Parser building methods are free to add as many arguments as they need, and even to add
subparsers and other exotic things.   They can of course also call other parser
building methods.

Each of your :class:`~rjgtoys.cli.Command` subclasses should define its
own :attr:`arguments` attribute (or property) that lists the parser builders
that need to be called.

This will work best if you create an intermediate class, e.g. ``MyCommand``, that
defines a `library` of ``_arg_`` methods for your ``MyCommand`` subclasses to
choose from.

You are of course free to override :meth:`~rjgtoys.cli.Command.add_arguments` in
your subclasses, and do parser building some other way.

The YAML tool specification language
====================================

The YAML used to describe a :class:`~rjgtoys.cli.Tool` using
:meth:`~rjgtoys.cli.Tool.from_yaml` basically defines a mapping
from command phrases to Python classes.

The Python classes are named using the dotted name that you'd use in a module
that had imported the module that provides the class; ``top.inner.CommandClass``
refers to a class ``CommandClass`` in the module (or subpackage) ``inner`` within
the package ``top``.

Instead of a command phrase, a 'special keyword' can be used.  The keywords
all start with underscore, ``_``, because nobody in their right mind (or me) would
ever create a command language in which command names started with underscore.

Currently the only 'special keyword' that is used is ``_package``; this sets a package
'prefix' for all commands; the prefix is prepended to the class paths specified
for the commands, allowing them to be shorter, and avoiding
repetition.

So the following two specification are equivalent::

    # Example 1: no _package
    say hello: rjgtoys.cli.examples.hello.HelloCommand
    wave goodbye: rjgtoys.cli.examples.goodbye.GoodbyeCommand

    # Example 2: with _package
    _package: rjgtoys.cli.examples
    say hello: hello.HelloCommand
    wave goodbye: goodbye.GoodbyeCommand

In place of a patch to a command implementation, a mapping may be given, that
defines a 'sublanguage', prefixed by the phrase that labels it.

This can save on repetition of prefixes for commands.  The following two
specifications are equivalent::

    # Example 1: flat language
    _package: discovery
    podbay doors open: podbay.doors.OpenCommand
    podbay doors close: podbay.door.CloseCommand
    podbay hatch open: podbay.hatch.OpenCommand
    podbay hatch close: podbay.hatch.CloseCommand

    # Example 2: nested languages
    _package: discovery
    podbay:
      _package: podbay
      doors:
        _package: doors
        open: OpenCommand
        close: CloseCommand
      hatch:
        _package: hatch
        open: OpenCommand
        close: CloseCommand

The 'nested' version takes more lines, but there is much less repetition of
'navigational' detail.

Note that sublanguages can be nested as deep as necessary.

The nested structure can be combined with YAML file inclusion, so that the
language definition itself can be modularised::

  # File doors.yaml
  _package: discovery.podbay.doors
  open: OpenCommand
  close: CloseCommand

  # File hatch.yaml
  _package: discovery.podbay.hatch
  open: OpenCommand
  close: CloseCommand

  # File podbay.yaml
  podbay:
    doors: !include doors.yaml
    hatch: !include hatch.yaml

The ``!include`` directive is implemented by rjgtoys.yaml_.

.. _rjgtoys.yaml: https://rjgtoys.readthedocs.io/projects/yaml/en/latest/

"""

import sys
import argparse
from collections import defaultdict

import importlib

from rjgtoys.yaml import yaml_load, yaml_load_path

__all__ = (
    'Command', 'Tool',
    'CommaList',
    'add_to_set',
    'SpecificationError',
    'HelpNeeded'
    )


class SpecificationError(Exception):
    """Raised if a YAML tool specification is ambiguous.

    A specification is ambiguous if a single phrase is associated
    with more than one Python class.

    It is not an error for a single phrase to be mentioned more than
    once for the *same* Python class.
    """

    def __init__(self, errors):
        errs = []

        for (phrase, impls) in errors:
            impls = ",".join(impls)
            errs.append(f"'{phrase}' implemented by [{impls}]")

        super().__init__(f"Specification error (ambiguous): {errs}")


class HelpNeeded(Exception):
    """Raised by a :class:`Command` to cause help to be printed.

    If :meth:`Command.main` sees a :exc:`HelpNeeded` exception it
    prints the exception to standard output and exits.

    This is intended to allow command implementations to deliver
    helpful messages to their users without having to contain
    explicit print calls or similar.

    """

    pass



class Command(object):
    """
    This is the base class for command actions.

    Each command subclass should override some of the
    following attributes:

    :py:attr:`description` (:class:`str`)
      A one-line short description of what the command does.

    :py:attr:`epilog` (:class:`str`)
      A 'tail' for the help text of the command.

    :py:attr:`usage` (:class:`str`)
      A longer description of how to use the command.

    :py:attr:`formatter_class` (`argparse formatter class`) = :class:`argparse.ArgumentDefaultsHelpFormatter`
      The class to be used to format help for this command.

    :py:attr:`arguments` (:class:`str or iterable`)
      Either an iterable producing a sequence of parser-building method names, or
      a string containing a comma-separated list of parser-building method names.

    Methods (most likely overridden first):

    .. automethod:: run

    .. automethod:: add_arguments

    .. automethod:: check_arguments

    .. automethod:: handle_arguments

    .. automethod:: build_parser

    .. automethod:: parse_args

    .. automethod:: main

    """
    description = None

    epilog = None
    usage = None

    formatter_class = argparse.ArgumentDefaultsHelpFormatter

    arguments = ()

    # Useful for suppressing defaults in parameters
    SUPPRESS = argparse.SUPPRESS

    def __init__(self, name=None):
        self._name = name

    def build_parser(self):

        # Return an argument parser

        p = argparse.ArgumentParser(
            self._name,
            description=self.description,
            epilog=self.epilog,
            usage=self.usage,
            formatter_class=self.formatter_class
        )

        p.set_defaults(_action=self.run)
        self.add_arguments(p)
        return p

    def add_arguments(self, p):
        """Add arguments to the parser for this command.

        The default implementation uses the :py:attr:`arguments`
        attribute to produce a list of 'argument factories' to
        invoke.
        """

        args = self.arguments
        if isinstance(args, str):
            args = args.split(',')

        for argname in args:
            argname = argname.strip()
            if not argname:
                continue
            action = getattr(self, '_arg_'+argname)
            action(p)

    def check_arguments(self, args):
        """Check parsed arguments for validity.

        Called by :meth:`main` once the arguments have been parsed, but before
        :meth:`handle_arguments`.

        Exceptions raised by this method will not be caught by :meth:`main`.

        The default implementation does nothing.
        """

        pass

    def handle_arguments(self, args):
        """Process parsed arguments.

        Called by :meth:`main` once the arguments have been checked by
        :meth:`check_arguments`, and just before the main action method, :meth:`run`
        is called.

        If this method raises :exc:`HelpNeeded` the exception will be printed
        (as help), but no other exceptions will be caught.

        The default implementation does nothing.
        """

        pass

    def parse_args(self,argv=None):
        """Build a parser and parse the arguments.

        Why is it structured this way?   I don't know.
        """

        p = self.build_parser()

        args = p.parse_args(argv)
        return args

    def main(self, argv=None):
        """The main entrypoint for a :class:`Command`.

        Parses the arguments, checks them, calls any handlers,
        and then calls the main action.

        Delivers help if needed.
        """

        args = self.parse_args(argv)
        self.check_arguments(args)
        try:
            self.handle_arguments(args)
            return args._action(args) or 0
        except HelpNeeded as help:
            print(str(help))
            return 0

    def run(self, args):
        """This performs the command action, and should be overridden by subclasses.

        By the time :meth:`run` is called, both :meth:`check_arguments` and
        :meth:`handle_arguments` have been called and returned successfully.

        Should return an integer status code of 0 for success, anything else
        for failure.

        A return of `None` is interpreted as 0.
        """

        pass


class Tool(object):

    # Command line tokens that cause help to be generated

    HELP_TOKENS = ('help', '--help', '-h')

    def __init__(self, commands):
        """The ``commands`` parameter is a list of ('phrase', 'classpath')
        pairs that define the 'command language' of this tool.   Each
        acceptable phrase is written out in full, along with a dotted 'classpath'
        that defines the Python class that will implement the command (and should
        be a subclass of :class:`rjgtoys.cli.Command`)::

          tool = Tool((
                ('make tea', 'home_essentials.MakeTeaCommand'),
                ('open podbay doors', 'discovery.hal.OpenPodbayDoors'),
                ('eject core', 'galaxy.emergencies.CoreEject')
                ))

        """
        self.cmds = sorted((p.split(' '),p,c) for (p,c) in commands)

    @classmethod
    def from_yaml(cls, text=None, path=None):
        """Create a tool definition from some yaml."""

        spec = cls.spec_from_yaml(text=text, path=path)

        return cls(spec)

    @classmethod
    def spec_from_yaml(cls, text=None, path=None):
        if None not in (text, path):
            raise ValueError("Tool specification may be text or path, not both")

        data = None
        if path:
            data = yaml_load_path(path)
        elif text:
            data = yaml_load(text)

        if not data:
            raise ValueError("Tool specification is missing")

        # Reduce the spec to something usable by the constructor

        """
        Example:

          _package: path.to.package:
          _title: Name of this group
          _description: |
            Longer description of this command group
          # Other keys define commands by naming the class that implements each
          word-or-phrase: name-of-class
          # Or by defining subcommands, using a nested structure:
          word-or-phrase:
             _package: optional
             _title: optional
             _description: optional
             word-or-phrase: module.suffix

        """

        return cls.spec_from_dict(data)

    @classmethod
    def spec_from_dict(cls, data):

        spec = list(cls._spec_from_dict(data))

        return cls.validate_spec(spec)

    @classmethod
    def _spec_from_dict(cls, data):
        yield from cls._parse_part('', tuple(), data)

    @classmethod
    def validate_spec(cls, spec):

        errors = list(cls._spec_errors(spec))

        if errors:
            raise SpecificationError(errors)

        return spec

    @classmethod
    def _spec_errors(cls, spec):
        """Generate a sequence of all errors found in a spec.

        Identifies phrases that have more than one implementation,
        i.e. are ambiguous.
        """

        targets = defaultdict(set)

        for (phrase, impl) in spec:
            targets[phrase].add(impl)

        for (phrase, impls) in targets.items():
            # Is this phrase ambiguous?
            if len(impls) > 1:
                yield (phrase, impls)

    @classmethod
    def _parse_part(cls, namespace, tokens, data):
        try:
            # Don't leave a leading '.' on this.
            namespace = (namespace + '.' + data._package).lstrip('.')
        except AttributeError:
            pass

        for (phrase, body) in data.items():
            if phrase.startswith('_'):
                continue
            tokens = tokens + (phrase,)
            try:
                if isinstance(body, str):
                    yield (' '.join(tokens), (namespace + '.' + body).lstrip('.'))
                    continue
                assert isinstance(body, dict)

                yield from cls._parse_part(namespace, tokens, body)
            finally:
                tokens = tokens[:-1]

    def do_help(self,possible=None, heading=None):
        if possible is None:
            possible = self.cmds

        print(heading or "Valid commands:")
        w = max(len(p) for (_,p,_) in possible)

        for (_,p,c) in possible:
            try:
                desc = resolve(c).description
            except Exception as e:
                raise
                desc = "BUG: %s" % (e)

            print("  %s - %s" % (p.ljust(w), desc))

    def main(self, argv=None):
        """Parse command line tokens, run the command, return the result.

        Parses the tokens in ``argv`` (or by default, in ``sys.argv[1:]``)
        and takes appropriate action, either:

        1. Run the command action (causing further process of the command line) or
        2. Print help, if requested to do so (``help``, ``--help`` or ``-h``)
           on the command line, before a command is recognised)
        3. Print help about an unrecognised or incomplete command


        """

        possible = self.cmds
        prefix = []

        argv = argv or sys.argv[1:]
        tokens = iter(argv)

        while len(possible):

            if len(possible) == 1:
                # Only one option: have we seen the entire phrase?
                if possible[0][0] == prefix:
                    break

            try:
                t = next(tokens)
            except:
                return self.handle_incomplete(prefix, possible)

            if t in self.HELP_TOKENS:
                # do some help
                self.do_help(possible)
                return

            prefix.append(t)

            next_state = [(p,s,c) for (p,s,c) in possible if p[:len(prefix)] == prefix]

            if not next_state:
                return self.handle_unrecognised(prefix, possible)

            possible = next_state

#        print "Found command '%s'" % (' '.join(prefix))

        cmdargv = argv[len(prefix):]

#        print "Cmd args %s" % (cmdargv)

        target = possible[0][2]
#        print "Target %s" % (target)

        target = resolve(target)

        cmd = target(name=' '.join(prefix))

        return cmd.main(cmdargv)

    def handle_unrecognised(self, prefix, possible):
        """Handle an unrecognised command.

        The default implementation prints some help.
        """

        if prefix:
            prefix = " ".join(prefix)
            heading=f"Unrecognised command '{prefix}', valid options are:"
        else:
            heading = "Unrecognised command, valid options are:"

        self.do_help(possible, heading=heading)

    def handle_incomplete(self, prefix, possible):
        """Handle an incomplete command.

        The default implementation prints some help.
        """

        if prefix:
            prefix = " ".join(prefix)
            heading = f"Incomplete command '{prefix}', could be one of:"
        else:
            heading = "Incomplete command, could be one of:"

        self.do_help(possible, heading=heading)

def resolve(name):
    """Convert a dotted module path to an object.

    This is used to do the importing, when :class:`Tool` resolves
    the path to a command implementation.
    """

    if not isinstance(name,str):
        return name

    p = name.rfind('.')
    if p > 0:
        mod = name[:p]
        cls = name[p+1:]
        m = importlib.import_module(mod)
        target = getattr(m,cls)
    else:
        target = globals()[name]

    return target


class CommaList(argparse.Action):
    """An :class:`argparse.Action` that allows an option to be used to specify
    multiple values, either as a comma-separated list, or by using the option
    multiple times, or a combination of those.
    """

    separator = ','

    def __call__(self, parser, ns, value, option_string=None):

        current = getattr(ns, self.dest) or []

        value = self._split(value)

        current.extend(value)

        setattr(ns, self.dest, current)

    def _split(self, value):
        """Separate the parts of value."""

        value = [v.strip() for v in value.split(self.separator)]

        value = [self._check(v) for v in value if v]

        return value

    def _check(self, value):
        """Check and if necessary convert the value to the desired type."""

        return value


class add_to_set(argparse.Action):
    """An :class:`argparse.Action` that builds a set.

    Use this as an ``action`` parameter to :meth:`~argparse.ArgumentParser.add_argument`
    when you want to build a set from multiple uses of an option, instead of, for example,
    a list (which you would do by passing ``action='append'``)
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            v = getattr(namespace, self.dest)
        except:
            v = None
        if v is None:
            v = set()
            setattr(namespace, self.dest, v)

        if isinstance(values,(list,tuple)):
            v.update(values)
        else:
            v.add(values)


class splitlist(object):

    def __init__(self,itemtype=None):
        self.itemtype = itemtype or str

    def __call__(self,value):
        r = []
        for v in value.split(","):
            v = v.strip()
            if v:
                r.append(self.itemtype(v))
        return r
