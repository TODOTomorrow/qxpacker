qxpacker- is utility to generate auto self-extracting packages.

Advantages:
* Created installation packages does not require additional utilites, except POSIX shell, mkdir and chmod utilites on target system
* qxpacker can generate installation packages in archive mode(use tar utility)
* Author can inject custom code in installation package. This make installation package more flexible

# Installation

qxpacker doesnot require installation. But for more usability you can copy all files with .py extension and file qxpacker.startup.script to directory, contained in $PATH variable (/usr/local/bin for example). 

# Creating install package
To see help for syntax type:
```
# qxpacker --help
```

To create package with name mypack.sh, contained directory dir1 and file file1 use following syntax:
```
# qxpacker dir1 file1 -o mypack.sh
```

To determine specific target path (usr/bin for example), use following:
```
# qxpacker -r usr/bin dir1 file1 -o mypack.sh
```
After this all files and directories after options -r usr/bin will put into directory usr/bin on target system.

To call custom shell code (for example "echo Hello world!"), use following:
```
# qxpacker -s "echo Hello world" -r usr/bin dir1 file1 -o mypack.sh
```
After this command "echo Hello world" will be called while installation going.

# Installation created package

To install package use following syntax:
```
# <package_name> [<installation_path>]
```
If installation path not specified it will be set into ./(current directory)

# Inside startup code

In startup code (begin, startup or after code), you can use some system variables and functions:

### Global variables:

| Variable definition | Description | Access mode |
|:-------------------:|:-----------:|:-----------:|
| TARGET_DIR=\<DIRNAME\> | directory to extracting files and directories (may be passed as parameter to installer). | read-write |
| BE_VERBOSE=\<True\|False\> | verbose mode flag | read-write |
| SELFNAME=\<File\> | path to current installer file | read-only |
| INSTALLER_TMPDIR=\<Dir\> | directory to save some temproray files | read-only |
| INSTALLER_UID=\<Number\> | unical ID of installer | read-only |
| EXTRACTOR_TYPE=\<dd\|shell\> | type of extractor (dd utility, or shell commands) | read-only |
| PAYLOAD_TYPE=\<tar\|shell\> | type of payload (tar archive, or shell commands) | read-only |

