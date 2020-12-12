"""
Tests for the yaml spec stuff.
"""

import pytest

from rjgtoys.cli import Tool, SpecificationError

def test_yaml_parsing():
    """Basic spec parsing works."""

    data = """
_package: package.namespace
word1:
  word2: w1w2
word3: w3
"""

    spec = set(Tool.spec_from_yaml(data))

    assert spec == set((
        ('word1 word2', 'package.namespace.w1w2'),
        ('word3', 'package.namespace.w3')
    ))

def test_yaml_parsing_phrases():
    """Specs may include phrases, underscores are skipped, namespace may be extended."""

    data = """
_package: package.namespace
_title: Top-level commands
top level:
  cmd1: top1
  sub commands:
    _package: subcommands
    subcommand 1: sub1
    subcommand 2: sub2
"""

    spec = set(Tool.spec_from_yaml(data))

    assert spec == set((
        ('top level cmd1', 'package.namespace.top1'),
        ('top level sub commands subcommand 1', 'package.namespace.subcommands.sub1'),
        ('top level sub commands subcommand 2', 'package.namespace.subcommands.sub2'),
    ))

def test_yaml_constructor():

    tool = Tool.from_yaml("""
    _package: tests.unit
    first: cmd1
    second: cmd2
    """)

    assert tool.cmds == [
        (['first'], 'first', 'tests.unit.cmd1'),
        (['second'], 'second', 'tests.unit.cmd2')
        ]


def test_spec_validation():
    """An invalid spec is spotted."""

    # This is fine - redundant but not ambiguous:

    spec = Tool.spec_from_yaml("""
        _package: testing
        first command: impl
        first:
          command: impl
        """)

    # This is ambiguous:

    with pytest.raises(SpecificationError):
        spec = Tool.spec_from_yaml("""
        _package: testing
        first command: impl
        first:
          command: other
        """)

