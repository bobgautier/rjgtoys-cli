
import sys
import argparse

import importlib

class NoSuchCommandError(Exception):
    pass


class IncompleteCommandError(Exception):
    pass


class HelpNeeded(Exception):
    """Raised when the user asks for help.

    The exception contains the help to be delivered.
    """

    pass

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
        self.add_options(p)
        return p

    def add_options(self,p):
        return p

    def check_options(self,opts):
        pass

    def handle_options(self,opts):
        pass

    def parse_args(self,argv=None):
        p = self.build_parser()

        opts = p.parse_args(argv)
        return opts

    def main(self, argv=None):
        opts = self.parse_args(argv)
        self.check_options(opts)
        try:
            self.handle_options(opts)
            return opts._action(opts) or 0
        except HelpNeeded as help:
            print(str(help))
            return 0

    def run(self,opts):
        pass

class Tool(object):

    def __init__(self, commands):

        self.cmds = sorted((p.split(' '),p,c) for (p,c) in commands)

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
