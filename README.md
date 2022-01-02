# vcfs - A Virtual Concatenating FUSE Filesystem
vcfs is a very minimal [FUSE](https://www.kernel.org/doc/html/latest/filesystems/fuse.html) filesystem for linux written in python.

It serves exactly one purpose: take any number of input files and present
them as one large virtual file (as if the inputs were concatenated).
This functionality was inspired by the affuse tool 
(part of the [afflib library](https://github.com/simsong/AFFLIBv3)).
Affuse however provides a read-only view on the virtual file while vcfs
is read-write.

If you don´t need write capabilities, affuse is probably the better tool
due to its greater maturity and readymade packages for various distros.

vcfs was written with a specific use-case in mind. 
Part of my (admitedly slighly weird) backup strategy is based on luks-encrypted container filesystems
that host a git repository.
You mount the encrypted container, do and commit some changes and push
to some upstream that also has the respective container mounted.

This gives you
* history (git)
* distributed backups (containers on several machines)
* (partial) security against ransomware (encryption trojans). 
  As long as one of your copies survives, you still have the last unencrypted
  version in its history (just make sure you disallow force pushes).

The idea is described [here](https://www.bookware.de/KaffeeKlatsch-2016-04.pdf) in more detail (in German)
 

Now assume you got yourself some cloud storage and want to host a copy 
of some containers there. Unfortunately, you have only webdav access.
This has two implications:
* there´s no git, no rsync, no shell. In order to do anything with the container,
  you need to mount it back to some local machine, e.g. using [davfs2](https://savannah.nongnu.org/projects/davfs2)
  
* you need a pretty stable network connection stable enough to upload a whole multi-GB container in the first place.
  Without rsync or a shell you cannot do the upload in parts and then concatenate them on the server

This is where vcfs comes into play:
* upload the container as several files to some directory
* mount that directory locally via davfs2
* use vcfs to provide a "view" on this directory as if it were a single container file
* then mount that _virtual_ file as a filesystem containing your actual git repo

Pretty large number of indirections? True, but it works for me.

## Usage
```
usage: main.py [-h] [-f FILENAME] [--fseq FILENAME] [--outfile OUTFILE]
               [--mode MODE] [-d] [-v]
               mountpoint
```
* -f FILENAME: add a single source file. Use multiple times to add more source files.
  The virtual file will pretend to be the concatenation of all source files in order of appearance on the commandline
* --fseq FILENAME: add multiple source files. Source files must have numeric file extensions.
  The given filename is the first file in the sequence, e.g. _part.000_. vcfs will then add _part.001_, _part.002_, ... 
  as long as it can find more files matching the pattern. 
* --outfile OUTFILE: specify the name of the _virtual_ file in the vcfs. Defaults to the name of the first source file
* --mode MODE: specify the access mode if the _virtual_ file. Use the usual unix octal notation _ugo_. Defaults to 644
* -d: enable fuse debugging output. This will print all called fuse functions and some parameters
* -v: increase general verbosity. Mainly used during setup of the fuse filesystem. 
* mountpoint: directory where the vcfs is to be mounted

You should now see a file ${mountpoint}/${OUTFILE} and be able to read from and write to it.

## Development Status
The current version was hacked together in just a couple of hours 
because I wanted to scratch an itch of my own.
Little thought was given to usecases that others might have.

I´ve also not done any serious python for years and this certainly can be seen from the code.

Long story short: this is basically a works-for-me project atm.
It might or might not work for you, eat your data or even kill your cat.

## Contributing
Feel free to use the bugtracker or submit pull requests.

Since so far this is a weekend project, please don´t expect me to put 
too much effort into it. But contributions that can easily be checked
and incorporated are certainly very welcome.

## Acknowledgements
The code was inspired by (and even partially copied from) [the official pyfuse3 tutorial](https://github.com/libfuse/pyfuse3/blob/master/examples/hello.py)
