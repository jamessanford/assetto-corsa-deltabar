
import json
import os


# Inside My Documents directory.
DIR_PARTS = ('Assetto Corsa', 'plugins', 'deltabar')
CONFIG_FILENAME = 'config.txt'

# NOTE: We do NOT need to hard code the sectors,
# the plugin will learn the sectors in singleplayer mode.
# Having defaults just helps if you immediately use multiplayer mode.
CONFIG_DEFAULTS = {
  'bar_mode': 0,
  'bar_moves': True,
  'bar_smooth': True,
  'enable_timing_window': False,
  'sectors': {
    'brands-hatch': [ 0.35944467782974243, 0.7798787355422974, 0 ],
    'imola': [ 0.3146900534629822, 0.6765202879905701, 0 ],
    'monza': [ 0.3682761788368225, 0.6733852028846741, 0 ],
    'mugello': [ 0.24961651861667633, 0.5557045340538025, 0 ],
    'nurburgring': [ 0.2860076427459717, 0.6445714831352234, 0 ],
    'nurburgring-sprint': [ 0.5542691946029663, 0 ],
    'silverstone': [ 0.2581382691860199, 0.7142373323440552, 0 ],
    'silverstone-international': [ 0.49429652094841003, 0 ],
    'spa': [ 0.3253447413444519, 0.7245596051216125, 0 ],
    'suzuka_0.9': [ 0.3216688930988312, 0.7127670049667358, 0 ],
    'vallelunga-club_circuit': [ 0.422470360994339, 0 ],
    'vallelunga-extended_circuit': [ 0.4330659508705139, 0.7526666522026062, 0 ]
  }
}


# TODO: constants that eventually you can override
APP_WIDTH = 800
APP_HEIGHT = 75

BAR_WIDTH_HALF = APP_WIDTH / 2
BAR_HEIGHT = 32
BAR_Y = 0
BAR_SCALE = BAR_WIDTH_HALF / 2000.0  # scale 2000 milliseconds into the bar

LABEL4_Y = BAR_Y + BAR_HEIGHT - 7
LABEL4_FONT_SIZE = 28
LABEL4_WIDTH = 100
LABEL4_WIDTH_HALF = LABEL4_WIDTH / 2

BANNER_FONT_SIZE = 22
BANNER_TEXT_WIDTH = 200
BANNER_Y = BAR_HEIGHT + 8


# constants
FASTEST_LAP = 0
FASTEST_SECTOR = 1
FASTEST_OPTIMAL = 2
SESSION_LAP = 3
SESSION_SECTOR = 4
SESSION_OPTIMAL = 5

MODES = (
  (FASTEST_LAP,    'vs all-time best lap'),
  (FASTEST_SECTOR, 'vs all-time best sectors'),
  (FASTEST_OPTIMAL, 'vs all-time optimal lap'),
  (SESSION_LAP,    'vs session best lap'),
  (SESSION_SECTOR, 'vs session best sectors'),
  (SESSION_OPTIMAL, 'vs session optimal lap'),
)


def my_documents_dir():
  try:
    import winreg
    folder_redirection = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    return winreg.QueryValueEx(folder_redirection, 'Personal')[0]
  except:
    return '/tmp/'


def get_config_path():
  return os.path.join(my_documents_dir(), *DIR_PARTS)


def save(config_dict):
  path = get_config_path()
  filename = os.path.join(path, CONFIG_FILENAME)

  try:
    os.makedirs(path, exist_ok=True)
    with open(filename, 'w') as f:
      f.write(json.dumps(config_dict, sort_keys=True, indent=2))
  except:
    pass # NOTE: Silently fail.


def load():
  path = get_config_path()
  filename = os.path.join(path, CONFIG_FILENAME)
  try:
    with open(filename, 'r') as f:
      config_dict = json.loads(f.read())
  except:
    return CONFIG_DEFAULTS # NOTE: Silently ignore all errors.

  # Merge any newly available track sector information.
  for track in CONFIG_DEFAULTS['sectors']:
    if track not in config_dict['sectors']:
      config_dict['sectors'][track] = CONFIG_DEFAULTS['sectors'][track]

  return config_dict
