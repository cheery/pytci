import tokenize, operator

macro_list = {}

def chomp(state, with_defined=False):
    token = state.next_expanded_token()
    while token is not None:
        if name_of(token) == "macro":
            for token in run_macro(state):
                yield token
        elif state.processing:
            yield token
        token = state.next_expanded_token()

def run_macro(state):
    identifier = state.expect('identifier')
    macro_name = value_of(identifier)
    if macro_name in macro_list:
        for token in macro_list[macro_name](state, position_of(identifier)):
            yield token
        assert state.macro_end(), "{1}: {0}: macro is expected to end".format(*position_of(identifier))
    else:
        assert False, "Macro {!r} not implemented".format(macro_name)

def pump_token(macro_stack, macro_queue, current, passthrough):
    if isinstance(current, list): # an expansion.
        for current in current:
            pump_token(macro_stack, macro_queue, current, passthrough)
    elif len(macro_stack) > 0:
        if macro_stack[-1].pump(current):
            macro_queue.extend(macro_stack.pop(-1).invoke())
    else:
        passthrough.append(current)

def pull_identifier(state):
    token = state.next_token()
    if token and value_of(token) == '(':
        token = state.next_token()
        stop = state.next_token()
        assert stop and value_of(stop) == ')', "bonked 'defined'"
    assert token and name_of(token) == 'identifier', "bonked 'defined'"
    return token

class CallBuilder(object):
    def __init__(self, position, expansion): # at this point '(' has been processed.
        self.position = position
        self.expansion = expansion
        self.bumps = 0
        self.bags = []
        self.bag = []
        self.toco = 0

    def pump(self, token):
        value = value_of(token)
        if value == ',' and self.bumps == 0:
            self.bags.append(self.bag)
            self.bag = []
        if value == '(':
            self.bumps += 1
        if value == ')':
            if self.bumps == 0:
                return True
            self.bumps -= 1
        self.bag.append(token)
        return False

    def invoke(self):
        if self.toco > 1: # only if there were nonzero arguments.
            self.bags.append(self.bag)
        return self.expansion(self.position, self.bags)

def process_define(state, position):
    macro_name = value_of(state.expect('identifier'))
    macro_func = (state.stream.character == '(')
    macro_stream = state.macro_stream()
    if state.processing:
        if macro_func: # TODO: warn if macro is redefined
            state.env[macro_name] = parse_macro_function(macro_stream)
        else:
            state.env[macro_name] = list(macro_stream)
    return ()

def process_undef(state, position):
    macro_name = value_of(state.expect('identifier'))
    if state.processing and macro_name in state.env:
        state.env.pop(macro_name)
    return ()

def process_if(state, position):
    state.stack.append((state.processing, state.processing_inside))
    state.processing_inside = 'cond-done'
    macro_stream = state.hacked_macro_expansion()
    if state.processing:
        state.processing = bool(state.macroeval(state, macro_stream))
        state.processing_inside = ('cond', 'cond-done')[state.processing]
    return ()

def process_elif(state, position):
    macro_stream = state.hacked_macro_expansion()
    if state.processing_inside == 'cond':
        state.processing = state.macroeval(state, macro_stream)
        state.processing_inside = ('cond', 'cond-done')[state.processing]
    elif state.processing_inside == 'cond-done':
        state.processing = False
    else:
        assert False, "{1}: {0}: #elif at toplevel".format(*position)
    return ()

def process_else(state, position):
    if state.processing_inside == 'cond':
        state.processing = True
    elif state.processing_inside == 'cond-done':
        state.processing = False
    else:
        assert False, "{2}: {1}: #else at {0}".format(state.processing_inside, *position)
    state.processing_inside = 'else-block'
    return ()

def process_ifdef(state, position):
    state.stack.append((state.processing, state.processing_inside))
    state.processing_inside = 'cond-done'
    macro_name = value_of(state.expect('identifier'))
    if state.processing:
        state.processing = macro_name in state.env
        state.processing_inside = ('cond', 'cond-done')[state.processing]
    return ()

def process_ifndef(state, position):
    state.stack.append((state.processing, state.processing_inside))
    state.processing_inside = 'cond-done'
    macro_name = value_of(state.expect('identifier'))
    if state.processing:
        state.processing = macro_name not in state.env
        state.processing_inside = ('cond', 'cond-done')[state.processing]
    return ()

def process_endif(state, position):
    assert len(state.stack) > 0, "{1}: {0}: excess endif".format(*position)
    state.processing, state.processing_inside = state.stack.pop(-1)
    return ()

# This error handling is bit weird. The idea is
# that you could generate stubs instead of halting the compiler.
def process_error(state, position):
    macro_stream = state.macro_stream()
    if state.processing:
        message = ' '.join(map(value_of, macro_stream))
        return [tokenize.token(position, 'error', message)]
    return ()

def process_line(state, position):
    line = int(value_of(state.expect('number')))
    filename = value_of(state.expect('string'))
    state.stream.skip_spaces()
    state.stream.line = line
    state.stream.filename = filename
    return ()

def process_include(state, position):
    if state.macro_end():
        assert len(state.stack) > 0, "{1}: {0}: malformed include".format(*position)
    token = state.next_token()
    if name_of(token) == 'string':
        if state.processing:
            return state.include(state, position, value_of(token), True)
    else:
        assert value_of(token) == '<', "{1}: {0}: malformed include".format(*position)
        string = ""
        while state.stream.character not in ('>', '', '\n'):
            string += state.stream.get_next()
        assert state.stream.get_next() == '>', "{1}: {0}: malformed include".format(*position)
        if state.processing:
            return state.include(state, position, string, False)
    return ()

def _init_itself():
    for name, value in globals().iteritems():
        if name.startswith('process_'):
            macro_name = name.split('_', 1)[1]
            macro_list[macro_name] = value
_init_itself()

# ? - badly implemented, ! - no implementation
#? Integer constants.
#? Character constants, which are interpreted as they would be in normal code.
#? Arithmetic operators for addition, subtraction, multiplication, division,
#?? bitwise operations, shifts, comparisons, and logical operations (&& and ||).
#! The latter two obey the usual short-circuiting rules of standard C.
#  Macros. All macros in the expression are expanded before
#  actual computation of the expression's value begins.
# Uses of the defined operator, which lets you check whether macros are defined in the middle of an #if.
# Identifiers that are not macros, which are all considered to be the number zero.
#   This allows you to write #if MACRO instead of #ifdef MACRO, if you know that MACRO,
#   when defined, will always have a nonzero value. Function-like macros used without
#   their function call parentheses are also treated as zero.
def default_macroeval(state, sequence):
    context = []
    value_stack = []
    operator_stack = []
    def flip(precedence):
        while len(operator_stack) > 0 and quick_precedence_table[operator_stack[-1]] >= precedence:
            op = operator_stack.pop(-1)
            argc, fn = quick_operator_table[op]
            value_stack[-argc:] = [fn(*value_stack[-argc:])]
    for token in sequence:
        if value_of(token) in quick_precedence_table:
            flip(quick_precedence_table[value_of(token)])
            operator_stack.append(value_of(token))
        elif value_of(token) == '(':
            context.append((value_stack, operator_stack))
            value_stack = []
            operator_stack = []
        elif value_of(token) == ')':
            flip(0)
            assert len(value_stack) == 1, "lol?"
            vs, operator_stack = context.pop(-1)
            value_stack = vs + value_stack
        elif name_of(token) == 'number':
            if '.' in value_of(token):
                value_stack.append(float(value_of(token)))
            elif value_of(token).startswith('0x') or value_of(token).startswith('0X'):
                value_stack.append(long(value_of(token).rstrip('L'), 16))
            else:
                value_stack.append(long(value_of(token).rstrip('L')))
            flip(150)
        elif name_of(token) in ('char', 'string'):
            value_stack.append(value_of(token))
            flip(150)
        elif name_of(token) == 'identifier':
            value_stack.append(0)
        else:
            assert False, "Not sure how to macro-evaluate: {}".format(token)
    flip(0)
    if len(value_stack) == 1 and len(context) == 0:
        return value_stack[0]
    assert False, (value_stack + list(reversed(operator_stack)))

quick_operator_table = {
    '!':(1, operator.not_),
    '*':(2, operator.mul), '/':(2, operator.div), '%':(2, operator.mod),
    '+':(2, operator.add), '-':(2, operator.sub),
    '<<':(2, operator.lshift), '>>':(2, operator.rshift),
    '<':(2, operator.lt), '<=':(2, operator.le), '>':(2, operator.gt), '>=':(2, operator.ge),
    '==':(2, operator.eq), '!=':(2, operator.ne),
    '&':(2, operator.and_), '^':(2, operator.xor), '|':(2, operator.or_),
    '&&':(2, (lambda x, y: x and y)), '||':(2, (lambda x, y: x or y)),

}
quick_precedence_table = {
    '!':200,
    '*':100, '/':100, '%':100,
    '+':80, '-':80,
    '<<':70, '>>':70,
    '<':60, '<=':60, '>':60, '>=':60,
    '==':50, '!=':50,
    '&':40, '^':35, '|':30, '&&':25, '||':20,
}

class BaseContext(object):
    def __init__(self, parent, stream, shadow):
        self.parent = parent
        self.stream = stream
        self.shadow = shadow
        self.variables = ()
        self.exhausted = False

    def next_token(self):
        token = tokenize.chop(self.stream)
        if token is None:
            self.exhausted = True
        return token
    
    def macro_concat(self):
        return False

    def macro_end(self):
        self.stream.skip_spaces()
        return self.stream.character in ('', '\n')

    def macro_func(self):
        self.stream.skip_spaces_and_newlines()
        return self.stream.character == '('

class ExpandContext(object):
    def __init__(self, parent, stream, shadow, variables=()):
        self.parent = parent
        self.stream = stream
        self.shadow = shadow
        self.variables = variables
        try:
            self.exhausted = False
            self.lookahead = stream.next()
        except StopIteration as stop:
            self.exhausted = True
            self.lookahead = None

    def next_token(self):
        token = self.lookahead
        try:
            self.exhausted = False
            self.lookahead = self.stream.next()
        except StopIteration as stop:
            self.exhausted = True
            self.lookahead = None
        assert token is not None, "over fetch"
        return token

    def macro_concat(self):
        return self.lookahead and value_of(self.lookahead) == '##'

    def macro_end(self):
        return False

    def macro_func(self):
        assert not self.exhausted
        return value_of(self.lookahead) == '('

class ExpandedContext(ExpandContext):
    pass

class PreprocessorState(object):
    def __init__(self, stream, env, include_chain=(), include=(), macroeval=default_macroeval, processing=True, processing_inside='toplevel'):
        self.stream = stream
        self.env = env
        self.include_chain = include_chain
        self.include = include
        self.macroeval = macroeval
        self.processing = processing
        self.processing_inside = processing_inside
        self.stack = []
        self.context = BaseContext(None, stream, ())

    def pump_context(self):
        while self.context and self.context.exhausted:
            self.context = self.context.parent

    def next_token(self):
        token = self.context.next_token()
        self.pump_context()
        return token

    def next_expanded_token(self, with_defined=False):
        context = self.context
        token = self.next_token()
        if self.context and self.context.macro_concat():
            self.next_token()
            assert self.context == context, "Catenate should stick within context"
            other = self.expect('identifier')
            return catenate_tokens(token, other, context.variables)
        if isinstance(context, ExpandedContext):
            return token
        if with_defined and token and value_of(token) == 'defined':
            token = self.next_token()
            if token and value_of(token) == '(':
                token = self.expect('identifier')
                rp = self.next_token()
                assert rp and value_of(rp) == ')', "expected right parenthesis in 'defined'"
            return tokenize.token(position_of(token), "number", ["0", "1"][value_of(token) in self.env])
        if token and value_of(token) == '#' and isinstance(context, ExpandContext) and context == self.context:
            ntoken = self.next_token()
            if value_of(ntoken) in context.variables:
                return tokenize.token(position_of(ntoken), "string", stringify(context.variables[value_of(ntoken)]))
            else:
                assert False, "'#' outside proper context"
        if token and name_of(token) == 'identifier':
            value = value_of(token)
            if value in context.shadow:
                return token
            if value in context.variables:
                self.context = ExpandedContext(self.context, iter(context.variables[value]), ())
                self.pump_context()
                return self.next_expanded_token()
            expansion = self.env.get(value)
            if expansion is None:
                return token
            elif callable(expansion) and self.context and self.context.macro_func():
                args = self.next_macro_call()
                self.context = expansion(self.context, context.shadow + (value,), position_of(token), args)
                self.pump_context()
                return self.next_expanded_token()
            else:
                self.context = ExpandContext(self.context, iter(expansion), context.shadow + (value,))
                self.pump_context()
                return self.next_expanded_token()
        return token

    def next_macro_call(self):
        begin = self.next_token()
        assert value_of(begin) == '(', "broken preprocessor"
        token = self.next_expanded_token()
        if token and value_of(token) == ')':
            return []
        bag = []
        args = [bag]
        while token and value_of(token) != ')':
            if value_of(token) == '(':
                bag.extend(self.grouped_tokens(token))
            elif value_of(token) == ',':
                bag = []
                args.append(bag)
            else:
                bag.append(token)
            token = self.next_expanded_token()
        if token and value_of(token) == ')':
            return args
        assert False, "{1}: {0}: nonterminated macro call".format(position_of(begin))

    def grouped_tokens(self, token):
        yield token
        token = self.next_expanded_token()
        while token and value_of(token) != ')':
            if value_of(token) == '(':
                for subtoken in self.grouped_tokens(token):
                    yield subtoken
            else:
                yield token
            token = self.next_expanded_token()
        if token and value_of(token) == ')':
            yield token
        else:
            assert False, "{1}: {0}: nonterminated preprocessed group".format(position_of(begin))

    def expect(self, name):
        token = self.next_token()
        assert name_of(token) == name, "'expected' error message not implemented: {} got {}".format(name, token)
        return token

    def macro_end(self):
        self.pump_context()
        if self.context is None:
            return True
        return self.context.macro_end()

    def macro_stream(self):
        sequence = []
        while not self.macro_end():
            sequence.append(self.next_token())
        return MacroStream(iter(sequence))

    def hacked_macro_expansion(self):
        sequence = []
        while not self.macro_end():
            sequence.append(self.next_token())
        original_context = self.context
        self.context = ExpandContext(None, iter(sequence), original_context.shadow)
        sequence = []
        while self.context is not None:
            sequence.append(self.next_expanded_token(with_defined=True))
        self.context = original_context
        return MacroStream(iter(sequence))

    def fork(self, stream, filename):
        include_chain = self.include_chain + (filename,)
        return self.__class__(stream, self.env, include_chain,
                include=self.include, macroeval=self.macroeval)

class MacroStream(object):
    def __init__(self, generator):
        self.generator = generator

    def next_token(self):
        try:
            return self.generator.next()
        except StopIteration as stop:
            return None

    def __iter__(self):
        return self.generator

def parse_macro_function(stream):
    lp = stream.next_token()
    assert value_of(lp) == '(', "broken preprocessor"
    bind = []
    is_variadic = False
    current = stream.next_token()
    while current and value_of(current) != ')':
        if value_of(current) == '...':
            is_variadic = True
            break
        bind.append(value_of(current))
        current = stream.next_token()
        if not current or value_of(current) != ",":
            break
        current = stream.next_token()
    assert current and value_of(current) == ')', "{1}: {0}: unterminated argument list error".format(position_of(lp))
    return MacroFunction(bind, is_variadic, list(stream))

class MacroFunction(object):
    def __init__(self, bind, is_variadic, body):
        self.bind = bind
        self.is_variadic = is_variadic
        self.body = body

    def __call__(self, context, shadow, position, args):
        if self.is_variadic:
            assert len(args) >= len(self.bind), "argument error, error not implemented. {} -> {} ({})".format(position, self.bind, args)
        else:
            assert len(args) == len(self.bind), "argument error, error not implemented. {} -> {} ({})".format(position, self.bind, args)
        variables = dict(zip(self.bind, args))
        if self.is_variadic:
            variables['...'] = args[len(self.bind):]
        return ExpandContext(context, iter(self.body), shadow, variables)

def position_of(token):
    return token[0]

def name_of(token):
    return token[1]

def value_of(token):
    return token[2]

def stringify(tokens):
    return ' '.join(map(value_of, tokens))

def catenate_tokens(lhs, rhs, variables):
    position = position_of(lhs)
    if value_of(lhs) in variables:
        lhs = variables[value_of(lhs)]
        assert len(lhs) <= 1, "rare case for catenation"
    else:
        lhs = [lhs]
    if value_of(rhs) in variables:
        rhs = variables[value_of(rhs)]
        assert len(rhs) <= 1, "rare case for catenation"
    else:
        rhs = [rhs]
    return tokenize.token(position, 'identifier', ''.join(map(value_of, lhs + rhs)))

if False:
    import character_stream
    pull = character_stream.pull
    def new_pull(x):
        ch = pull(x)
        print "read character:", repr(ch)
        return ch
    character_stream.pull = new_pull

if __name__=='__main__':
    import trigraphs, traceback, os, sys
    from character_stream import CharacterStream

    local_includes = []
    global_includes = ['/usr/lib/gcc/x86_64-linux-gnu/4.8/include', '/usr/local/include', '/usr/lib/gcc/x86_64-linux-gnu/4.8/include-fixed', '/usr/include/x86_64-linux-gnu', '/usr/include']

    def include_stub(state, position, name, local):
        if local:
            includes = [os.path.dirname(state.include_chain[-1])] + local_includes
        else:
            includes = global_includes
        filename = name
        for dirname in includes:
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                filename = path
                break
        else:
            return [] # incorrect, but lets lol later.
        if filename in state.include_chain:
            print "{1}: {0}: cyclic include: ".format(*position) + filename
            return [] # incorrect again
        with open(filename, 'r') as fd:
            contents = fd.read()
        stream = CharacterStream(trigraphs.translate(contents), 1, filename)
        return chomp(state.fork(stream, filename))

    def advance_position((line0, file0), (line1, file1)):
        if file0 == file1 and line1 - 9 < line0 < line1:
            sys.stdout.write("\n" * (line1 - line0))
        else:
            sys.stdout.write("\n#line {!r} \"{!s}\"\n".format(line1, file1))
        return (line1, file1)

    def main():
        import sys
        env = {}
        if len(sys.argv) < 2:
            filename = "/usr/include/stdio.h"
        else:
            filename = sys.argv[1]
        with open(filename, 'r') as fd:
            contents = fd.read()
        stream = CharacterStream(trigraphs.translate(contents), 1, filename)
        state = PreprocessorState(stream, env,
                include_chain=(filename,),
                include=include_stub)
        try:
            position = (1, filename)
            for token in chomp(state):
                if position_of(token) != position:
                    position = advance_position(position, position_of(token))
                # Token generation. This is still wrong
                if name_of(token) == 'string': 
                    sys.stdout.write('"' + value_of(token) + '" ')
                elif name_of(token) == 'char':
                    sys.stdout.write("'" + value_of(token) + "' ")
                else:
                    sys.stdout.write(value_of(token) + ' ')
            sys.stdout.write('\n')
        except AssertionError as ass:
            traceback.print_exc()
            for x in range(5):
                print tokenize.chop(stream)
    main()
