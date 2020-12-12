"""
Most of the CLI core is here.

"""

import sys
import argparse
from collections import defaultdict

import importlib

from rjgtoys.yaml import yaml_load, yaml_load_path

__all__ = (
    'Command', 'Tool',
    'CommaList',
    'NoSuchCommandError',
    'IncompleteCommandError',
    'SpecificationError',
    'HelpNeeded'
    )

class NoSuchCommandError(Exception):
    pass


class IncompleteCommandError(Exception):
    pass


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
    Base for command parsers/actions
    """
    description = None

    epilog = None
    usage = None

    formatter_class = argparse.ArgumentDefaultsHelpFormatter

    # Useful for suppressing defaults in parameters
    SUPPRESS = argparse.SUPPRESS

    def build_parser(self):

        # Return an argument parser

        p = argparse.ArgumentParser(
            description=self.description,
            epilog=self.epilog,
            usage=self.usage,
            formatter_class=self.formatter_class
        )

        p.set_defaults(_action=self.run)
        self.add_arguments(p)
        return p

    def add_arguments(self,p):
        return self.add_options(p)

    def add_options(self, p):
        """Deprecated old name for add_arguments."""
        pass

    def check_arguments(self, args):
        return self.check_options(args)

    def check_options(self,opts):
        pass

    def handle_arguments(self, args):
        return self.handle_options(args)

    def handle_options(self,opts):
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
                    yield (' '.join(tokens), namespace + '.' + body)
                    continue
                assert isinstance(body, dict)

                yield from cls._parse_part(namespace, tokens, body)
            finally:
                tokens = tokens[:-1]

    def do_help(self,possible=None):
        if possible is None:
            possible = self.cmds

        print("Valid commands:")
        w = max(len(p) for (_,p,_) in possible)

        for (_,p,c) in possible:
            try:
                desc = resolve(c).description
            except Exception as e:
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
                raise IncompleteCommandError(prefix)

            if t in ('help','--help'):
                # do some help
                self.do_help(possible)
                return

            prefix.append(t)

            possible = [(p,s,c) for (p,s,c) in possible if p[:len(prefix)] == prefix]

            if not possible:
                raise NoSuchCommandError(prefix)

#        print "Found command '%s'" % (' '.join(prefix))

        cmdargv = argv[len(prefix):]

#        print "Cmd args %s" % (cmdargv)

        target = possible[0][2]
#        print "Target %s" % (target)

        target = resolve(target)

        cmd = target()

        return cmd.main(cmdargv)

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
