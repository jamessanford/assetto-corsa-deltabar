CLIENT USAGE:

EDIT client_debug.py to have the .py filenames you want to send
EDIT client_debug.py IP address (192.168.1...)
EDIT deltabar/deltabar.py def pyroserver() IP address (192.168.1...)

# Send local .py files to AC plugin and perform hot-reload
linux% ./client_debug.py send


# Look at recent errors
linux% ./client_debug.py error



CONSOLE EXAMPLES:

# Interactive python prompt with AC client
linux% ./client_debug.py console
>


import sys
sys.modules['deltabar_lib'].data

sys.modules['deltabar'].deltabar_app.local_data

import sim_info
sim_info.info.static.sectorCount

import ac
import acsys
ac.getCarName(0)

dir(ac)
dir(acsys)

