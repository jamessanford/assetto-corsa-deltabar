#!/usr/bin/python3

# PYRO_LOGFILE="{stderr}" PYRO_LOGLEVEL=DEBUG

import sys
import time

import Pyro4.core
import Pyro4.utils.flame

Pyro4.config.SERIALIZER = "pickle"  # flame requires pickle serializer
Pyro4.config.PICKLE_PROTOCOL_VERSION = 3

def main(args):
  #location = "localhost:9999"
  location = "192.168.1.41:9999"
  flame = Pyro4.core.Proxy("PYRO:%s@%s" % (Pyro4.constants.FLAME_NAME, location))
  #flame._pyroHmacKey = "FOO"
  flame._pyroBind()

  # print something to the remote server output
  #flame.builtin("print")("Hello there, remote server stdout!")

  if len(args) < 2:
    args.append('help')  # you need help

  # remote console
  if args[1] == 'console':
    with flame.console() as console:
      console.interact()
  elif args[1] == 'send':
    flame.evaluate("setattr(sys.modules['deltabar'], 'has_error', True)")  # HACK FIXME TODO, this pauses acUpdate while we reload the module
    time.sleep(0.1)  # HACK
#    sys.exit(1)  # FIXME
    for filename in ("sim_info.py", "config.py", "lap.py", "lap_serialize.py", "statusbox.py", "deltabar_lib.py"):
      modulename = filename[:filename.rindex(".py")]
      modulesource = open("deltabar_lib/" + filename).read()
      flame.sendmodule("deltabar_lib." + modulename, modulesource)
# lame, this is not exposed:
#      flame.createModule(modulename, modulesource, filename=filename)
    time.sleep(0.1)  # HACK
    flame.evaluate("setattr(sys.modules['deltabar'], 'has_error', False)")
  elif args[1] in ('error', 'errors', 'watch'):
    while True:
      logged_errors = flame.evaluate("sys.modules['deltabar'].logged_errors")
#      print(logged_errors)
#      sys.exit(0)
#      delta = flame.module('deltabar')
#      print(list(delta.logged_errors))
#      import code
#      foo = globals().copy()
#      foo.update(locals())
#      code.InteractiveConsole(locals=foo).interact()
      for error in logged_errors:
        print(error)
      if args[1] == 'watch':
        time.sleep(1)
        print()
      else:
        break
  else:
    print("use 'console', 'send', or 'errors' command")
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv)
