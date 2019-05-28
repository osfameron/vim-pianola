import re
from itertools import groupby
from functools import reduce
from operator import itemgetter
from pathlib import Path
import pprint
from colorama import init, Fore, Back, Style

def left(bits, count=1):
    return bits[count:] + ([False] * count)

def right(bits, count=1):
    return ([False] * count) + bits[:-count]

def extend(bits, count):
    ls = range(1, count+1)
    return [any(bit)
            for bit
            in zip(*([bits]
                   + [left(bits, l) for l in ls]
                   + [right(bits, l) for l in ls]))]

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
            return {'leaf': True,
                    'name': name}
        else:
            return {'leaf': False,
                    'name': name,
                    'children': tree([tail for [_, *tail] in paths])}

    branch = [node(name, group)
              for (name, group)
              in groupby(paths, itemgetter(0))]

    branch[-1]['last'] = True  
    return branch

def getTree(items):
    paths = [Path(item).parts for item in items]
    return tree(paths)

def contextSearch(items, predicate, count=1):
    bits = [predicate(item) for item in items]
    context = zip(extend(bits, count), items)

    ellipsis = {'name':"...", 'leaf':True, 'selected':False}
    def aux(pair):
        (selected, group) = pair # bloody PEP3113
        return [item for (_, item) in group] if selected else [ellipsis]

    return flatten(
        [aux(pair) for pair in groupby(context, itemgetter(0))])


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


modified = """src/components/App.js
src/helpers/cartHelper.js""".split("\n")

sourceTree = getTree(items)
targetTree = getTree(modified)

def navigate(tree, key):
    return next((item['children'] for item in tree if item['name'] == key), None)

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
                        Fore.GREEN if selected(item) and item['leaf'] else '',
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
tree = contextTree(sourceTree, targetTree, 2)
pp = pprint.PrettyPrinter(indent=4, depth=6)
printTree(tree)

