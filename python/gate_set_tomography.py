"""For use in Gate Set Tomography.
Converst the sequence templates provided by Sandia National Labs into HSDIO scripts that we can use."""

__author__ = 'Martin Lichtman'

def template_to_HSDIO_scripts(path):
    # load the text in from a file
    with open(path, 'r') as f:
        text = f.readlines()

    # split the text into a list of strings for each sequence
    sequences = [line.split(' ')[0] for line in text]

    # remove the header
    sequences.pop(0)

    # prepare a regex parser to read the repeat numbers
    import re
    p = re.compile('\d+')

    # create an empty list to hold a script string for each sequence
    scripts = []
    lengths=[]

    # for each sequence
    for i, s in enumerate(sequences):

        # start with an empty script
        script = ''
        length=0

        # go until we've parsed the whole sequence
        while len(s) > 0:
            # check if the remaining sequence starts with a known gate
            # if so, add it to the script
            if s.startswith('{}'):
                s = s[2:]
            elif s.startswith('Gx'):
                script += '  compressedGenerate Gx\n'
                s = s[2:]
                length += 1
            elif s.startswith('Gy'):
                script += '  compressedGenerate Gy\n'
                s = s[2:]
                length += 1
            elif s.startswith('Gi'):
                script += '  compressedGenerate Gi\n'
                s = s[2:]
                length += 1
            # in the case of parenthesis, parse through the whole statement to be repeated
            elif s.startswith('('):
                # make a mini script for the repeat
                repeat_script = ''
                repeat_length = 0
                s = s[1:]  # remove the '('
                # go until the close parenthesis
                while s[0] != ')':
                    # check for each of the known gates
                    if s.startswith('{}'):
                        s = s[2:]
                    elif s.startswith('Gx'):
                        repeat_script += '    compressedGenerate Gx\n'
                        s = s[2:]
                        repeat_length += 1
                    elif s.startswith('Gy'):
                        repeat_script += '    compressedGenerate Gy\n'
                        s = s[2:]
                        repeat_length += 1
                    elif s.startswith('Gi'):
                        repeat_script += '    compressedGenerate Gi\n'
                        s = s[2:]
                        repeat_length += 1
                    else:
                        print "unrecognized input {} in sequence {}\n{}\n".format(s[:1], i, sequences[i])
                        break
                # the parenthetical statement is now fully parsed
                s = s[1:]  # remove the ')'
                # check to see if there is a caret denoting how many times to repeat
                if s.startswith('^'):
                    s = s[1:]  # remove the '^'
                    # read the first number
                    m = p.match(s)
                    repeats = m.group()  # a string of how many repeats
                    s = s[len(repeats):]  # remove the number
                    # don't write anything if the number of repeats is zero
                    if int(repeats)>0:
                        # add the repeat number to the script
                        script += '  repeat ' + repeats + '\n'
                        script += repeat_script
                        script += '  end repeat\n'
                    length += repeat_length*int(repeats)
                else:
                    script += repeat_script
                    length += repeat_length
            else:
                print "unrecognized input {} in sequence {}\n{}\n".format(s[:1],i,sequences[i])
                break
        # save the script
        scripts += [script]
        lengths += [length]
    print '{} scripts generated'.format(len(scripts))
    return scripts, lengths
