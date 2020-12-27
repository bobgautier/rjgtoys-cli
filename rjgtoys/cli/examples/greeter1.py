"""Example tool"""

from rjgtoys.cli import Tool

tool = Tool(
    (
        ('say hello', 'rjgtoys.cli.examples.hello.HelloCommand'),
        ('say goodbye', 'rjgtoys.cli.examples.goodbye.GoodbyeCommand')
    )
)

if __name__ == "__main__":
    import sys
    sys.exit(tool.main())

