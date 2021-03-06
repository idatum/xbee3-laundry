"""Copy main.py to /flash/src on XBee via XCTU File System Manager tool.
   Paste below code using CTRL-E then CTRL-D to run via a terminal or the
   XCTU Micropython Terminal tool.
   Then reset: import machine; machine.reset()"""

import uos

try:
    # Cleanup.
    uos.remove('/flash/main.mpy')
except OSError:
    pass
# Compile.
uos.compile('/flash/src/main_laundry.py', '/flash/main.mpy')
