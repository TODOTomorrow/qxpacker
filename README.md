qxpacker- is utility to generate auto self-extracting packages.

Advantages:
* Created installation packages does not require additional utilites, except POSIX shell, mkdir and chmod utilites on target system
* qxpacker can generate installation packages in archive mode(use tar utility)
* Author can inject custom code in installation package. This make installation package more flexible

# Installation

You can install it using pip

```
# python setup.py sdist ; pip install ./dist/qxpacker-0.1.tar.gz
```

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

To add some script file, which will be executed on installation process, use following:
```
# qxpacker -s "echo Hello world" -r usr/bin dir1 file1 -o mypack.sh
```
Note, that if you want to start your code after basic installation initialization, your code should be into main() function.

# Installation created package

To install package use following syntax:
```
# <package_name> [-t|--target <installation_path>] [-h|--help] [-i|--info] [-l|--list]
```
If installation path not specified it will be set into ./(current directory)

# Inside startup code

In startup code (begin, startup or after code), you can use some system variables and functions:


