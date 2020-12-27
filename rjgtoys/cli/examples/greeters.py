
from greetbase import GreeterBase

from rjgtoys.cli import Tool

class HelloCommand(GreeterBase):

    description = "Says hello"

    arguments = "name"

    DEFAULT_NAME = "me"

    def run(self, args):
        print(f"Hello from {args.name}!")

class GoodbyeCommand(GreeterBase):

    description = "Says goodbye"

    arguments = "name"

    DEFAULT_NAME = "him"

    def run(self, args):
        print(f"Goodbye from {args.name}")

tool = Tool.from_yaml(f"""
_package: {__name__}
say hello: HelloCommand
say goodbye: GoodbyeCommand
""")

if __name__ == "__main__":
    import sys
    sys.exit(tool.main())


