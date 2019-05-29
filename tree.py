import re
from itertools import groupby
from functools import reduce
from operator import itemgetter
from pathlib import Path
import pprint
from colorama import init, Fore, Back, Style

head = itemgetter(0)

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
    return sum(parts, [])
    # return list(itertools.chain.from_iterable(parts)) # seriously?

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

    ellipsis = {'name':"...", 'leaf':True, 'selected':False}
    def aux(pair):
        (selected, group) = pair # bloody PEP3113
        return [item for (_, item) in group] if selected else [ellipsis]

    return flatten(
        [aux(pair) for pair in groupby(context, head)])


items=""".gitignore
README.md
_config.yml
docs/README.md
docs/_config.yml
docs/resources/app_preview.png
docs/resources/cart_item_preview.png
docs/resources/cart_preview.png
docs/resources/cart_totals_preview.png
docs/resources/menu_header_preview.png
docs/resources/menu_item_preview.png
docs/resources/menu_preview.png
docs/resources/menu_section_closed_preview.png
docs/resources/menu_section_open_preview.png
package.json
public/index.html
src/assets/data.json
src/assets/styles.css
src/components/App.js
src/components/Cart/CartItem.js
src/components/Cart/CartTotals.js
src/components/Cart/index.js
src/components/Menu/MenuHeader.js
src/components/Menu/MenuItem.js
src/components/Menu/MenuSection.js
src/components/Menu/index.js
src/helpers/cartHelper.js
src/helpers/menuHelper.js
src/index.js
src/setupTests.js
src/templates/cart/cart.html
src/templates/cart/cartItem.html
src/templates/cart/cartTotals.html
src/templates/index.html
src/templates/menu/menu.html
src/templates/menu/menuHeader.html
src/templates/menu/menuItem.html
src/templates/menu/menuSection.html
src/tests/components/Cart/CartItem.test.js
src/tests/components/Cart/CartTotals.test.js
src/tests/components/Cart/__snapshots__/CartItem.test.js.snap
src/tests/components/Cart/__snapshots__/CartTotals.test.js.snap
src/tests/components/Cart/__snapshots__/index.test.js.snap
src/tests/components/Cart/index.test.js
src/tests/components/Menu/MenuHeader.test.js
src/tests/components/Menu/MenuItem.test.js
src/tests/components/Menu/MenuSection.test.js
src/tests/components/Menu/__snapshots__/MenuHeader.test.js.snap
src/tests/components/Menu/__snapshots__/MenuItem.test.js.snap
src/tests/components/Menu/__snapshots__/MenuSection.test.js.snap
src/tests/components/Menu/__snapshots__/index.test.js.snap
src/tests/components/Menu/index.test.js
src/tests/containers/App.test.js
src/tests/data/mockData.json
src/tests/helpers/cartHelper.test.js
src/tests/helpers/menuHelper.test.js""".split("\n")


modified = """A src/components/App.js
M src/helpers/cartHelper.js""".split("\n")

def pathOnly(line):
    return {"path": line}

def pathStatus(line):
    (mode, path) = line.split(' ', 1)
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

targetTree = getTree(modified, pathStatus)
sourceTree = getTree(items, pathOnly)

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
    def nodeName(item):
        return ''.join([Style.BRIGHT if selected(item) else '',
                        Fore.GREEN if 'mode' in item and item['mode'] == 'A' else '',
                        Fore.BLUE if 'mode' in item and item['mode'] == 'M' else '',
                        # Fore.GREEN if selected(item) and item['leaf'] else '',
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

    printTreeL([0], tree)

init(autoreset=True)

print()
tree = contextTree(mergeTree(sourceTree, targetTree), targetTree, 2)
pp = pprint.PrettyPrinter(indent=4, depth=6)
printTree(tree)

