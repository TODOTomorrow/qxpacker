from qxpacker.Container import Container , ContainerFileType
from qxpacker.DdContainer import DdContainer
from qxpacker.EchoContainer import EchoContainer
import os , tempfile 
import tarfile


# OPTIONS:
#      name     :   possible values  : description
#------------------------------------------------------------
#      compress : gzip none          : Set compression type
#      loader   : dd echo            : Select bootloader (dd by default)
class TarContainer(Container):
    
    compression=''
    bootloader = DdContainer()
    
    def shell_module_required(self):
        return []
    
    def __init__(self, ctx = None):
        self.compression = ''
        self.bootloader = DdContainer()
        Container.__init__(self, ctx)
    
    def _control_code_flush(self, shellctx):
        shellctx.constant("CONTAINER_TYPE","tar")
    
    def _data_flush(self, to, callnext, data_extraction_fname = "extract_data", after_extraction = "", control_code_flush=True):
        targz_tmpfile = tempfile.mktemp()
        tf = tarfile.open(targz_tmpfile, 'w:' + self.compression)
        
        for f in self.search(recurse_datalist = True):
            absname = os.path.abspath(f.name)
            dirname=os.path.dirname(absname)
            filename=os.path.basename(absname)
            tf.add(absname , arcname = f.target_path)
        tf.close()
        to.write("tarcontainer_extract() { \n")
        to.write("tar -xf")
        if self.compression == "gz":
            to.write("z")
        to.write(" $TMPFILENAME\n");
        if after_extraction != "":
            to.write("\t%s $@" % after_extraction)
        to.write(" }\n")
        self.bootloader.add(targz_tmpfile, tpath = "$TMPFILENAME")
        self.bootloader.flush(to, callnext,  data_extraction_fname = data_extraction_fname, after_extraction = "tarcontainer_extract", control_code_flush = False)

        if os.path.isfile(targz_tmpfile): os.remove(targz_tmpfile)
    
    
    def set_opt(self,opt,val):
        if opt == 'compress':
            if   val == 'none': self.compression = ''
            elif val == 'gzip': self.compression = 'gz'
            else: raise Exception('Bad option value ' + opt + ' = ' + val)
        elif opt == 'loader':
            if   val == 'dd': self.bootloader = DdContainer()
            elif val == 'echo': self.bootloader = EchoContainer()
            else: raise Exception('Bad option value ' + opt + ' = ' + val)
    
