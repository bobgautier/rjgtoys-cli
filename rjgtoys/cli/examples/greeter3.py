"""Example tool"""

from rjgtoys.cli import Tool

tool = Tool.from_yaml("""
_package: rjgtoys.cli.examples
say hello: hello.HelloCommand
say goodbye: goodbye.GoodbyeCommand
"""
)

if __name__ == "__main__":
    import sys
    sys.exit(tool.main())

