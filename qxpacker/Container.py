import types
import os
from qxpacker.shellgen import ShellScriptBuilder
from stat import ST_MODE

def enum(**enums):
    return type('Enum', (), enums)

def path2prefixlist(path):
    dirs = path.split('/')
    ar = []
    cs = ""
    for dir in dirs:
        cs += dir + "/"
        ar.append(cs)
    return ar[:-1]

def parent(path):
    return os.path.basename(os.path.normpath(path + '/../'))

ContainerFileType = enum(FILE='FILE', DIR='DIR')

# Decorator for default byte stream
class ContainerByteStream:
    bs = None
    bcount=0
    def __init__(self, bs):
        self.__dict__['bs'] = bs
        self.__dict__['bcount'] = 0
    
    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value 
        else:
            setattr(self.bs , name , value)
        
    def __getattr__(self, name):
        return getattr(self.bs , name)
    
    def tell(self):
        return int(self.bcount)
    
    def write(self, *args):
        for arg in args:
            self.bcount += len(str(arg))
            self.bs.write(arg)


class ContainerFile:
    name=""
    target_path=""
    stype=ContainerFileType.FILE
    parent = None
    all_childs_inc = True
    childs = []
    
    def __eq__(self, other):
        if other == None:
            return False;
        return ( (self.name == other.name)     and
                 (self.stype == other.stype)   and
                 (self.target_path == other.target_path))
    
    def __init__(self, name, tpath = None, parent = None):
        self.parent = parent
        self.name = os.path.normpath(name)
        if os.path.normpath (tpath) == '.': tpath = None
        self.childs = []
        self.all_childs_inc = True
        if tpath == None:
            if not os.path.isdir(name):
                tpath = os.path.basename(name)
            else:
                tpath = '/'
        tpath = tpath.replace('//','/')
        self.target_path = os.path.normpath(tpath)
        
        if os.path.isdir(name):
            self.stype = ContainerFileType.DIR
        else:
            self.stype = ContainerFileType.FILE
    
    def size(self):
        return os.path.getsize(self.name)
    
    def permissions(self):
        return oct(os.stat(self.name)[ST_MODE])[-3:]
    
    def content(self, chunk_size=1024):
        f = open(self.name,'rb')
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data
    
    # Mark current node as node, that not included all childs
    # Used for recursive updating
    # If recursive flag is set and node is directory, 
    # then flag is set recursively for all childs
    def make_dirty(self, recursive = False):
        self.all_childs_inc = False
        if (recursive and self.isdir()):
            for c in self.childs:
                c.make_dirty()
    
    def add_child(self, c):
        self.childs.append(c)
    
    def del_child(self,c):
        self.childs.remove(c)
    
    # Get highest ancestor for current node.
    # Options:
    #      cond - is  condition, which will be checked on each step of hierarchy lifting
    #              if cond is false, then current element returned
    def highest_ancestor(self, cond = (lambda x: True)):
        if ((self.parent != None) and (cond(self))):
            return self.parent.highest_ancestor(cond);
        else:
            return self;
    
    # Private ancillary method for highest ancestry searching
    def ancestors_r(self, alist = []):
        alist.append(self)
        if self.parent == None:
            return alist
        else:
            return self.parent.ancestors_r(alist)
        
    # Get list of all ancestors for current node
    def ancestors(self): 
        v = self.ancestors_r([])
        if len(v):
            return v[1:]
        else:
            return v
    
    def isfile(self):
        return (self.stype == ContainerFileType.FILE)
    
    def isdir(self):
        return (self.stype == ContainerFileType.DIR)
    
    def __str__(self):
        return self.name + " => " + self.target_path + " (" + str(self.stype) + ")"
    
    def compare(self, path = None, tpath = None, strictly = True, type = None, cmp = None):
        if path != None: path = os.path.normpath(path);
        
        if path != None:
            path = os.path.normpath(path)
            if strictly:
                 if path != self.name:
                    return False
            else:
                if not self.name.startswith(path):
                    return False
        
        if tpath != None:
            tpath = os.path.normpath(tpath)
            if strictly:
                 if tpath != self.target_path:
                    return False
            else:
                if not self.target_path.startswith(tpath):
                    return False
        
        if type != None:
            if type != self.stype:
                return False
        if cmp != None:
            if not cmp(self):
                return False
        return True

class Container:
    datalist = []
    datalist_recurse = []
    recurse_dirty = False
    shell_ctx = ShellScriptBuilder()
    
    def __init__(self, shell_context = None ):
        if shell_context == None:
            shell_context = ShellScriptBuilder()
        self.datalist = []
        self.recurse_dirty = False
        self.shell_ctx = shell_context
    
    def _add_file_node(self,node):
        self.datalist.append(node)
        if node.parent != None:
            node.parent.add_child(node)
        self.recurse_dirty = True
        
    def _del_file_node(self,node, recursive = False):
        if node.parent != None:
            node.parent.del_child(node)
        if (recursive and node.isdir()):
            childlist = node.childs[:]
            for c in childlist:
                self._del_file_node(c, recursive = True)
        
        self.datalist.remove(node)
        self.recurse_dirty = True
    
    def _walk_dir_recurse(self, rpath, tpath):
        if tpath == None: tpath = './'
        files = os.listdir(rpath)
        d = []
        for file in files:
            d.append((rpath + '/' + file , tpath + '/' + os.path.basename(file)))
        return d
    
    def _add(self, rpath, tpath, type = None, recurse_root = True, parent = None):
        self.recurse_dirty = True
        cf = ContainerFile(rpath, tpath, parent = parent)
        self._add_file_node(cf)
        if recurse_root:
            self.datalist_recurse.append(cf)
        return cf
    
    # Add file or directory to container
    # Paramters:
    #         rpath - real path to file
    #         tpath - path to file into container
    def add(self,rpath, tpath = None, recurse_root = True, parent = None):
        if os.path.isdir(rpath):
            filedir_list = self._walk_dir_recurse(rpath, tpath)
            o = self._add(rpath, tpath, recurse_root = recurse_root, parent = parent)
            for (rpath , _tpath) in filedir_list:
                self.add(rpath, _tpath, False, parent = o)
        else:
            self._add(rpath, tpath, recurse_root = recurse_root, parent = parent)
        
        
    
    def __str__(self):
        s = ''
        for l in self.datalist:
            s += str(l) + "\n"
        return s
    
    # Find nodes by passed parameters
    # Most of all parameters are relevant to ContainerFile properties
    # Additional options
    #       cmp              - is predicate, which can be used for custom comparasion
    #       strictly         - relevant to tpath and rpath. If is true, then comparasion 
    #                          will be by for whole path, else by prefix 
    #                          ( if paths have some common prefix, then comparasion will be successfull)
    #       recurse_datalist - if selected, then recurse data list will be used as data source
    #       get_ids_only     - if selected, then function return only identifiers(not objects)
    def search(self, path = None, tpath = None, strictly = True, type = None, recurse_datalist = False, get_ids_only = False, cmp = None):
        nodes = []
        i=0
        if recurse_datalist:
            dl = self.get_recurse_datalist()
        else:
            dl = self.datalist
        
        for f in dl:
            if f.compare(path = path, tpath = tpath, strictly = strictly, type = type, cmp = cmp):
                nodes.append(i)
            i+=1
        
        if get_ids_only:
            return nodes
        else:
            return self.__getitem__(nodes,recurse_datalist = recurse_datalist)
    
    # Convert passed key to identifier
    # Valid key formats:
    # 1. Number with identifier ( will return the same)
    # 2. List of other keys
    # 3. String with identifier. Format (all parts are optional):
    #         [real file path]=>[target file path]
    def key2ids(self,key, strictly = True):
        if isinstance(key , types.ListType):
            n = []
            for k in key:
                n += self.key2ids(k)
            return n
        if isinstance(key, ( types.IntType , types.LongType)):
            return [key]
        else:
            key = key.strip()
            if key == None: raise Exception("Incorrect datalist key")
            if isinstance(key, basestring):
                paths = key.split("=>")
                if len(paths) == 1:
                    rpath = key
                    tpath = None
                else:
                    if len(paths[0]) > 0:
                        rpath = paths[0].strip()
                        tpath = paths[1].strip()
                    else:
                        rpath = None
                        tpath = paths[1].strip()
                nodes = []
                fnodes = self.search(rpath,tpath, get_ids_only = True, strictly = strictly)
                for f in fnodes:
                    nodes.append(f)
                return nodes
    
    def _tpath_neighbors(self, tpath):
        ar = []
        keys = self.search(tpath = tpath, strictly = False)
        for k in keys:
            relpath = k.target_path[len(tpath):]
            if len(relpath) and relpath.count('/') == 0:
                ar.append(relpath)
        return ar
    
    def _recurse_update(self):
        if not self.recurse_dirty:
            return True
        self.recurse_dirty = False
        self.datalist_recurse = []
        for fn in self.search(cmp = (lambda x: x.all_childs_inc)):
            a = fn.highest_ancestor((lambda (x): x.parent.all_childs_inc))
            if not a in self.datalist_recurse:
                self.datalist_recurse.append(a)
        #for x in [ str(s) for s in self.datalist_recurse]: print "\t Recurse " + x
#        print [ str(s.target_path) for s in self.datalist_recurse]
            #tpath = fn.target_path
            #print tpath , fn.full
            #print tpath , [ str(s) for s  in self.parent(fn)]
        
    
    def is_node_exists(self, node):
        if node in node.parent.childs:
            return True
        return False
    
    # Exclude file from container
    def exclude(self, kkey):
        nodes = self.__getitem__(kkey)
        if len(nodes) == 0:
            print "[Warning] Cannot exclude %s. Not found in container" % kkey
        for node in nodes:
            for anc in node.ancestors():
                anc.make_dirty()
                #anc.full = False
            if self.is_node_exists(node):
                self._del_file_node(node, recursive = True)
            
    
    def get_recurse_datalist(self):
        self._recurse_update()
        return self.datalist_recurse
    
    def __getitem__(self, kkey, recurse_datalist = False, strictly = True):
        keys = self.key2ids(kkey, strictly = strictly)
        d = []
        if recurse_datalist:
            dl = self.get_recurse_datalist()
        else:
            dl = self.datalist
        
        for key in keys:
            d.append(dl[key])
        return d
    
    def control_code_flush(self, shellctx):
        shellctx.array("FILES", [(s.target_path, s.stype, s.permissions(), s.size()) for s in self.search()])
        self._control_code_flush(shellctx)
    
    # Convert container content to byte stream
    # Paramters:
    #          to - output stream (shoult support 'write' operator)
    #          callnext - string with name of shell function, which should be called after container shell initialization
    def flush(self, to, callnext = "", data_extraction_fname = "extract_data", after_extraction = "", control_code_flush=True):
        if isinstance(to, basestring):
            to = ContainerByteStream(open(to,"w"))
        
        if not isinstance(to, ContainerByteStream):
            to = ContainerByteStream(to)
        
        self._recurse_update()
        if control_code_flush:
            self.control_code_flush(self.shell_ctx)
        self.shell_ctx.flush(to)
        self._data_flush(to, callnext, data_extraction_fname, after_extraction, control_code_flush)
    
    # Set some custom options (handled by descendants)
    def set_opt(self,opt,val):
        True
    
    # Return list of shell modules required to container content
    # Overrided by descendants
    def shell_module_required(self):
        return []
