import stat
import os
import logging
import errno
import pyfuse3
from pyfuse3 import FUSEError

log = logging.getLogger(__name__)

class SourceFile:
    def __init__(self, file_name, start_pos):
        self.handle = os.fdopen(os.open(file_name, os.O_RDWR), 'rb+')
        self.start_pos = start_pos
        self.size = os.path.getsize(file_name)
        self.end_pos = self.start_pos + self.size

class Fs(pyfuse3.Operations):
    def __init__(self, source_filenames, dest_filename, dest_mode):
        super(Fs, self).__init__()
        self.source_filenames = source_filenames
        self.dest_filename = dest_filename
        self.dest_mode = dest_mode
        self.dest_inode = pyfuse3.ROOT_INODE + 1

        start_pos = 0
        self.source_files = []
        self.total_size = 0
        for source_filename in self.source_filenames:
            source_file = SourceFile(source_filename, start_pos)
            self.source_files.append(source_file)
            start_pos = start_pos + source_file.size
            self.total_size = source_file.end_pos

    async def lookup(self, inode_p, name, ctx=None):
        # inode_p: parent inode
        assert inode_p == pyfuse3.ROOT_INODE
        if name == self.dest_filename.encode('utf-8'):
            return await self.getattr(self.dest_inode, ctx)
        else:
            entry = pyfuse3.EntryAttributes()
            entry.st_ino = 0 # denotes: does not exist
            return entry

    async def readdir(self, fh, start_id, token):
        # WHY IS THIS CALLED WITH fh=0
        # fh is a file handle, not an inode
        # previous call is opendir - which returns a file handle
        # assert fh == pyfuse3.ROOT_INODE
        if start_id == 0:
            pyfuse3.readdir_reply(
                token, self.dest_filename.encode('utf-8'), await self.getattr(self.dest_inode), 1)
        return

    async def getattr(self, inode, ctx=None):
        entry = pyfuse3.EntryAttributes()
        if inode == pyfuse3.ROOT_INODE:
            entry.st_mode = (stat.S_IFDIR | 0o755)
            entry.st_size = 0
        elif inode == self.dest_inode:
            entry.st_mode = (stat.S_IFREG | self.dest_mode)
            entry.st_size = self.total_size
        else:
            raise pyfuse3.FUSEError(errno.ENOENT)

        stamp = int(1438467123.985654 * 1e9)
        entry.st_atime_ns = stamp
        entry.st_ctime_ns = stamp
        entry.st_mtime_ns = stamp
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode

        return entry

    async def open(self, inode, flags, ctx):
        if inode != self.dest_inode:
            raise pyfuse3.FUSEError(errno.ENOENT)
        # do we need to check this against dest_mode or will the kernel do that for us?
        # if flags & os.O_RDWR or flags & os.O_WRONLY:
        #     raise pyfuse3.FUSEError(errno.EACCES)
        return pyfuse3.FileInfo(fh=inode)

    async def read(self, fh, off, size):
        assert fh == self.dest_inode
        return self.read_internal(off, size)

    async def write(self, fh, off, buf):
        assert fh == self.dest_inode
        return self.write_internal(off, buf, 0)

    def find_source_file(self, off):
        for source_file in self.source_files:
            if off >= source_file.start_pos and off < source_file.end_pos:
                return source_file
        return None

    def read_internal(self, off, size):
        if size <= 0:
            return b''
        source_file = self.find_source_file(off)
        if source_file == None:
            return b''
        pos_in_file = off - source_file.start_pos
        source_file.handle.seek(pos_in_file)
        cnt = min(size, source_file.size - pos_in_file)
        return source_file.handle.read(cnt) + self.read_internal(off+cnt, size-cnt)

    def write_internal(self, off, buf, already_written):
        source_file = self.find_source_file(off)
        if source_file == None:
            return already_written
        pos_in_file = off - source_file.start_pos
        source_file.handle.seek(pos_in_file)
        cnt = min(len(buf), source_file.size - pos_in_file)
        buf_this      = buf[0:cnt]
        buf_remaining = buf[cnt:-1]
        bytes_written = source_file.handle.write(buf_this)
        if len(buf_remaining) == 0:
            # done
            return already_written + bytes_written
        else:
            return self.write_internal(off + bytes_written, buf_remaining, already_written + bytes_written)