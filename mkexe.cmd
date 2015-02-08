rd /s /q build
rd /s /q dist
\python27-32\python setup-exe.py py2exe
del dist\w9xpopen.exe
rd /s /q dist\tcl\tk8.5\demos
rd /s /q dist\tcl\tk8.5\images
rd /s /q dist\tcl\tcl8.5\http1.0
rd /s /q dist\tcl\tcl8.5\tzdata
rd /s /q dist\tcl\tcl8.5\opt0.4