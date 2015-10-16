"""
    The one of the most beloved features of C/C++.
    https://en.wikipedia.org/wiki/Digraphs_and_trigraphs#C

    If trigraphs are used, like they usually are,
    it is put before the character stream.
"""

trigraphs = { "=":"#", "/":"\\", "(":"[", ")":"]", "!":"|", "<":"{", ">":"}", "-":"~" }

def translate(sequence):
    k = 0
    for ch in sequence:
        if ch == '?' and k < 2:
            k += 1
        elif ch == '?':
            yield '?'
        elif k == 2 and ch in trigraphs:
            yield trigraphs[ch]
            k = 0
        else:
            for _ in range(k):
                yield '?'
            yield ch
            k = 0
    for _ in range(k):
        yield '?'

if __name__=='__main__':
    test = "// Will the next line be executed????????????????/\na++;\n/??/\n* A comment *??/\n/"
    print ''.join(translate(test))
