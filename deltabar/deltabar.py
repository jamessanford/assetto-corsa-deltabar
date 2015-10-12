import ac
import os
import platform
import sys
import time
import traceback

# Nothing interesting here.  See deltabar_lib/deltabar_lib.py
#
# This is the entry point for the Assetto Corsa API,
# we wrap the API calls with some error checking and farm it
# out to our actual implementation.
#
# This wrapper allows us to replace the deltabar_lib module
# with a new version while AC is running; AC will still call
# the endpoints here but we can switch over to the new module version.

has_error = False
logged_errors = []


def log_error():
  msg = 'Exception: {}\n{}'.format(time.asctime(), traceback.format_exc())
  ac.log(msg)
  ac.console(msg)
  logged_errors.append(msg)


def get_lib_dir():
  if platform.architecture()[0] == '64bit':
    return 'lib64'
  else:
    return 'lib'


# Fix import path for sim_info ctypes
lib_dir = 'apps/python/deltabar/{}'.format(get_lib_dir())
sys.path.insert(0, lib_dir)
# I doubt this is necessary:
#os.environ['PATH'] += ';.'


class DeltaBarData:
  pass


# Important to do this before importing deltabar_lib.
deltabar_data = DeltaBarData()


try:
  from deltabar_lib.deltabar_lib import deltabar_app
except:
  log_error()
  raise


def acMain(ac_version):
  try:
    deltabar_data.app_id = ac.newApp('deltabar')
    ac.addRenderCallback(deltabar_data.app_id, onRender)

    return deltabar_app.acMain(ac_version)
  except:
    log_error()
    raise


def acUpdate(delta_t):
  global has_error
  if has_error:
    return
  try:
    deltabar_app.acUpdate(delta_t)
  except:
    log_error()
    has_error = True


def acShutdown():
  global has_error
  if has_error:
    return
  try:
    deltabar_app.acShutdown()
  except:
    log_error()
    has_error = True


def onRender(delta_t):
  global has_error
  if has_error:
    return
  try:
    deltabar_app.onRender(delta_t)
  except:
    log_error()
    has_error = True


def onClick(*args, **kwargs):
  global has_error
  if has_error:
    return
  try:
    deltabar_app.onClick()
  except:
    log_error()
    has_error = True
