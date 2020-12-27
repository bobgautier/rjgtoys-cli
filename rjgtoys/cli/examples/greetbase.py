
from rjgtoys.cli import Command

class GreeterBase(Command):

    DEFAULT_NAME = "you"

    def _arg_name(self, p):

        p.add_argument(
            '--name',
            type=str,
            help="Name of the person to greet",
            default=self.DEFAULT_NAME
        )

    def run(self, args):
        print(f"Hello {args.name}!")
