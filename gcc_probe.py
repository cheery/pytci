"""
    This pytci utility probes a list of interesting paths from the gcc.

    Not called by rest of the pytci, due to extraneous dependencies not elsewhere.
"""
import subprocess, re, tempfile

def main():
    import sys
    compiler = sys.argv[1:]
    if len(compiler) == 0:
        compiler = ['gcc', '-m64']
    interpreter = probe_program_interpreter(compiler)
    search_paths = probe_search_paths(compiler)
    inc_local, inc_global = probe_includes(compiler)
    print "search paths:", search_paths
    print "\"...\" includes:", inc_local
    print "<...> includes:", inc_global
    print "program interpreter:", interpreter


def probe_search_paths(compiler):
    proc = subprocess.Popen(compiler + ['-Xlinker', '--verbose'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    search_paths = list(re.findall(r"SEARCH_DIR\(\"=(.*?)\"\);", proc.stdout.read()))
    proc.wait()
    return search_paths

def probe_includes(compiler):
    proc = subprocess.Popen(compiler + ['-xc', '-E', '-v', '-'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    proc.stdin.close()

    local_includes = []
    global_includes = []
    fill = strash = []
    for line in proc.stderr.readlines():
        if line == '#include "..." search starts here:\n':
            fill = local_includes
        elif line == '#include <...> search starts here:\n':
            fill = global_includes
        elif line == 'End of search list.\n':
            break
        else:
            fill.append(line.strip())
    proc.wait()
    return local_includes, global_includes

def probe_program_interpreter(compiler):
    testfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False)

    proc_gcc = subprocess.Popen(compiler + ['-xc', '-', '-o', '/proc/self/fd/1'],
        stdout=testfile,
        stdin=subprocess.PIPE)
    proc_gcc.stdin.write('int main() { return 0; }')
    proc_gcc.stdin.close()
    proc_gcc.wait()

    proc = subprocess.Popen(['readelf', '-l', testfile.name],
        stdout=subprocess.PIPE)
    interpreter = re.search(r"\[Requesting program interpreter: (.*)\]", proc.stdout.read())
    proc.wait()
    testfile.unlink(testfile.name)
    return interpreter.group(1).strip()

if __name__=='__main__':
    main()
