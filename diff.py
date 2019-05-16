import diff_match_patch
import time
import re
from subprocess import (Popen, call, PIPE)

dmp = diff_match_patch.diff_match_patch()

def send(text):
    call(['vim', '--remote-send', text])

def expr(text):
    p = Popen(['vim', '--remote-expr', text], stdout=PIPE, stderr=PIPE)
    (output, error) = p.communicate()
    if error:
        print("ERROR! " + error.decode("utf-8"))
        return None
    else:
        return output.decode("utf-8")

def down(lines=1):
    if lines:
        send('%sj' % lines)

def right(count=1):
    if count:
        send('%s<Space>' % count)

def col(pos):
    if pos:
        send('%s|' % pos)

def type(text):
    send('<ESC>i')
    for char in text:
        send(char)
    send('<ESC>')

def cr():
    send("<Esc>:CR<CR>")

def line(pos):
    ret = expr("line(%s)" % pos)
    if ret == None:
        return None
    else:
        return int(ret)

def currentline():
    return line("'.'")

def getline(pos):
    return expr("getline(%s)" % pos)

def getcurrentline():
    return getline("'.'")

def path(text):
    items = text.rstrip().split(" ")
    filename = items[-1]
    depth = len(items)-1
    return (depth, filename)

def expandedfolder(name, pos, depth):
    if re.search(r'/$', name):
        (d2, t2) = path(getline(pos+1))
        if d2 == None:
            return False
        elif d2 > depth:
            return True
        else:
            return False
    else:
        return False

def edit(name):
    send('<Esc>:Explore<cr>')
    send('<Esc><Down><Down><Esc>')

    matchedPath = ""
    descent = 1

    while(True):
        text = getcurrentline()
        pos = currentline()
        (depth, currname) = path(text)
        #print("CHECKING: pos=%s, depth=%s, currname=%s, descent=%s" % (pos, depth, currname, descent))
        if depth == None:
            raise Exception("End of list")

        elif depth < descent:
            raise Exception("Not found")

        if name == matchedPath + currname:
            time.sleep(0.2)
            cr()
            return

        elif re.match(r'^' + matchedPath + currname, name):
            matchedPath += currname
            descent += 1
            if not expandedfolder(currname, pos, depth):
                cr()
        else:
            if expandedfolder(currname, pos, depth):
                cr()

        down()

# this command must be installed, because remote-send doesn't do mappings
# and netrw maps <CR> to something quite mad, with no command to invoke it.
# :command! CR :call feedkeys('<ESC>:<ESC><CR>')
# edit("clojure-diff/README.md")
# edit("test/foo/bar")

def diff(b1, b2):
    diffs = dmp.diff_main(b1, b2)
    dmp.diff_cleanupSemantic(diffs)

    send('<ESC>:set paste<CR>')
    send('gg')

    for (action, text) in diffs:
        print("DIFF: %s - '%s'" % (action, text))
        # input("Press Enter to continue...")
        lines = text.split("\n")
        d = len(lines)-1
        r = len(lines[-1])

        if action == 0:
            if d:
                down(d)
                col(r+1)
            else:
                right(r)
            time.sleep(0.2)

        elif action == 1:
            type(text)
            send('l')

        elif action == -1:
            send('<ESC>v')
            if d:
                down(d)
                col(r)
            else:
                right(r-1)
            time.sleep(0.5)
            send('x')
            time.sleep(0.1)
        else:
            raise Error("EEEEK!")

    send('<ESC>:set nopaste<CR>')
    send(':<CR>')

jabber1 = '''Twas brillig, and the slithy toves
      Did gyre and gimble in the wabe:
All mimsy were the borogoves,
      And the mome raths outgrabe.'''
jabber2 = '''Twas four o'clock and the lithe and slimy badger-lizards
      Turned round and made holes in the grass plot around a sundial:
All flimsy and miserable were the shabby birds,
      And the lost green pigs bellowed.'''

diff("", jabber1)
diff(jabber1, jabber2)
diff(jabber2, jabber1)
diff(jabber1, "")
