from qxpacker.Container import Container , ContainerFileType
import os , tempfile 
import tarfile

# OPTIONS:
class EchoContainer(Container):
    
    dirstack = []
    echo_cmd = "echo -en"
    
    def _control_code_flush(self, shellctx):
        shellctx.constant("CONTAINER_TYPE","echo")
        
    def __init__(self,ctx=None):
        Container.__init__(self, ctx)
    
    def file_content_to_cmd(self, filename, output_stream):
        src = open(filename,'rb')
        b = src.read(1)
        bn=0
        output_stream.write("$ECHO_CMD '")
        while b != "":
            if b == "'":
                output_stream.write("'\\''")
            elif ord(b) == 0:
                output_stream.write("\\0000")
            elif b == '\\':
                output_stream.write("\\\\")
            else:
                output_stream.write(b)
            b = src.read(1)
        output_stream.write("'")
    
    def shell_module_required(self):
        return []
    
    def __init__(self):
        True
    
    def _get_shell_payload(self, callnext):
        return "" + callnext +"\n"
    
    def _push_dir(self, to, dir):
        dirstack.append(dir)
    
    def _pop_dir(self, to, dir):
        d = dirstack[-1:]
        del dirstack[-1:]
    
    def _data_flush(self, to, callnext, data_extraction_fname = "extract_data", after_extraction = "", control_code_flush=True):
        self.shell_ctx.require('toolchain')
        self.shell_ctx.flush(to)
        to.write("%s () {\n" % data_extraction_fname)
        to.write("configure_echo_binary\n")
        for d in self.search(type = ContainerFileType.DIR):
            to.write("\tmkdir " + d.target_path + "\n")
        for d in self.search(type = ContainerFileType.FILE):
            to.write("\t")
            self.file_content_to_cmd(d.name, to)
            to.write(" >" + d.target_path + "\n")
            to.write("chmod " + d.permissions() + " " + d.target_path + "\n")
        if after_extraction != "":
            to.write("%s $@\n" % after_extraction)
        to.write("}\n")
        to.write(callnext + " $@\n")
    
    def set_opt(self,opt,val):
        True
    
