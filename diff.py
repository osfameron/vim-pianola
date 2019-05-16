import diff_match_patch
import time
import re
from subprocess import (Popen, call, PIPE)

dmp = diff_match_patch.diff_match_patch()

class Vim:
    def send(cls, text):
        call(['vim', '--remote-send', text])

    def expr(cls, text):
        p = Popen(['vim', '--remote-expr', text], stdout=PIPE, stderr=PIPE)
        (output, error) = p.communicate()
        if error:
            print("ERROR! " + error.decode("utf-8"))
            return None
        else:
            return output.decode("utf-8")

    def down(cls, lines=1):
        if lines:
            cls.send('%sj' % lines)

    def right(cls, count=1):
        if count:
            cls.send('%s<Space>' % count)

    def gotocol(cls, pos):
        if pos:
            cls.send('%s|' % pos)

    def type(cls, text):
        cls.send('<ESC>i')
        for char in text:
            cls.send(char)
        cls.send('<ESC>')

    def cr(cls):
        cls.send("<Esc>:CR<CR>")

    def line(cls, pos):
        ret = cls.expr("line(%s)" % pos)
        if ret == None:
            return None
        else:
            return int(ret)

    def currentline(cls):
        return cls.line("'.'")

    def col(cls, pos):
        ret = cls.expr("col(%s)" % pos)
        if ret == None:
            return None
        else:
            return int(ret)

    def currentcol(cls):
        return cls.col("'.'")

    def getline(cls, pos):
        return cls.expr("getline(%s)" % pos)

    def getcurrentline(cls):
        return cls.getline("'.'")

    def path(cls, text):
        items = text.rstrip().split(" ")
        filename = items[-1]
        depth = len(items)-1
        return (depth, filename)

    def expandedfolder(cls, name, pos, depth):
        if re.search(r'/$', name):
            (d2, t2) = cls.path(getline(pos+1))
            if d2 == None:
                return False
            elif d2 > depth:
                return True
            else:
                return False
        else:
            return False

    def edit(cls, name):
        cls.send('<Esc>:Explore<cr>')
        cls.send('<Esc><Down><Down><Esc>')

        matchedPath = ""
        descent = 1

        while(True):
            text = getcurrentline()
            pos = currentline()
            (depth, currname) = cls.path(text)
            #print("CHECKING: pos=%s, depth=%s, currname=%s, descent=%s" % (pos, depth, currname, descent))
            if depth == None:
                raise Exception("End of list")

            elif depth < descent:
                raise Exception("Not found")

            if name == matchedPath + currname:
                time.sleep(0.2)
                cls.cr()
                return

            elif re.match(r'^' + matchedPath + currname, name):
                matchedPath += currname
                descent += 1
                if not expandedfolder(currname, pos, depth):
                    cls.cr()
            else:
                if expandedfolder(currname, pos, depth):
                    cls.cr()

            cls.down()

    def select(cls, d, r):
        cls.send('<ESC>v')
        if d:
            cls.down(d)
            cls.gotocol(r)
        else:
            cls.right(r-1)

    def delete(cls):
        cls.send('x')

    def start(cls):
        cls.send('<ESC>:set paste<CR>')
        cls.send('gg')

    def end(cls):
        cls.send('<ESC>:set nopaste<CR>')
        cls.send(':<CR>')

    # this command must be installed, because remote-send doesn't do mappings
    # and netrw maps <CR> to something quite mad, with no command to invoke it.
    # :command! CR :call feedkeys('<ESC>:<ESC><CR>')
    # edit("clojure-diff/README.md")
    # edit("test/foo/bar")

def diff(driver, b1, b2):
    diffs = dmp.diff_main(b1, b2)
    # dmp.diff_cleanupSemantic(diffs)
    dmp.diff_cleanupEfficiency(diffs)

    driver.start()

    for (action, text) in diffs:
        print("DIFF: %s - '%s'" % (action, text))
        # input("Press Enter to continue...")
        lines = text.split("\n")
        d = len(lines)-1
        r = len(lines[-1])

        if action == 0:
            if d:
                driver.down(d)
                driver.gotocol(r+1)
            else:
                driver.right(r)
            time.sleep(0.2)

        elif action == 1:
            driver.type(text)
            driver.right()

        elif action == -1:
            driver.select(d, r)
            time.sleep(0.5)
            driver.delete()
            time.sleep(0.1)

        else:
            raise Error("EEEEK!")

    driver.end()

jabber1 = '''Twas brillig, and the slithy toves
      Did gyre and gimble in the wabe:
All mimsy were the borogoves,
      And the mome raths outgrabe.'''
jabber2 = '''It was four o'clock and the lithe and slimy badger-lizards
      Turned round and made holes in the grass plot around a sundial:
All flimsy and miserable were the shabby birds,
      And the lost green pigs bellowed.'''

driver = Vim()

diff(driver, "", jabber1)
diff(driver, jabber1, jabber2)
diff(driver, jabber2, jabber1)
diff(driver, jabber1, "")
