
from argparse import ArgumentParser

from rjgtoys.cli._base import add_to_set, splitlist

def test_simple():

    p = ArgumentParser()
    p.add_argument('--item',help="Item to add",
        action=add_to_set,type=int)

    args = p.parse_args("--item 1 --item 2 --item 1".split(" "))

    assert args.item == set((1,2))

def split(v):
    return [int(item) for item in v.split(',')]

def test_multi():

    p = ArgumentParser()
    p.add_argument('--item',help="Item(s) to add",
        action=add_to_set,type=split)

    args = p.parse_args("--item 1,2 --item 1".split(" "))

    assert args.item == set((1,2))

def test_multi_split():

    p = ArgumentParser()
    p.add_argument('--item',help="Item(s) to add",
        action=add_to_set,type=splitlist(int))

    args = p.parse_args("--item 1,2 --item 1".split(" "))

    assert args.item == set((1,2))
