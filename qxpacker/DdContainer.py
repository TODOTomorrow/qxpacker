from qxpacker.Container import Container , ContainerFileType
import os , tempfile 
import tarfile
import shellgen
import math 

class DdFile:
    file = None
    def __init__(self, file):
        self.__dict__['file'] = file
    
    def __setattr__(self, name, value):
        setattr(self.file , name , value)
        
    def __getattr__(self, name):
        return getattr(self.file , name)

def roundup(x,to):
    if x == 0:
        return 1
    if x%to != 0:
        return (x/to)+1
    else:
        return (x/to)

# OPTIONS:
#      name     :   possible values  : description
#------------------------------------------------------------
#      align    : [number]           : Set align size
class DdContainer(Container):
    align = 1024
    def __init__(self, ctx = None):
        Container.__init__(self, ctx)
        self.align = 1024
    
    def _control_code_flush(self, shellctx):
        shellctx.constant("CONTAINER_TYPE","dd")
    
    def _data_extraction_content(self, files, dummy, data_extraction_fname = "extract_data", after_extraction = ""):
        dircontent=""
        filecontent=""
        for f in files:
            if f.isdir():
                dircontent += "\tmkdir " + f.target_path + "\n"
            else:
                block_cnt = f.size() / self.align
                byte_cnt = f.size() % self.align
                if dummy:
                    if block_cnt:
                        filecontent += "\tdd if=$0 of=" + f.target_path + " bs=" + str(self.align) + " count=" + str(block_cnt) + " skip=" + (" " * 20) + "\n"
                    if byte_cnt:
                        filecontent += "\tdd if=$0 bs=1 count=" + str(byte_cnt) + " skip=" + (" " * 20) + " >>" + f.target_path + "\n"
                    if (block_cnt == 0 and byte_cnt == 0):
                        filecontent += "\ttouch " + f.target_path + "\n"
                    filecontent += "\tchmod " + str(f.permissions()) + " " + f.target_path + "\n"
                else:
                    if block_cnt:
                        filecontent += "\tdd if=$0 of=" + f.target_path + " bs=" + str(self.align) + " count=" + str(block_cnt) + " skip=" + str(f.offset) + ((20 - len(str(f.offset))) * " ") + "\n"
                    if byte_cnt:
                        filecontent += "\tdd if=$0 bs=1 count=" + str(byte_cnt) + " skip=" + str((f.offset + block_cnt) * 1024) + ((20 - len(str(f.offset + block_cnt))) * " ")  + " >>" + f.target_path + "\n"
                    if (block_cnt == 0 and byte_cnt == 0):
                        filecontent += "\ttouch " + f.target_path + "\n"
                    filecontent += "\tchmod " + str(f.permissions()) + " " + f.target_path + "\n"
        outs = ("%s() {\n" + dircontent + "\n" + filecontent + "\n") % data_extraction_fname
        if after_extraction != "":
            outs += "\t%s $@\n" % after_extraction
        outs += "}\n"
        return outs
    
    def _data_flush(self, to, callnext, data_extraction_fname = "extract_data", after_extraction = "", control_code_flush=True):
        self.shell_ctx.require('tmpfile')
        self.shell_ctx.constant('TMPFILENAME','`tmpfilename`')
        self.shell_ctx.flush(to)
        files = [DdFile(s) for s in (self.search(type = ContainerFileType.FILE) + self.search(type = ContainerFileType.DIR))];
        dummy_content = self._data_extraction_content(files, True, data_extraction_fname, after_extraction)
        dummy_content += callnext + " $@ \n"
        offset=roundup(len(dummy_content) + to.tell(),self.align)
        start_offset = offset
        for f in files:
            if f.isfile():
                f.offset = offset
                offset+=roundup(f.size(), self.align)
        
        content = self._data_extraction_content(files, False, data_extraction_fname, after_extraction)
        content += callnext + " $@ \n"
        to.write(content)
        # Make alignation for first file
        to.write(" " * ((self.align * start_offset) - to.tell()))
        for f in files:
            if f.isfile():
                for part in f.content():
                    to.write(part)
                to.write(" " * ((self.align * (f.offset + roundup(f.size(), self.align))) - to.tell()))
    
    def set_opt(self,opt,val):
        if opt == "align":
            self.align = val
    
