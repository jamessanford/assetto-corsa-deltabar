import ac
import sys
import time
import traceback

has_error = False
logged_errors = []


def log_error():
  msg = 'Exception: {}\n{}'.format(time.asctime(), traceback.format_exc())
  ac.log(msg)
  ac.console(msg)
  logged_errors.append(msg)


sys.path.insert(0, 'apps/python/deltabar/lib')


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
