#!/usr/bin/python3
# ./generate_from_rlottie.py /path/to/clean/rlottie/src/ /path/to/clean/rlottie/inc/
import glob
import os
import re
import sys

FILE_KEYS = {}

def get_closest_local_header(header):
    for full_path, local in FILE_KEYS.items():
        if os.path.basename(full_path) == header:
            return local
    return ''

def fix_headers(code_text):
    out = ''
    for line in code_text:
        # Special fixes
        if line == '#include <vpoint.h>':
            line = '#include "vpoint.h"'
        if line == '#include <vsharedptr.h>':
            line = '#include "vsharedptr.h"'
        if line == '#include <vglobal.h>':
            line = '#include "vglobal.h"'
        if line == '#include <vrect.h>':
            line = '#include "vrect.h"'
        header_file = re.match('#include\s+["]([^"]+)["].*', line)
        # regex to search for <, > too
        #header_file = re.match('#include\s+[<"]([^>"]+)[>"].*', line)
        if header_file:
            header = header_file.groups()[0]
            abs_header = os.path.abspath(header)
            header_exists = os.path.exists(abs_header)
            if header_exists and abs_header in FILE_KEYS:
                out += '#include "' + FILE_KEYS[abs_header] + '"\n'
            else:
                local = get_closest_local_header(header)
                if local != '':
                    out += '#include "' + local + '"\n'
                else:
                    out += line + '\n'
        else:
            out += line + '\n'
    return out

if len(sys.argv) < 2:
    print('usage: ./generate_from_rlottie.py /path/to/clean/rlottie/src/ /path/to/clean/rlottie/inc/')
    os._exit(1)

code = ['.c', '.s', '.S', '.sx', 'cc', 'cpp', 'cpp' ]
header = ['.h', '.hh', '.hpp', '.hxx' ]

# Remove old files
files = os.listdir('.')
for file in files:
    if file.endswith(tuple(code)) or file.endswith(tuple(header)):
        os.remove(os.path.join('.', file))

paths = []
it = iter(sys.argv)
next(it, None)
for argv in it:
    paths.append(argv)

for path in paths:
    for file in glob.iglob(path + '/**', recursive=True):
        # Ignore msvc config.h and wasm file
        if file.endswith('config.h') or 'wasm' in file:
            continue
        if file.endswith(tuple(code)) or file.endswith(tuple(header)):
            key = os.path.abspath(file)
            val = file.replace(path, '').replace('/', '_')
            FILE_KEYS[key] = val

header_check = []
for full_path, local in FILE_KEYS.items():
    header_file = os.path.basename(full_path)
    if header_file.endswith(tuple(code)):
        continue
    if not header_file in header_check:
        header_check.append(header_file)
    else:
        print('WARNING: ' + header_file + ' has multiple reference in subdirectories')

cur_dir = os.path.abspath('.')
for full_path, local in FILE_KEYS.items():
    os.chdir(os.path.dirname(full_path))
    with open(full_path) as code:
        code_text = code.read().splitlines() 
    code.close()
    fixed = fix_headers(code_text)
    os.chdir(cur_dir)
    local_file = open(local, "w")
    local_file.write(fixed)
    local_file.close()

# Write config.h
config = '#define LOTTIE_THREAD_SUPPORT\n#define LOTTIE_CACHE_SUPPORT\n'
config_file = open('config.h', "w")
config_file.write(config)
config_file.close()

# Fix vector_pixman_pixman-arm-neon-asm.S
with open('vector_pixman_pixman-arm-neon-asm.S') as code:
    assembly = code.read()
code.close()
assembly = '#ifdef __ARM_NEON__\n' + assembly + '#endif\n'
fixed_assembly = open('vector_pixman_pixman-arm-neon-asm.S', "w")
fixed_assembly.write(assembly)
fixed_assembly.close()
