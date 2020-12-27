Tutorial
========


Single-command tools
--------------------

A simple CLI tool can be written as a subclass of :class:`rjgtoys.cli.Command`,
in which you provide at least three things:

1. A ``description`` class attribute, that describes what your command does;
2. An ``add_arguments`` method that adds arguments to a provided :class:`argparse.ArgumentParser`;
3. A ``run`` method that accepts parsed arguments and performs the action you want to do.

Here's a simple example:

.. literalinclude:: ../../rjgtoys/cli/examples/hello.py

This creates a script with a simple command-line interface::

    $ python rjgtoys/cli/examples/hello.py -h
    usage: hello.py [-h] [--name NAME]

    Says hello

    optional arguments:
      -h, --help   show this help message and exit
      --name NAME  Name of the person to greet (default: you)
    $ python rjgtoys/cli/examples/hello.py
    Hello you!
    $ python rjgtoys/cli/examples/hello.py --name Bob
    Hello Bob!


Composing commands into languages
---------------------------------

You can compose multiple :class:`~rjgtoys.cli.Command` classes into a single
script that defines a :class:`rjgtoys.cli.Tool`.

A :class:`~rjgtoys.cli.Tool` defines a 'command language' by listing a set
of command names (or phrases) along with the name of the :class:`~rjgtoys.cli.Command`
class that implements each.

Imagine you have another :class:`~rjgtoys.cli.Command` implementation, similar to
the :class:`~rjgtoys.cli.examples.hello.HelloCommand`, called :class:`~rjgtoys.cli.examples.hello.GoodbyeCommand`,
and you wanted to provide both in a single 'greeter' script.

It might look like this:

.. literalinclude:: ../../rjgtoys/cli/examples/greeter1.py

The :class:`~rjgtoys.cli.Tool` constructor accepts a list of `(command phrase, class path)`
pairs; the 'command phrase' is simply the list of command line tokens that will
select a function, and the `class path` is a dotted path to the :class:`~rjgtoys.cli.Command`
class that implements that function.

The :class:`~rjgtoys.cli.Tool` class handles parsing of the command phrases themselves,
generating help about the available commands, and dealing with parsing errors,
until a complete phrase is recognised, at which point the corresponding :class:`~rjgtoys.cli.Command`
is invoked, and parses the rest of the command line.

Here is some example output from the above `greeter1` script::

    $ python rjgtoys/cli/examples/greeter1.py
    Incomplete command, could be one of:
      say goodbye - Says goodbye
      say hello   - Says hello
    $ python rjgtoys/cli/examples/greeter1.py say hello
    Hello you!
    $ python rjgtoys/cli/examples/greeter1.py say goodbye -h
    usage: say goodbye [-h] [--name NAME]

    Says goodbye

    optional arguments:
      -h, --help   show this help message and exit
      --name NAME  Name of the person to greet (default: you)

Constructing a :class:`~rjgtoys.cli.Tool` from YAML
---------------------------------------------------

The 'pure Python' syntax for describing a tool language can be fiddly and
hard to read, when the list becomes large.

It's also possible to describe a :class:`~rjgtoys.cli.Tool` in YAML:

.. literalinclude:: ../../rjgtoys/cli/examples/greeter2.py

Furthermore, to avoid repeating a package prefix many times, the YAML
form allows setting a 'default' package:

.. literalinclude:: ../../rjgtoys/cli/examples/greeter3.py

It is also possible to load the YAML from a file, which makes it easy
to consider putting the command language definition in the hands of
your users: provide them with a set of command implementations, and
a default bit of YAML to be starting with, and they can pick and choose
which commands they need available, and what they'd like to call them.

The :class:`rjgtoys.cli.examples.goodbye.GoodbyeCommand` code
-------------------------------------------------------------

Here is the code for the 'say goodbye' command:

.. literalinclude:: ../../rjgtoys/cli/examples/goodbye.py

