#!/usr/bin/env python
"""git-context-tree

Usage:
    git-context-tree [-c <count>] <commit>

Options:
    -c <count>,--context=<count>  Surrounding context [default: 1]
"""

import re
from docopt import docopt
from itertools import groupby
from functools import reduce
from operator import itemgetter
from pathlib import Path
from colorama import init, Fore, Back, Style
from subprocess import PIPE, Popen

def extend(bits, count):
    """
    Given a bitmask, extend the True areas by `count` places.
    e.g.

    [True, False, True, False, False]
            =>
    [True, True, True, True, False] extended by 1
    [True, True, True, True, True] extended by 2
    """
    def left(bits, count=1):
        """ shift bitmask left """
        return bits[count:] + ([False] * count)

    def right(bits, count=1):
        """ shift bitmask right """
        return ([False] * count) + bits[:-count]

    cs = range(1, count+1)

    return [any(pos)
            for pos
            in zip(*([bits]
                   + [left(bits, c) for c in cs]
                   + [right(bits, c) for c in cs]))]

def flatten(parts):
    """Flatten a list of lists by one level"""
    return sum(parts, [])
    # return list(itertools.chain.from_iterable(parts)) # seriously?

head = itemgetter(0)

def tree(paths):
    """
    Given a list of paths, return a tree with nodes like:
        {'leaf': False, 'name': '...', 'children': ...}
    """

    def node(name, group):
        """
        e.g. if we're a single node path:

           [('baz.txt')]

        then we want to return a leaf node with that path, otherwise a path
        with children.
        """

        (path, *_) = paths = list(group)
        if len(paths) == 1 and len(path) == 1:
            return path[0]
        else:
            return {'leaf': False,
                    'name': name,
                    'children': tree([tail for [_, *tail] in paths])}

    branch = [node(name, group)
              for (name, group)
              in groupby(paths, head)]

    return branch

def getTree(paths, fn):
    """
    Given a list of string paths, return a tree with all routes through
    """
    def pathToList(path):
        node = fn(path)
        pathList = list(Path(node['path']).parts)
        pathList[-1] = {"name": pathList[-1],
                        "leaf": True,
                        **node}
        return pathList

    return tree([pathToList(path) for path in paths])

def contextSearch(items, predicate, count=1):
    bits = [predicate(item) for item in items]
    context = zip(extend(bits, count), items)

    def ellipsis():
        """show a ... line for elided items, if context requested"""
        if count:
            return [{'name':"...", 'leaf':True, 'selected':False}]
        else:
            return []

    def aux(pair):
        (selected, group) = pair # bloody PEP3113
        return [item for (_, item) in group] if selected else ellipsis()

    return flatten(
        [aux(pair) for pair in groupby(context, head)])


def pathOnly(line):
    return {"path": line}

def pathStatus(line):
    (mode, path) = re.split('\s', line, maxsplit=1)
    return {"path": path,
            "mode": mode}

def navigate(tree, key):
    return next((item['children'] for item in tree if item['name'] == key), None)

def mergeTree(fs, ts):
    if not ts:
        return fs
    elif not fs:
        return ts

    ((f,*fs2), (t,*ts2)) = (fs, ts)
    if f['name'] == t['name']:
        if t['leaf']:
            return [t] + mergeTree(fs2, ts2)
        else:
            return [{**t, 'children': mergeTree(f['children'], t['children'])}] \
                   + mergeTree(fs2, ts2)
    elif f['name'] > t['name']:
        return [t] + mergeTree(fs, ts2)
    elif t['name'] > f['name']:
        return [f] + mergeTree(fs2, ts)
    else:
        raise Exception('eeek')

def contextTree(sourceTree, targetTree, c=1):
    pred = lambda node: node['name'] in [target['name'] for target in targetTree]

    t = contextSearch(sourceTree, pred, c)

    def aux(node):
        node['selected'] = pred(node)

        if not node['leaf']:
            if node['selected']:
                node['children'] = contextTree(
                                       node['children'],
                                       navigate(targetTree, node['name']),
                                       c)
            else:
                del node['children'] 

        return node

    branch = [aux(item) for item in t]
    branch[-1]['last'] = True
    return branch

def selected(node):
    return node.get('selected', False)

def printTree(tree):

    def colour(item):
        if 'mode' in item:
            return {'A': Fore.GREEN,
                    'M': Fore.BLUE,
                    'D': Fore.RED}.get(item['mode'], '')
        else:
            return ''

    def mode(item):
        if 'mode' in item:
            return '%s ' % item['mode']
        else:
            return ''

    def nodeName(item):
        return ''.join([Style.BRIGHT if selected(item) else '',
                        colour(item),
                        mode(item),
                        item['name'],
                        '' if item['leaf'] else '/'])

    def printAtIndent(indent, text):
        print('    ' * indent, end='')
        print('%-4s' % text, end='')

    def printRoot(root):
        for indent in root:
            printAtIndent(indent, '│')

    def printTreeL(branches, subtree):
        (root, branch) = (branches[:-1], branches[-1])
        for item in subtree:
            printRoot(root)
            if 'last' in item:
                printAtIndent(branch, '└──')
                print(nodeName(item))
                if 'children' in item:
                    printTreeL(root + [branch + 1], item['children'])
            else:
                printAtIndent(branch, '├──')
                print(nodeName(item))
                if 'children' in item:
                    printTreeL(root + [branch, 0], item['children'])

    init(autoreset=True)
    printTreeL([0], tree)

def run(command):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    (output, error) = p.communicate()
    return output.decode('utf-8').rstrip().split('\n')

def sourceFiles(commit):
    return run(['git', 'ls-tree',
                       '-r',
                       '--name-only',
                       commit])

def targetFiles(commit):
    return run(['git', 'diff-tree',
                       '--no-commit-id',
                       '--name-status',
                       '-r',
                       commit])

if __name__ == '__main__':
    arguments = docopt(__doc__, version='git context-tree 0.1')

    commit = arguments['<commit>']
    context = int(arguments['--context'])

    source = sourceFiles(commit)
    target = targetFiles(commit)

    sourceTree = getTree(source, pathOnly)
    targetTree = getTree(target, pathStatus)

    tree = contextTree(mergeTree(sourceTree, targetTree), targetTree, context)

    printTree(tree)

