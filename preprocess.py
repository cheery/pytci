import tokenize

def chomp(state):
    token = state.next_token()
    while token is not None:
        if name_of(token) == "macro":
            identifier = state.expect('identifier')
            macro_process(state, value_of(identifier))
        elif state.processing:
            yield token
        token = state.next_token()

def macro_process(state, name):
    if name == 'ifndef':
        macro_name = value_of(state.expect('identifier'))
        assert state.macro_end(), "were supposed to end here"
        state.stack.append(state.processing)
        if state.processing:
            state.processing = macro_name not in state.env
        print '+ processing =', state.processing
    elif name == 'ifdef':
        macro_name = value_of(state.expect('identifier'))
        assert state.macro_end(), "were supposed to end here"
        state.stack.append(state.processing)
        if state.processing:
            state.processing = macro_name in state.env
        print '+ processing =', state.processing
    elif name == 'if':
        state.stack.append(state.processing)
        if state.processing:
            state.processing = macro_expression(state)
        else:
            state.macro_record()
        assert state.macro_end(), "were supposed to end here"
    elif name == 'elif':
        if state.processing:
            state.processing = False
            state.macro_record()
        else:
            state.processing = macro_expression(state)
        assert state.macro_end(), "were supposed to end here"
    elif name == 'endif':
        assert state.macro_end(), "were supposed to end here"
        state.suppressed = stream.stack.pop(-1)
        print '- processing =', state.suppressed
    elif name == 'define':
        macro_name = value_of(state.expect('identifier'))
        if state.processing:
            state.stream.skip_spaces()
            assert state.stream.character != '(', "parametric macros not implemented"
            state.env[macro_name] = state.macro_record()
        else:
            state.macro_record()
    elif name == 'undef':
        macro_name = value_of(state.expect('identifier'))
        assert state.macro_end(), "were supposed to end here"
        if state.processing and macro_name in state.env:
            state.env.pop(macro_name)
    elif name == 'error':
        if state.processing:
            assert False, "error occurred, but error printing not implemented in pytci"
        state.macro_record()
    elif name == 'else':
        assert state.macro_end(), "were supposed to end here"
        state.processing = not state.processing
    elif name == 'include':
        assert False, "include needs to be implemented first"
    elif name == 'line':
        line = int(value_of(state.expect('number')))
        filename = value_of(state.expect('string'))
        assert state.macro_end(), "were supposed to end here"
        state.stream.line = line
        state.stream.filename = filename
    else:
        assert False, name

def macro_expression(state):
    assert False, "macro expressions not present yet"
    # Integer constants.
    # Character constants, which are interpreted as they would be in normal code.
    # Arithmetic operators for addition, subtraction, multiplication, division,
    # bitwise operations, shifts, comparisons, and logical operations (&& and ||).
    # The latter two obey the usual short-circuiting rules of standard C.
    # Macros. All macros in the expression are expanded before
    # actual computation of the expression's value begins.
    # Uses of the defined operator, which lets you check whether macros are defined in the middle of an #if.
    # Identifiers that are not macros, which are all considered to be the number zero.
    #   This allows you to write #if MACRO instead of #ifdef MACRO, if you know that MACRO,
    #   when defined, will always have a nonzero value. Function-like macros used without
    #   their function call parentheses are also treated as zero.

def name_of(token):
    return token[1]

def value_of(token):
    return token[2]

class PreprocessorState(object):
    def __init__(self, stream, env, processing=True):
        self.stream = stream
        self.env = env
        self.processing = processing
        self.stack = []
        self.macroexpansion = []

    def next_token(self):
        if len(self.macroexpansion) == 0:
            token = tokenize.chop(self.stream)
            print 'read token', token
        else:
            token = self.macroexpansion.pop(0)
            print 'macroexpand token', token
        return token

    def expect(self, name):
        token = self.next_token()
        assert name_of(token) == name, "'expected' error message not implemented"
        return token

    def macro_end(self):
        if len(self.macroexpansion) == 0:
            self.stream.skip_spaces()
            return self.stream.character in ('', '\n')
        return False

    def macro_record(self):
        sequence = []
        while not state.macro_end():
            sequence.append(state.next_token())
        return sequence

if False:
    import character_stream
    pull = character_stream.pull
    def new_pull(x):
        ch = pull(x)
        print "read character:", repr(ch)
        return ch
    character_stream.pull = new_pull

if __name__=='__main__':
    import trigraphs, traceback
    from character_stream import CharacterStream

    def main():
        env = {}
        filename = "/usr/include/stdio.h"
        with open(filename, 'r') as fd:
            contents = fd.read()
        stream = CharacterStream(trigraphs.translate(contents), 1, filename)
        state = PreprocessorState(stream, env)
        try:
            for token in chomp(state):
                print token
        except AssertionError as ass:
            traceback.print_exc()
            for x in range(5):
                print tokenize.chop(stream)
    main()
