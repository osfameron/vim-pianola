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

def tree(paths, level=0):
    """
    Given a list of paths, return a tree like:

        ['file1',
         'file2',
         ('foo', ['file1', 'file2', 'file3'])
         ('bar', ['file1',
                  ('baz': ['file1'])])]

    e.g. a node is either:

        * a file: string)
        * a directory: a tuple of (name, [list of nodes])
    """

    def aux(name, group, level):
        """
        e.g. if we're at level 2 and we have a single path

           [('foo', 'bar', 'baz.txt')]

        then we want to return 'baz.txt'
        """

        (path, *rest) = paths = list(group)
        if not rest and len(path) == level + 1:
        #if (len(path), len(rest)) == (level + 1, 0):
            return path[-1]
        else:
            return (name, tree(paths, level+1))

    return [aux(name, group, level)
            for (name, group)
            in groupby(paths, itemgetter(level))]

def getTree(items):
    paths = [Path(item).parts for item in items]
    return tree(paths)

def contextSearch(items, predicate, count=1):
    bits = [predicate(item) for item in items]
    context = zip(extend(bits, count), items)

    def aux(pair):
        (selected, group) = pair # bloody PEP3113
        return [item for (_, item) in group] if selected else ["..."]

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
src/tests/components/Cart/__snapshots__/CartItem.test.js.snap
src/helpers/cartHelper.js""".split("\n")

sourceTree = getTree(items)
targetTree = getTree(modified)

def isLeaf(item):
    return type(item) == str

def name(item):
    name = item if isLeaf(item) else item[0]
    return name

def navigate(tree, key):
    return next((item[1] for item in tree if name(item) == key), None)

def contextTree(sourceTree, targetTree, c=1):
    pred = lambda item: name(item) in [name(target) for target in targetTree]

    t = contextSearch(sourceTree, pred, c)

    def aux(item):
        node = {'name': name(item),
                'leaf': isLeaf(item),
                'selected': pred(item)}

        if node['selected'] and not node['leaf']:
            node['children'] = contextTree(item[1],
                                           navigate(targetTree, name(item)),
                                           c)
        return node

    branch = [aux(item) for item in t]
    branch[0]['first'] = True  
    branch[-1]['last'] = True  
    return branch

def printTree(tree):
    def nodeName(item):
        return ''.join([Style.BRIGHT if item['selected'] else '',
                        Fore.GREEN if item['selected'] and item['leaf'] else '',
                        item['name'],
                        '' if item['leaf'] else '/'])

    def printAtIndent(indent, text):
        print('   ' * indent, end='')
        print('%-3s' % text, end='')

    def printRoot(root):
        for indent in root:
            printAtIndent(indent, '│')

    def printTreeL(branches, subtree):
        (root, branch) = (branches[:-1], branches[-1])
        for item in subtree:
            printRoot(root)
            if 'last' in item:
                printAtIndent(branch, '└──')
                print(item['name'])
                if 'children' in item:
                    printTreeL(root + [branch + 1], item['children'])
            else:
                printAtIndent(branch, '├──')
                print(item['name'])
                if 'children' in item:
                    printTreeL(root + [branch, 0], item['children'])

    printTreeL([0], tree)

init(autoreset=True)

tree = contextTree(sourceTree, targetTree, 1)
pp = pprint.PrettyPrinter(indent=4, depth=6)
pp.pprint(tree)
print("-----")
printTree(tree)

