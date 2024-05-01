#!/usr/bin/env python
"""
Extract function signatures from html comments in markdown.
"""

import glob
import os
import os.path
import pathlib
import sys
import contextlib
import subprocess

@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(previous_dir)

HERE = pathlib.Path(__file__).parent


def get_sigs():
    sigs = {} 
    ref_dir = os.path.join(HERE, 'src', 'functions-reference')
    with pushd(ref_dir):
        for file in glob.glob('*.qmd'):
            with open(file) as rmd_file:
                lines = rmd_file.readlines()
                cur_sig = None
                for idx, line in enumerate(lines):
                    if line.startswith('<!-- '):
                        line = line.lstrip('<!- ')
                        parts = [x.strip() for x in line.split(';')]
                        if len(parts) == 3 and parts[1].endswith("~"):
                            sig = (parts[1].strip(" ~"), '~' ,parts[0], file)
                            sigs[sig] = lines[idx-2]
                        elif len(parts) == 4:
                            sig = (parts[1], parts[2], parts[0], file)
                            sigs[sig] = ""
                            cur_sig = sig
                        else:
                            print('not a function sig: {}'.format(line))
                    else:
                        # Part of documentation 
                        if (cur_sig is None or
                            line.startswith(("\\index", "{{")) or
                            line.endswith("\\newline\n") or
                            not line.strip()):
                            continue
                        if line.startswith("#"):
                            cur_sig = None
                        else:
                            sigs[cur_sig] += line.replace(";", "").replace("\n", "\\n")
                        
    return sigs



def main():
    if len(sys.argv) > 2:
        stan_major = int(sys.argv[1])
        stan_minor = int(sys.argv[2])
        outfile_name = 'stan-functions-{}_{}.txt'.format(str(stan_major), str(stan_minor))
    else:
        try:
            bash_git_hash = ['git', 'rev-parse', 'HEAD']
            git_hash = subprocess.run(bash_git_hash, stdout=subprocess.PIPE, universal_newlines=True).stdout
            outfile_name = 'stan-functions-{}.txt'.format(str(git_hash).strip())
        except OSError:
            print('Stan version not found and Git not found! Either install Git or add 2 arguments <MAJOR> <MINOR> version numbers')
            sys.exit(1)

    sigs = get_sigs()

    with open(outfile_name, 'w') as outfile:
        outfile.write('StanFunction;Arguments;ReturnType;Documentation;\n')
        for sig, doc in sigs.items():
            # print(doc)
            outfile.write(f"{sig[0]};{sig[1]};{sig[2]}")
            outfile.write(';')
            outfile.write(doc.strip())
            outfile.write(';\n')


if __name__ == '__main__':
    main()
