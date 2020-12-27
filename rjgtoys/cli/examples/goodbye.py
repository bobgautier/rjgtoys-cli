
from rjgtoys.cli import Command

class GoodbyeCommand(Command):

    description = "Says goodbye"

    DEFAULT_NAME = "you"

    def add_arguments(self, p):
        p.add_argument(
            '--name',
            type=str,
            help="Name of the person to greet",
            default=self.DEFAULT_NAME
        )

    def run(self, args):
        print(f"Goodbye {args.name}!")

if __name__ == "__main__":

    import sys

    cmd = GoodbyeCommand()
    sys.exit(cmd.main())


