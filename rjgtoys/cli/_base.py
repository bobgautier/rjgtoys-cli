"""

The :class:`~rjgtoys.cli.Command` base class
--------------------------------------------

.. autoclass:: Command
   :members:  add_arguments, run

   .. automethod:: build_parser

Parser building methods and the :attr:`arguments` attribute
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Describe the ``_arg__`` mechanism here.

The :class:`~rjgtoys.cli.Tool` base class
-----------------------------------------

.. autoclass:: Tool

The YAML tool specification language
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Don't forget to describe the YAML specification language

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

    def __init__(self, errors):
        errs = []

        for (phrase, impls) in errors:
            impls = ",".join(impls)
            errs.append(f"'{phrase}' implemented by [{impls}]")

        super().__init__(f"Specification error (ambiguous): {errs}")


class HelpNeeded(Exception):
    """Raised when the user asks for help.

    The exception contains the help to be delivered.
    """

    pass


class CommaList(argparse.Action):
    """An action that allows an option to be used to specify multiple values,
    either as a comma-separated list, or by using the option multiple times,
    or a combination of those.
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


class Command(object):
    """
    This is the base class for command actions.

    Each command subclass should override some of the
    following:

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
        pass

    def handle_arguments(self, args):
        pass

    def parse_args(self,argv=None):
        p = self.build_parser()

        args = p.parse_args(argv)
        return args

    def main(self, argv=None):
        args = self.parse_args(argv)
        self.check_arguments(args)
        try:
            self.handle_arguments(args)
            return args._action(args) or 0
        except HelpNeeded as help:
            print(str(help))
            return 0

    def run(self, args):
        """This performs the command action, and should be overridden by subclasses."""

        pass


class Tool(object):

    def __init__(self, commands):

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
        """Generate a sequence of all errors found in a spec."""

        targets = defaultdict(set)

        for (phrase, impl) in spec:
            targets[phrase].add(impl)

        for (phrase, impls) in targets.items():
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

            if t in ('help','--help','-h'):
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
        if prefix:
            prefix = " ".join(prefix)
            heading=f"Unrecognised command '{prefix}', valid options are:"
        else:
            heading = "Unrecognised command, valid options are:"

        self.do_help(possible, heading=heading)

    def handle_incomplete(self, prefix, possible):
        if prefix:
            prefix = " ".join(prefix)
            heading = f"Incomplete command '{prefix}', could be one of:"
        else:
            heading = "Incomplete command, could be one of:"

        self.do_help(possible, heading=heading)

def resolve(name):
    """ Convert a dotted module path to an object """

    if not isinstance(name,str):
        return name

    p = name.rfind('.')
    if p > 0:
        mod = name[:p]
        cls = name[p+1:]
        m = importlib.import_module(mod)
#        m = sys.modules[mod]
        target = getattr(m,cls)
    else:
        target = globals()[name]

    return target

class add_to_set(argparse.Action):

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
