"""
    The one of the most beloved features of C/C++.
    https://en.wikipedia.org/wiki/Digraphs_and_trigraphs#C

    If trigraphs are used, like they usually are,
    it is put before the character stream.
"""

trigraphs = {
    "=": "#",
    "/": "\\",
    "(": "[",
    ")": "]",
    "!": "|",
    "<": "{",
    ">": "}",
    "-": "~",
}

def translate(sequence):
    k = 0
    for ch in sequence:
        if k == 0:
            if ch != '?':
                yield ch
            else:
                k = 1
            continue
        elif k == 1:
            if ch != '?':
                yield '?'
                yield ch
                k = 0
            else:
                k = 2
            continue
        else:
            k = 0
            if ch in trigraphs:
                yield trigraphs[ch]
                continue
            elif ch == '?':
                k = 2
                yield '?'
            else:
                yield '?'
                yield '?'
                yield ch
    for _ in xrange(k):
        yield '?'

if __name__ == '__main__':
    test = "// Will the next line be executed????????????????/\na++;\n/??/\n* A comment *??/\n/"
    print ''.join(translate(test))
