"""
    The preprocessor tokenizer, imitating the behavior of a popular C compiler.
"""

# Bugs noticed in this code when translating it to lever/lib/c.lc:
# The double digraph %:%: is not handled correctly.
# The %: is not recognized as a macro character in beginning of line.
def chop(stream):
    stream.skip_spaces()
    while stream.character == '\n':
        stream.get_next()
        stream.skip_spaces()
        # Tokenizer must mark "#" as MACRO, if it
        # appears in the beginning of a "logical" line
        if stream.character == '#':
            return token(stream.position, "macro", stream.get_next())
    if not stream.character:
        return None
    position = stream.position
    # Identifier: any sequence of letters, digits, or underscores,
    #             which begins with a letter or underscore
    #             you may have to accept $ as a letter
    if stream.character.isalpha() or stream.character == '_':
        value = stream.get_next()
        while stream.character.isalnum() or stream.character == '_':
            value += stream.get_next()
        return token(position, "identifier", value)
    # String literals start with: " ", ' ' literals cannot cross lines.
    # there is no way to escape backslash in #include <...>
    if stream.character in ("'", '"'):
        stream.comments = False
        terminal = stream.get_next()
        string = ""
        while stream.character != terminal:
            assert stream.character, "unterminated string"
            assert stream.character != "\n", "unterminated string"
            character = stream.get_next()
            if character == '\\':
                string += escape_sequence(stream)
            else:
                string += character
        stream.comments = True
        terminal = stream.get_next()
        if terminal == "'":
            return token(position, "char", string)
        elif terminal == '"':
            return token(position, "string", string)
        else:
            assert False, "error in tokenizing"
    # Preprocessing number: Formally, preprocessing numbers begin
    #                       with an optional period, a required
    #                       decimal digit, and then continue with
    #                       any sequence of letters, digits, underscores,
    #                       periods, and exponents. Exponents are the
    #                       two-character sequences 
    character = stream.get_next()
    if character.isdigit() or character == "." and stream.character.isdigit():
        number = character
        while stream.character.isalnum() or stream.character in ('._'):
            character = stream.get_next()
            number += character
            if character + stream.character in exponents:
                number += stream.get_next()
        return token(position, "number", number)
    if character in punctuators:
        punc = character
        pair = punc + stream.character
        while pair in long_punctuators:
            punc += stream.get_next()
            pair = punc + stream.character
        if pair in digraphs:
            punc = digraphs[punc + stream.get_next()]
        return token(position, "punctuation", punc)
    return token(position, "other", character)

def escape_sequence(stream):
    if stream.character in escape_sequences:
        return stream.get_next()
    string = stream.get_next()
    #\xhh The character whose numerical value is given by hh interpreted as a hexadecimal number
    if string == 'x':
        code = get_hex(stream) + get_hex(stream)
        if len(code) == 2:
            return chr(int(code, 16))
        return "\\" + string + code
    #\nnn The character whose numerical value is given by nnn interpreted as an octal number
    if is_octal_char(string):
        string += get_octal(stream) + get_octal(stream)
        if len(string) == 3:
            return chr(int(string, 8))
    return "\\" + string

def get_hex(stream):
    if stream.character in hex_alphabet:
        return stream.get_next()
    return ""

def get_octal(stream):
    if is_octal_char(stream.character):
        return stream.get_next()
    return ""

def is_octal_char(character):
    return character in octal_alphabet

def token(position, name, value=""):
    return position, name, value

hex_alphabet = set("0123456789ABCDEFabcdef")

octal_alphabet = set("01234567")

escape_sequences = {"a": 0x07, "b": 0x08, "f": 0x0C, "n": 0x0A, "r": 0x0D, "t": 0x09, "v": 0x0B, "\\": 0x5C, "'": 0x27, "\"": 0x22, "?": 0x3F}

exponents = set(["e+", "e-", "E+", "E-", "p+", "p-", "P+", "P-"])

punctuators = set([
    "!", "#", "$", "%", "&", "(", ")", "*", "+", 
    ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "[", 
    "\\", "]", "^", "_", "{", "|", "}", "~",
])

long_punctuators = set([
    "<=", ">=", "!=", "&&", "||", "++", "--", "==", "<<", ">>", "+=",
    "-=", "*=", "/=", "%=", "&=", "^=", "|=", "->", "..", "##",
    "...", "<<=", ">>="
])

digraphs = {"<%":"{", "&>":"}", "<:":"[", ":>":"]", "%:":"#", "%:%:":"##"}

# This is actually only used here for testing.
def chop_chop(stream):
    stream.skip_spaces()
    while stream.character is not "":
        yield chop(stream)

if __name__=='__main__':
    from character_stream import CharacterStream
    import trigraphs
    test = "#What ??=will c0me ??/\n0ut of/***sho*sho**/this line?//lollipops?"
    stream = CharacterStream(trigraphs.translate(test))
    for token_ in chop_chop(stream):
        print token_
