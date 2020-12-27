
from rjgtoys.cli import Command, Tool
from rjgtoys.cli._base import resolve

import pytest
import os

class TargetCommand(Command):

    description = "A command for testing"

    def add_arguments(self,p):
        p.add_argument('--test',help="Do test",
            action="store_true", default=False)
        p.add_argument('--value',help="Value",
            type=int, default=0)

        return p

    def run(self,opts):
        self.result = opts.value

class TryCommand(Command):

    description = "A command for trying"

    def add_arguments(self,p):
        p.add_argument('--tryout',help="Try it",
            action="store_true", default=False)

    def run(self,opts):
        self.tried = opts.tryout

def test_command_basics():

    cmd = TargetCommand()

    opts = cmd.parse_args([])

    assert not opts.test
    assert opts.value == 0

    opts = cmd.parse_args(['--test','--value','42'])

    assert opts.test
    assert opts.value == 42

    cmd.main(['--test','--value','39'])

    assert cmd.result == 39


class NoSuchCommandError(Exception):
    pass


class IncompleteCommandError(Exception):
    pass


class RaisingTool(Tool):
    """Override the help generators so we can easily check they were called."""

    def handle_unrecognised(self, prefix, possible):
        raise NoSuchCommandError

    def handle_incomplete(self, prefix, possible):
        raise IncompleteCommandError


def test_tool_basics():

    t = RaisingTool((
        ('test',TargetCommand),
        ('try this',TryCommand),
        ))

    t.main(['test'])
    t.main(['try','this'])

    with pytest.raises(NoSuchCommandError):
        t.main(['bad'])

    with pytest.raises(IncompleteCommandError):
        t.main(['try'])

    t.do_help()

def test_resolve():

    m = os.path.isfile

    assert resolve(os.path.isfile) is m
    assert resolve('os.path.isfile') is m

