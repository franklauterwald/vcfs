from fs import Fs
import pyfuse3
import trio
import argparse
import os
from pathlib import Path

class Filename:
    def __init__(self, filename):
        self.filename = filename

class Filesequence:
    def __init__(self, first_filename):
        self.first_filename = first_filename

def create_parser():
    parser = argparse.ArgumentParser(description='Create a fuse filesystem that contains the contents of multiple source files as one virtually-concatenated file')
    parser.add_argument('-f', help='Add an input file. Can be used multiple times', action='append', dest='filenames', type=Filename)
    parser.add_argument('--fseq', help='Add a sequence of input files. Files must have numbered extensions, e.g. data.000, data.001, ... . Pass the name of the first file as parameter', action='append', dest='filenames', type=Filesequence)
    parser.add_argument('--outfile', help='Name of the virtual file. Defaults to the name of the first input file', default=None)
    parser.add_argument('--mode', help='Mode (access permissions) of the virtual file. Use octal notation, e.g. 644', default='644')
    parser.add_argument('-d', help='Enable fuse debugging output', action='store_true')
    parser.add_argument('-v', help='Verbose output', action='store_true')
    parser.add_argument('mountpoint', help='Mountpoint under which the fuse fs with the virtual file is created')
    return parser

# take a list of either Filename or Filesequence objects and create one flat list of strings with all actual filenames
# existing is a list of already flattened filenames (used for calling recursively)
def flatten_filenames(list, existing, verbose):
    if len(list) == 0:
        return existing
    if isinstance(list[0], Filename):
        filename = list[0].filename
        if verbose:
            print('Appending ' + filename + ' to list of files')
        assert Path(filename).is_file(), 'Input file ' + filename + ' does not exist. Exiting'
        return flatten_filenames(list[1:], existing + filename, verbose)
    if isinstance(list[0], Filesequence):
        if verbose:
            print('Appending sequence of files starting at ' + list[0].first_filename + ' to list of files')
        first_filename = list[0].first_filename
        assert Path(first_filename).is_file(), 'Input file ' + first_filename + ' does not exist. Exiting'
        additional = []
        basename, extension_with_dot = os.path.splitext(first_filename)
        extension = extension_with_dot[1:]
        try:
            idx = int(extension)
        except ValueError:
            assert False, 'When appending sequences of files, the file extension must be numeric. This is not the case for ' + first_filename
        next_filename = first_filename
        while (Path(next_filename).is_file()):
            additional.append(next_filename)
            idx = idx + 1
            format_string = '.{0:0'+str(len(extension))+'d}'
            next_filename = basename + (format_string.format(idx))

        return flatten_filenames(list[1:], existing + additional, verbose)

def parse_file_mode(mode):
    assert len(mode) == 3, 'file mode must consist of exactly three characters'
    u = int(mode[0])
    g = int(mode[1])
    o = int(mode[2])
    return u * 8 * 8 + g * 8 + o


def main():
    parser = create_parser()
    args   = parser.parse_args()

    verbose = args.v
    debug   = args.d

    assert args.filenames != None, "No input files given"
    source_filenames = flatten_filenames(args.filenames, [], verbose)

    if (args.outfile == None):
        dest_filename = source_filenames[0]
    else:
        dest_filename = args.outfile
    dest_mode         = parse_file_mode(args.mode)
    mountpoint        = args.mountpoint
    fs = Fs(source_filenames, dest_filename, dest_mode)
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=multiloop')
    if debug:
        fuse_options.add('debug')
    pyfuse3.init(fs, mountpoint, fuse_options)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=False)
        raise

    pyfuse3.close()

if __name__ == '__main__':
    main()