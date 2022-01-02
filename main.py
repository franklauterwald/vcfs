from fs import Fs
import pyfuse3
import trio

def main():
    source_filenames = ['/mnt/sdb/use/test-cloud-container/foo.000', '/mnt/sdb/use/test-cloud-container/foo.001']
    dest_filename    = 'foo'
    dest_mode        = 0o666
    mountpoint       = '/mnt/sdb/use/test-cloud-container/mnt/'
    fs = Fs(source_filenames, dest_filename, dest_mode)
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=hello')
    fuse_options.add('debug')
    pyfuse3.init(fs, mountpoint, fuse_options)
    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=False)
        raise

    pyfuse3.close()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()