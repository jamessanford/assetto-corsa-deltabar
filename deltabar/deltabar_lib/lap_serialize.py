
import array
import json
import os
import zipfile

from deltabar_lib import config
from deltabar_lib import lap


# Encoder for lap.Lap objects into JSON.
#   We lose the reason for using array.array() by doing this, but that is OK.

# Use lap_serializer.encode(obj) and lap_serializer.decode(str)
#   or
# lap_serializer.save(obj) and lap_serializer.load(track_config, car, lap.BEST)

def to_json(obj):
  if isinstance(obj, lap.Lap):
    return {'__lap__': obj.__dict__}
  if isinstance(obj, array.array):
    return {'__array__': list(obj), '__array_typecode__': obj.typecode}
  return json.JSONEncoder().encode(obj)


def from_json(item):
  if '__lap__' in item:
    lap_obj = lap.Lap()
    lap_obj.__dict__ = item['__lap__']
    return lap_obj
  if '__array__' in item:
    return array.array(item['__array_typecode__'], item['__array__'])
  return item


def encode(lap_obj):
  return json.dumps(lap_obj, default=to_json)


def decode(json_str):
  return json.loads(json_str, object_hook=from_json)


def get_path(track, car, lap_type):
  path = os.path.join(config.get_config_path(), 'laps', track)
  filename = '{}_{}'.format(car, lap_type)
  return path, filename, 'txt'


def save(lap_obj, lap_type):
  # lap_type == 'best', 's1', 's2', ...
  if not (lap_obj.track and lap_obj.car):
    # TODO: log error, 'tried to save incomplete lap object'
    return

  path, filename, ext = get_path(lap_obj.track, lap_obj.car, lap_type)
  fullpath = os.path.join(path, '{}.zip'.format(filename))

  os.makedirs(path, exist_ok=True)
  with zipfile.ZipFile(fullpath, mode='w',
                       compression=zipfile.ZIP_DEFLATED) as zip:
    zip.writestr('{}.{}'.format(filename, ext), encode(lap_obj))
  # NOTE: Errors will raise and hopefully get logged.
  #       It is no fun when your fast laps are not saved.


def load(track, car, lap_type):
  # lap_type == 'best', 'p1', 'p2', ...

  path, filename, ext = get_path(track, car, lap_type)
  fullpath = os.path.join(path, filename)
  try:
    with zipfile.ZipFile('{}.zip'.format(fullpath), mode='r') as zip:
      lap = decode((zip.read('{}.{}'.format(filename, ext))).decode('utf-8'))
      lap.fromfile = True
      return lap
  except:
    return None # NOTE: Silently fail.
