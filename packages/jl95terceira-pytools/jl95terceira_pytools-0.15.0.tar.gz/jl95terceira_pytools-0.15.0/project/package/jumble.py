import argparse
import os
import random
import subprocess

MARKER = b'8B1F2397EBFF4A07969BF2744340BAA3'
FILE_RW_CHUNK_SIZE = 1048*1048
FILE_ENCRYPTED_TAIL = '.JUMBLED'
FILE_DECRYPTED_TAIL = '.UNJUMBLED'

class Jumbler:

    def __init__(self,key:str):

        self._key    = key
        self._random = random.Random()

    def _jumble(self,f:str,fo:str,de:bool=False):

        self._random.seed(self._key)
        with open(f,mode='rb') as fr:

            with open(fo,mode='wb') as fw:

                if not de:

                    fw.write(MARKER)

                else:

                    fr.seek(len(MARKER))

                while True:

                    chunk = fr.read(FILE_RW_CHUNK_SIZE)
                    if not chunk: break
                    rbytes = self._random.randbytes(len(chunk))
                    fw.write(bytes(a^b for a,b in zip(chunk, rbytes)))

        return fo

    def jumble(self,f:str,fo:str|None=None):

        with open(f,mode='rb') as fr:

            if fr.read(len(MARKER)) == MARKER:
            
                raise Exception('file encrypted already')

        return self._jumble(f,fo if fo is not None else \
                            f'{f}{FILE_ENCRYPTED_TAIL}',de=False)

    def unjumble(self,f:str,fo:str|None=None):

        with open(f,mode='rb') as fr:

            if fr.read(len(MARKER)) != MARKER:
            
                raise Exception('file not encrypted - cannot decrypt')

        return self._jumble(f,fo                          if fo is not None                  else \
                            f[:-len(FILE_ENCRYPTED_TAIL)] if f.endswith(FILE_ENCRYPTED_TAIL) else \
                            f'{f}{FILE_DECRYPTED_TAIL}',de=True)

class Mode:  
    def __init__(self,descr:str): self._descr = descr
class Modes:
    PEEK = Mode('peek')
    EDIT = Mode('edit')

def do_it(f  :str,
          key:str,
          cleanup=False,
          de     =False,
          mode   :Mode|None=None):

    jumbler = Jumbler(key=key)
    if mode is Modes.PEEK:

        fo=jumbler.unjumble(f)
        subprocess.Popen([fo,],shell=True).wait()
        os.remove(fo)

    elif mode is Modes.EDIT:

        fo=jumbler.unjumble(f)
        subprocess.Popen([fo,],shell=True).wait()
        do_it(fo, key, cleanup=True)

    elif mode is None:
    
        (jumbler.jumble if not de else \
         jumbler.unjumble)(f)
        if cleanup:

            os.remove(f)

    else: raise AssertionError()

def main():

    class A:
        PATH    ='f'
        KEY     ='key'
        CLEANUP ='c'
        DECRYPT ='de'
        PEEK    ='peek'
        EDIT    ='edit'
    ap = argparse.ArgumentParser(description=f'Encrypt / Decrypt a file\nThe default action is to encrypt. To decrypt, set option {repr(A.DECRYPT)}.')
    ap.add_argument(f'{A.PATH}',
                    help='path to the file')
    ap.add_argument(f'{A.KEY}',
                    help='key (password)')
    ap.add_argument(f'--{A.CLEANUP}',
                    help='after processing, remove the original file',
                    action='store_true')
    ap.add_argument(f'--{A.DECRYPT}',
                    help='decrypt',
                    action='store_true')
    ap.add_argument(f'--{A.PEEK}',
                    help='decrypt and open the decrypted file with the system\'s default editor. After closing, the decrypted file will be removed.',
                    action='store_true',)
    ap.add_argument(f'--{A.EDIT}',
                    help='decrypt, open the decrypted file with the system\'s default editor, save and re-encrypt.\nThis option is useful for quickly editing an encrypted file.',
                    action='store_true',)
    get = ap.parse_args().__getattribute__
    mode = Modes.PEEK if get(A.PEEK) else \
           Modes.EDIT if get(A.EDIT) else \
           None
    if mode is not None:
        print(f'Mode: {mode._descr}')
    do_it(get(A.PATH),
          get(A.KEY),
          cleanup=get(A.CLEANUP),
          de=get(A.DECRYPT),
          mode=mode)
    print('Done')

if __name__ == '__main__': main()