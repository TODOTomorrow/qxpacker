import os, re, sys

class statement():
    flushed = False
    def __init__(self):
        self.flushed = False
        self.name=""
    
    def _flush(self, to):
        True
    
    def set(self, val):
        True
    
    def get(self, val):
        True
    
    def flush(self, to):
        if self.flushed:
            return
        self.flushed = True
        self._flush(to)

class custom_string(statement):
    def __init__(self, name, strn):
        statement.__init__(self)
        self.name = name
        self.val = strn
    
    def set(self, val):
        self.val = val
    
    def get(self):
        return self.val
    
    def _flush(self,to):
        to.write(self.val + "\n")
    
    

class constant(statement):
    def __init__(self, name, value):
        statement.__init__(self)
        self.name = name 
        self.value = value
    
    def set(self, val):
        self.value = val
    
    def get(self):
        return self.value
    
    def _flush(self, to):
        to.write(self.name + "=\"" + self.value + "\"\n")

class ro_array(statement):
    def __init__(self, name, value):
        statement.__init__(self)
        self.name = name
        self.value = value
    
    def set(self, val):
        self.value = val
    
    def get(self):
        return self.value
    
    def _flush(self, to):
        to.write("foreach_%s() {\n" % self.name)
        if len(self.value) == 0:
            to.write("true\n")
        for item in self.value:
            to.write("$@ ")
            if type(item) != str:
                for v in item:
                    to.write(" \"%s\" " % v)
            else:
                to.write(" \"%s\" " % item)
            to.write("\n")
        to.write("}\n")

class rw_array(statement):
    def __init__(self, name, value):
        statement.__init__(self)
        self.name = name
        self.value = value
    
    def set(self, val):
        self.value = val
    
    def get(self):
        return self.value
    
    def _flush(self, to):
        to.write("ar_init %s\n" % self.name)
        for item in self.value:
            to.write("ar_update %s \"" % self.name)
            if type(item) != str:
                for v in item:
                    to.write(" %s " % v)
            else:
                to.write(" %s " % item)
            to.write("\"\n")

class module(statement):
    mod = None
    deps_satisfied = False
    
    def __init__(self, Mod):
        statement.__init__(self)
        self.mod = Mod
        self.deps_satisfied = False
        self.name = Mod.name
    
    def _flush(self, to):
        self.mod.flush(to)

class ModuleCompilerException(Exception):
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message


class Module:
    base_paths = ["./"]
    
    def get_valid_path(self, path, start_with, end_with):
        if os.path.isfile(path):
            return path
        
        for base_path in self.base_paths:
            if os.path.isfile(base_path + path):
                return  base_path + path
            elif os.path.isfile(base_path + start_with + path + end_with):
                return base_path + start_with + path + end_with
        raise Exception("Invalid file name '" + path + "'")
    
    def __init__(self, path, end_with = ".module",start_with="qxpacker.", base_paths = ['./']):
        self.base_paths = base_paths
        self.flushed = False
        self.path = path
        self.name = os.path.basename(path)[len(start_with):-len(end_with)]
        if self.name == "":
            self.name = os.path.basename(path)
        
        if not os.path.isfile(path):
            self.path = self.get_valid_path(path,start_with, end_with)
        
        self.desc = open(self.path,"r")
        self.req_mods=[]
        req_pattern = re.compile('^\#[\ \t]*REQUIRE[\ ]*:([a-zA-Z\ \,]+)$')
        ls = self.desc.readlines()
        for l in ls:
            if req_pattern.match(l):
                req_mod_string = req_pattern.search(l).group(1)
                self.req_mods = [ x.strip() for x in req_mod_string.split(',')]
    
    def content(self):
        self.desc.seek(0)
        return self.desc.read()
    
    def __str__(self):
        return "Module : %s (%s). Reqs : %s" % (self.name,self.path,str(self.req_mods))
    
    def reset(self):
        self.flushed = False
    
    def flush(self, to):
        if self.flushed:
           return 
        self.flushed = True
        to.write(self.content())

name_seq_counter = 0
class ShellScriptBuilder:
    path = ["./"]
    statements = [custom_string("header", "#!/bin/sh")]
    default_statements_en = False
    avail_modules = {}
    
    def __str__(self):
        return "ShellScriptBuilder instance (%d statement, %d flushed)" % (len(self.statements),
                                        len([s for s in self.statements if s.flushed]))
    
    def add_path(self, new_path):
        if isinstance(new_path, list):
            self.path += new_path
        else:
            self.path.append(new_path)
        self.avail_modules = {}
        
        for p in self.path:
            self.detect_modules(p, self.avail_modules)
    
    def __init__(self, context_path = None):
        if context_path == None:
            self.path = ["./"]
        else:
            self.path = context_path
        for p in self.path:
            self.detect_modules(p, self.avail_modules)
        
    def __setattr__(self, name, value):
        for s in self._stmt(name = name):
            s.set(value)
    
    def __getattr__(self, name):
        sl = [ s.get() for s in self._stmt(name = name) ]
        return sl
    
    
    def script(self, script_path):
        if not os.path.isfile(script_path):
            for p in self.path:
                if os.path.isfile(p + '/' + script_path):
                    script_path = p + '/' + script_path
                    break
            if not os.path.isfile(script_path):
                raise Exception("Bad filename passed Paths:(" + str(self.path) + "). Target : " + script_path )
        s = Module(script_path , "" , "", base_paths = self.path)
        self.statements.append(module(s))
    
    def string(self,string,name=str(name_seq_counter)):
        global name_seq_counter
        self.statements.append(custom_string(name,string))
        name_seq_counter+=1
        
    def detect_modules(self, path = os.path.abspath(__file__), mods = {}):
        if not os.path.isdir(path):
            return
        cur_dir=os.path.dirname(path)
        for file in os.listdir(cur_dir):
            if (file.endswith('.module') and file.startswith('qxpacker.')):
                m = Module(cur_dir + '/' + file, base_paths = self.path)
                mods[m.name] = m
        return mods
    
    def _find_missing_modules(self,req_modules):
        req_set = set()
        present_set = set()
        for (k,v) in self.avail_modules.items():
            present_set.add(k)
        
        for (name, req) in req_modules.items():
            for v in req:
                req_set.add(v)
        return ' , '.join(req_set - present_set)
    
    # Resolve dependences from self.modules. 
    # Return list where each element contain list of modules to start
    # Now work at n^2 time, but it more simpler solution
    def _build_dependencies(self, mods):
        mod_reqs = {}

        # Collect needed dependences
        mods = mods[:]
        while len(mods):
            reqs = set()
            for name in mods:
                if name not in self.avail_modules:
                    raise ModuleCompilerException("\nCannot resolve. Missing module : " + name )
                mod_reqs[name] = self.avail_modules[name].req_mods[:]
                reqs |= set(self.avail_modules[name].req_mods)
            mods = list(reqs)
        
        stages = []
        curr_stage=0
        sh=True
        while sh:
            sh=False
            stages.append([])
            curr_stage=len(stages)-1
            for (name,reqs) in mod_reqs.items():
                if len(reqs) == 0:
                    sh=True
                    stages[curr_stage].append(name)
                    for (_,reqs) in mod_reqs.items():
                        if name in reqs:
                            reqs.remove(name)
                    del mod_reqs[name]
            curr_stage+=1
        if len(mod_reqs):
            mods = ' , '.join([x for (x,_) in mod_reqs.items()])
            mm = self._find_missing_modules(mod_reqs)
            error_couse=""
            if len(mm) == 0:
                error_couse += "\nPosible error - recursive dependecies"
            else:
                error_couse = "\nMissing modules : " + mm
            raise ModuleCompilerException("\nCannot resolve following modules : " + mods + error_couse )
        return stages
    
    def require(self, modname):
        modlist = self._stmt(module, modname)
        if len(modlist):
            return
        self.statements.append(module(Module(modname, base_paths = self.path)))
    
    def gather_reqs(self):
        req_mods = []
        for script in self.scripts:
            req_mods += script.req_mods
        req_mods += self.req_extend_mods
        return req_mods
    
    def reset(self):
        for s in self.statements:
            s.reset()
    
    def constant(self, name, value = None):
        if value != None:
            self.statements.append(constant(name,value))
        else:
            return self._stmt(constant, name)
    
    def _stmt(self, types = None,  name = None):
        if types == None:
            return [s for s in self.statements if ((s.name == name) or (name == None))]
        else:
            return [s for s in self.statements if (isinstance(s,types) and ((s.name == name) or (name == None)))]
    
    def array(self, name, listvar = None, editable = False):
        if listvar != None:
            if editable:
                self.statements.append(rw_array(name, listvar))
            else:
                self.statements.append(ro_array(name, listvar))
        else:
            self._stmt((rw_array, ro_array), name)
    
    def _stmt_idx(self, stmt):
        return self.statements.index(stmt)
    
    def flush(self, to):
        
        # Collecting required modules and find maximum statement identifier
        # for inserting all required modules in output program
        insert_idx = sys.maxint
        req_mods = []
        for s in [s for s in self._stmt(module) if not s.deps_satisfied]:
            s.deps_satisfied = True
            req_mods += [m for m in s.mod.req_mods if not m in req_mods]
            id = self._stmt_idx(s)
            if id < insert_idx:
                insert_idx = id
        
        if insert_idx == sys.maxint:
            insert_idx = 1
        
        # Building dependecies list and inserting required dependencies 
        # to statement list
        already_added_names = [s.mod.name for s in self._stmt(module)]
        deplist = self._build_dependencies(req_mods)
        
        for stage in deplist:
            for mod in stage:
                if mod in already_added_names:
                    lst = [s for s in self._stmt(module) if s.name == mod]
                    for s in lst:
                        self.statements.remove(s)
                self.statements.insert(insert_idx, module(Module(mod, base_paths = self.path)))
                for s in self._stmt(module, mod): s.deps_satisfied = True
                insert_idx+=1
                    
        
        for s in self.statements:
            s.flush(to)
