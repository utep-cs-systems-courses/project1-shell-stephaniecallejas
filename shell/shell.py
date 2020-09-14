#! /usr/bin/env python3
#Sections this code have been retrieved and modified from demos provided by the Instructor

import re, sys, os


def path(parent):
    for dir in re.split(':', os.environ['PATH']):  # try each directory in the path
        program = "%s/%s" % (dir, parent[0])
        try:
            os.execve(program, parent, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass  # ...fail quietly
    os.write(2, ("Could not exec %s\n" % parent[0]).encode())
    sys.exit(1)  # terminate with error


def execute(symbol, number, userIn):
    input = userIn.split(symbol)
    os.close(number)
    if symbol == '>':
        sys.stdout = open(input[1].strip(), 'w')
        fd = sys.stdout.fileno()
    else:
        sys.stdin = open(input[1].strip(), 'r')
        fd = sys.stdin.fileno()
    os.set_inheritable(fd, True)
    parent = input[0].split()
    path(parent)


while True:
    if 'PS1' in os.environ:  # If defined
        os.write(1, (os.environ['PS1']).encode())
    else:  # PS1 variable set to '$'
        os.write(1, ('$ ').encode())
    try:
        userInput = input()
    except EOFError:
        sys.exit(1)

    if userInput == "":  # Empty input, will prompt again
        continue
    if 'exit' in userInput:  # Terminates shell
        break
    if 'cd' in userInput:  # Change directory
        if '..' in userInput:
            changeDir = '..'
        else:
            changeDir = userInput.split('cd')[1].strip()
        try:
            os.chdir(changeDir)
        except FileNotFoundError:
            pass

        continue

    pid = os.fork()

    if pid < 0:
        os.write(2, ('Fork failed').encode())
        sys.exit(1)

    elif pid == 0:
        if "|" in userInput:  # Piping command
            pipe = userInput.split("|")
            commands = pipe[0].split()

            pRead, pWrite = os.pipe()  # file descriptors pr, pw for reading and writing
            for f in (pRead, pWrite):
                os.set_inheritable(f, True)
            pFork = os.fork()

            if pFork < 0:  # fork failed
                os.write(2, ('Fork failed').encode())
                sys.exit(1)

            if pFork == 0:  # child - will write to pipe
                os.close(1)  # redirect child's stdout
                os.dup(pWrite)
                os.set_inheritable(1, True)
                for fd in (pRead, pWrite):
                    os.close(fd)
                path(commands)

            else:  # parent (forked ok)
                os.close(0)
                os.dup(pRead)
                os.set_inheritable(0, True)
                for fd in (pWrite, pRead):
                    os.close(fd)
                path(pipe[1].split())

        if '&' in userInput:  # To run in background
            userInput = userInput.split('&')[0]
            parent = userInput.split()
        if '>' in userInput:  # Redirect output
            execute('>', 1, userInput)
        if '<' in userInput:  # Redirect input
            execute('<', 0, userInput)
        else:
            parent = userInput.split()
            if '/' in parent[0]:
                program = parent[0]
                try:
                    os.execve(program, parent, os.environ)
                except FileNotFoundError:
                    pass
            else:
                path(parent)
    else:
        if not '&' in userInput:
            os.wait()
