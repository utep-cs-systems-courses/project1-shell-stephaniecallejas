#! /usr/bin/env python3

#In order for it to work
import os, sys, time, re

def path(args):
        for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                program = "%s/%s" % (dir, args[0])
                #os.write(1, ("Child:  ...trying to exec %s\n" % program).encode())
                try:
                        os.execve(program, args, os.environ) # try to exec program
                except FileNotFoundError:             # ...expected
                        pass                              # ...fail quietly

        #os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                 # terminate with error

        
def redirect(direction, userInput):
        userInput = userInput.split(direction)    #Split user input by direction sign
        if direction == '>':                      #If '>' redirect output into file
                os.close(1)
                sys.stdout = open(userInput[1].strip(), "w")  #open and set to write
                os.set_inheritable(1, True)
                path(userInput[0].split())
        else:
                os.close(0)                       #Redirect input 
                sys.stdin = open(userInput[1].strip(), 'r')   #open and set to read
                os.set_inheritable(0, True)
                path(userInput[0].split())
while True:
        if 'PS1' in os.environ:  #If PS1 defined, use it
            os.write(1, (os.environ['PS1']).encode())
        else:
            os.write(1, ('$$ ').encode())   #If not, go to default

        try:
                userInput = input()
        except EOFError:
                sys.exit(1)

        #Tried to user read() but did not work
        """
        userInput = os.read(0,100).decode() # Read input
        if not userInput:
                sys.exit(0)
        elif userInput is '\n':                      # End of line
                pass                
        """
        if userInput == "": # Empty input, will prompt again
            continue
        if 'exit' in userInput: # Terminates shell
            break
        if 'cd' in userInput: # Change directory
                if '..' in userInput:
                        changeDir = '..'
                else:
                        changeDir = userInput.split('cd')[1].strip()
                try:
                        os.chdir(changeDir)
                except FileNotFoundError:
                        pass
                continue
        pid = os.getpid()
        #os.write(1, ("About to fork (pid:%d)\n" % pid).encode())
        rc = os.fork()
        if rc < 0:
                #os.write(2, ("fork failed, returning %d\n" % rc).encode())
                sys.exit(1)
        elif rc == 0:                   # child

                #os.write(1, ("Child: My pid==%d.  Parent's pid=%d\n" %(os.getpid(), pid)).encode())
                args = userInput.split()
                

                if "|" in userInput: # Piping command
                        pipe = userInput.split("|")    
                        pipeCommand1= pipe[0].split()
                        pipeCommand2 = pipe[1].split()

                        pr, pw = os.pipe()  # file descriptors pr, pw for reading and writing
                        for f in (pr, pw):
                                os.set_inheritable(f, True)
                        pipeFork = os.fork()
                        if pipeFork < 0:  # fork failed
                                #os.write(2, ('Fork failed').encode())
                                sys.exit(1)

                        if pipeFork == 0: # child - will write to pipe
                                os.close(1) # redirect child's stdout
                                os.dup(pw)
                                os.set_inheritable(1, True)
                        
                                for fd in (pr, pw):
                                        os.close(fd)
                                path(pipeCommand1)    
                        else: # parent (forked ok)
                                os.close(0)
                                os.dup(pr)
                                os.set_inheritable(0, True)
                                for fd in (pw, pr):
                                        os.close(fd)
                                path(pipeCommand2)
        
                if '&' in userInput: # To run in background
                        userInput = userInput.split('&')[0]
                        args = userInput.split()
                        
                if '>' in userInput:     #If > in input, send to
                                         #redirect method for output redirection
                        redirect('>', userInput)
                elif '<' in userInput:   #Input redirection
                        redirect('<', userInput)
                else:
                        if '/' in args[0]:  #If '/' in user input, try the given path
                                program = args[0]
                                try:
                                        os.execve(program,args,os.environ)
                                except FileNotFoundError:  #If not found, give error
                                        pass
                        else:
                                path(args)                 #If no redirection/path/piping
                                                           #send to find path


        else:                           # parent (forked ok)
                if not '&' in userInput:                  #If not '&', no background task, wait
                                                          #for child
                        
                        #os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" %(pid, rc)).encode())
                        childPidCode = os.wait()
                        #os.write(1, ("Parent: Child %d terminated with exit code %d\n" %childPidCode).encode())
                