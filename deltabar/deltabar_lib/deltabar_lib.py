import ac
import acsys
import sys
import time

from deltabar_lib import sim_info

from deltabar_lib import config
from deltabar_lib import lap
from deltabar_lib import lap_serialize

# Yuck this looks nasty.  It used to be inline with the code and looked better.
# TODO: move these over to the config file...
APP_WIDTH = 800
APP_HEIGHT = 85

BAR_WIDTH_HALF = APP_WIDTH / 2
BAR_HEIGHT = 50
BAR_Y = 8
BAR_SCALE = BAR_WIDTH_HALF / 2000.0  # scale 2000 milliseconds into the bar

LABEL4_Y = BAR_Y + BAR_HEIGHT - 7
LABEL4_FONT_SIZE = 28
LABEL4_WIDTH = 100
LABEL4_WIDTH_HALF = LABEL4_WIDTH / 2

BANNER_FONT_SIZE = 22
BANNER_TEXT_WIDTH = 200


FASTEST_LAP = 0
FASTEST_SECTOR = 1
SESSION_LAP = 2
SESSION_SECTOR = 3
MODES = (
  (FASTEST_LAP,    'vs best all-time lap'),
  (FASTEST_SECTOR, 'vs best all-time sectors'),
  (SESSION_LAP,    'vs best session lap'),
  (SESSION_SECTOR, 'vs best session sectors'),
)


__author__ = 'James Sanford (jsanfordgit@froop.com)'


class Delta:
  def __init__(self):
    self.data = sys.modules['deltabar'].deltabar_data
    self.lap = None
    self.last_sector = -1
    self.sector_wait = None
    self.sectors_available = False  # auto-set to True when available
    self.bar_mode = FASTEST_LAP
    self.banner_time = 0
    self.first_update = True

  def acMain(self, version):
    ac.setTitle(self.data.app_id, "")
    ac.setBackgroundOpacity(self.data.app_id, 0.6)
    ac.drawBorder(self.data.app_id, 0)
    ac.setIconPosition(self.data.app_id, 0, -10000)
    ac.setSize(self.data.app_id, APP_WIDTH, APP_HEIGHT)
    return 'deltabar'

  def acShutdown(self):
    self.data.config['bar_mode'] = self.bar_mode
    if hasattr(self, 'sector_lookup'):
      lookup = self.data.config.setdefault('sectors', {})
      lookup[ac.getTrackConfiguration(0)] = self.sector_lookup
    config.save(self.data.config)

    if hasattr(self.data, 'fastest_lap') and not self.data.fastest_lap.fromfile:
      lap_serialize.save(self.data.fastest_lap, 'best')

    for sector_number, lap in enumerate(self.data.fastest_splits):
      if lap is not None and not lap.fromfile:
        lap_serialize.save(lap, 'q{}'.format(sector_number + 1))

  def reinitialize_app(self):
    # Avoid a "sector change" until it actually changes.
    self.last_sector = sim_info.info.graphics.currentSectorIndex

    if not hasattr(self.data, 'clicklabel'):
      self.data.clicklabel = ac.addLabel(self.data.app_id, "")
      ac.addOnClickedListener(self.data.clicklabel, sys.modules['deltabar'].onClick)
    ac.setPosition(self.data.clicklabel, 0, 0)
    ac.setSize(self.data.clicklabel, APP_WIDTH, APP_HEIGHT)

    if not hasattr(self.data, 'label4'):
      self.data.label4 = ac.addLabel(self.data.app_id, "")
    ac.setPosition(self.data.label4, BAR_WIDTH_HALF, LABEL4_Y)
    ac.setSize(self.data.label4, LABEL4_WIDTH, LABEL4_FONT_SIZE)
    ac.setFontAlignment(self.data.label4, 'center')
    ac.setFontSize(self.data.label4, LABEL4_FONT_SIZE)

    if not hasattr(self.data, 'label7'):
      self.data.label7 = ac.addLabel(self.data.app_id, 'p7')
    ac.setPosition(self.data.label7,
                   BAR_WIDTH_HALF - 100, LABEL4_Y + LABEL4_FONT_SIZE)
    ac.setSize(self.data.label7, 200, BANNER_FONT_SIZE)
    ac.setFontAlignment(self.data.label7, 'center')
    ac.setFontSize(self.data.label7, BANNER_FONT_SIZE)
    ac.setText(self.data.label7, "")

    ac.setFontColor(self.data.label4, 0.0, 0.0, 0.0, 1.0)
    ac.setFontColor(self.data.label7, 0.0, 0.0, 0.0, 1.0)

    track = ac.getTrackConfiguration(0)

    if not hasattr(self.data, 'config'):
      self.data.config = config.load()
      if 'bar_mode' in self.data.config:
        self.bar_mode = self.data.config['bar_mode']
      if ('sectors' in self.data.config and
          track in self.data.config['sectors']):
        self.sector_lookup = self.data.config['sectors'][track]

    if not hasattr(self.data, 'fastest_lap'):
      rlap = lap_serialize.load(track, ac.getCarName(0), 'best')
      if rlap is not None:
        self.data.fastest_lap = rlap

    if not hasattr(self.data, 'fastest_splits'):
      self.data.fastest_splits = []
      for sector_number in range(sim_info.info.static.sectorCount):
        rlap = lap_serialize.load(track,
                                  ac.getCarName(0),
                                  'q{}'.format(sector_number + 1))
        self.data.fastest_splits.append(rlap)  # May be None

    if not hasattr(self.data, 'session_splits'):
      self.data.session_splits = [None] * sim_info.info.static.sectorCount

  def init_lap(self):
    self.lap.track = ac.getTrackConfiguration(0)
    self.lap.car = ac.getCarName(0)
    self.lap.lap_number = ac.getCarState(0, acsys.CS.LapCount)
    self.lap.splits = [0] * sim_info.info.static.sectorCount
    self.lap.invalid_sectors = [False] * sim_info.info.static.sectorCount

  def finalize_lap(self):
    if sim_info.info.graphics.iLastTime:
      self.lap.complete = True
      self.lap.lap_time = sim_info.info.graphics.iLastTime
      # Splits come from update_sector.

    self.lap.tires = sim_info.info.graphics.tyreCompound
    self.lap.timestamp = time.time()

    if self.lap.complete and not self.lap.invalid:
      if (not hasattr(self.data, 'fastest_lap') or
          self.lap.lap_time < self.data.fastest_lap.lap_time):
        self.data.fastest_lap = self.lap
      if (not hasattr(self.data, 'session_lap') or
          self.lap.lap_time < self.data.session_lap.lap_time):
        self.data.session_lap = self.lap

  def acUpdate(self, delta_t):
    if sim_info.info.graphics.status != sim_info.AC_LIVE:
      return

    if self.first_update:
      self.first_update = False
      self.reinitialize_app()

    pos = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)

    if self.lap is None:
      if pos > 0.5:
        # We are coming up on the start line, wait until we cross it.
        return
      else:
        self.lap = lap.Lap()
        self.init_lap()

    current_lap = ac.getCarState(0, acsys.CS.LapCount)
    current_sector = sim_info.info.graphics.currentSectorIndex

    if not self.sectors_available:
      # See if they have become available now.
      if current_sector > 0:
        self.sectors_available = True
      else:
        # Use lookup table.
        # However, beware of the car jumping position (vallelunga).
        current_sector = self.get_sector(current_lap, pos)

    use_sector = self.check_sector(current_lap, current_sector, pos)

    if self.lap.lap_number != current_lap:
      self.finalize_lap()
      self.lap = lap.Lap()
      self.init_lap()

    elapsed_seconds = ac.getCarState(0, acsys.CS.LapTime)
    speed_ms = ac.getCarState(0, acsys.CS.SpeedMS)
    throttle_pct = ac.getCarState(0, acsys.CS.Gas)
    brake_pct = ac.getCarState(0, acsys.CS.Brake)
    steering_angle = sim_info.info.physics.steerAngle
    gear = ac.getCarState(0, acsys.CS.Gear)
    distance = sim_info.info.graphics.distanceTraveled
    self.lap.add(pos, elapsed_seconds, speed_ms,
                 throttle_pct, brake_pct, steering_angle,
                 gear, distance)

    if (ac.getCarState(0, acsys.CS.LapInvalidated) or
        sim_info.info.physics.numberOfTyresOut > 2):
      self.lap.invalid = True
      if use_sector:
        self.lap.invalid_sectors[current_sector] = True

    if self.bar_mode == FASTEST_LAP:
      if hasattr(self.data, 'fastest_lap'):
        self.update_bar_data(self.data.fastest_lap, -1, pos,
                             elapsed_seconds, speed_ms, 0, 0)
      else:
        self.clear_screen_data()
    elif self.bar_mode == SESSION_LAP:
      if hasattr(self.data, 'session_lap'):
        self.update_bar_data(self.data.session_lap, -1, pos,
                             elapsed_seconds, speed_ms, 0, 0)
      else:
        self.clear_screen_data()
    elif not use_sector:
      self.clear_screen_data()
    else:
      if self.bar_mode == FASTEST_SECTOR:
        fastest = self.data.fastest_splits[current_sector]
      elif self.bar_mode == SESSION_SECTOR:
        fastest = self.data.session_splits[current_sector]
      else:
        fastest = None

      if fastest is None:
        self.clear_screen_data()
      else:
        # We could cache this and only update it in update_sector.
        min1 = sum(self.lap.splits[0:current_sector])
        min2 = sum(fastest.splits[0:current_sector])
        self.update_bar_data(fastest, current_sector, pos,
                             elapsed_seconds, speed_ms, min1, min2)

  def update_bar_data(self, fastest, sector, pos,
                      elapsed_seconds, speed_ms, min1, min2):
    idx = fastest.index_for_offset(pos)
    if idx >= 0:
      t = elapsed_seconds - min1 - fastest.elapsed_seconds[idx] + min2
      s = speed_ms - fastest.speed_ms[idx]

      if sector == -1:
        star = '*' if self.lap.invalid else ""
      else:
        star = '*' if self.lap.invalid_sectors[sector] else ""

      self.data.t = t
      self.data.s = s
      self.data.star = star

  def get_sector(self, current_lap, pos):
    # This is only for when currentSectorIndex is not available (multiplayer)
    if self.lap.lap_number == current_lap:
      if not hasattr(self, 'sector_lookup'):
        # sectors not available
        return -1
      elif pos >= self.sector_lookup[self.last_sector]:
        if self.last_sector < sim_info.info.static.sectorCount - 1:
          return self.last_sector + 1
    return self.last_sector

  def generate_sector_lookup(self):
    splits = ac.getLastSplits(0)
    if not 0 in splits:
      sector_lookup = []
      total = 0
      for split_time in splits[:-1]:
        total += split_time
        pos = self.lap.offset_for_elapsed(total)
        sector_lookup.append(pos)
      sector_lookup.append(0)
      self.sector_lookup = sector_lookup

  def check_sector(self, current_lap, current_sector, pos):
    # When the lap changes, currentSectorIndex still has the old value
    # for a few frames.  Use sector_wait to avoid testing sector changes
    # until both the lap and currentSectorIndex have changed.
    if (self.sector_wait is not None and
        self.sector_wait != (current_lap, current_sector)):
      return False  # currentSectorIndex is not yet valid

    self.sector_wait = None

    if self.lap.next_offset_ok(pos) and current_sector > self.last_sector:
      self.last_sector = current_sector
      self.update_sector(current_sector)

    if self.lap.lap_number != current_lap:
      self.update_sector(0)
      self.last_sector = 0
      self.sector_wait = (current_lap, 0)
      return False  # currentSectorIndex is not yet valid

    return True

  def update_sector(self, new_sector):
    if new_sector == 0:
      if self.sectors_available:
        # On a new lap, lastSectorTime is not immediately available
        sector_time = ac.getLastSplits(0)[-1]
      else:
        sector_time = sim_info.info.graphics.iLastTime - sum(self.lap.splits)
        sector_time = max(0, sector_time)

      if not hasattr(self, 'sector_lookup'):
        self.generate_sector_lookup()
    else:
      # Normal new sector update
      if self.sectors_available:
        sector_time = sim_info.info.graphics.lastSectorTime
      else:
        sector_time = ac.getCarState(0, acsys.CS.LapTime) - sum(self.lap.splits)
        sector_time = max(0, sector_time)
    # ^ TODO? refactor above to "get_sector_time"?

    sector_number = new_sector - 1  # 'last'
    if sector_number == -1:
      sector_number = sim_info.info.static.sectorCount - 1

    # Always record the time, even if the lap is invalid.
    self.lap.splits[sector_number] = sector_time

    # But do not check for fastest when invalid, just bail out.
    if self.lap.invalid_sectors[sector_number]:
      return

    # Should not really happen except maybe on initial sector discovery.
    # This also happens when 'reset session' is used.
    if sector_time == 0:
      return

    fastest = self.data.fastest_splits
    if (fastest[sector_number] is None or
        not fastest[sector_number].splits[sector_number] or
        sector_time < fastest[sector_number].splits[sector_number]):
      fastest[sector_number] = self.lap

    session = self.data.session_splits
    if (session[sector_number] is None or
        not session[sector_number].splits[sector_number] or
        sector_time < session[sector_number].splits[sector_number]):
      session[sector_number] = self.lap

  def clear_screen_data(self):
    ac.setText(self.data.label4, "") # delta text
    if hasattr(self.data, 't'):
      del self.data.t
    if hasattr(self.data, 's'):
      del self.data.s

  def show_banner(self, duration, text):
    self.banner_time = time.time() + duration
    ac.setText(self.data.label7, text)

  def check_banner(self):
    if self.banner_time != 0 and time.time() >= self.banner_time:
      self.banner_time = 0
      ac.setText(self.data.label7, "")

  def draw_delta_bar(self, time_delta, speed_delta):
    # NOTE: Scale from 0.0 meters/sec = 1.0  to  5.0 meters/sec = 0.0
    #       If you change 5.0, change 0.2 to 1/new_value
    x = 1.0 - (min(abs(speed_delta), 5.0) * 0.2)
    if speed_delta >= 0.0:
      colors = (x, 1.0, x, 1.0)
    else:
      colors = (1.0, x, x, 1.0)

    original_time_delta = time_delta
    if time_delta > 2000:
      time_delta = 2000
    elif time_delta < -2000:
      time_delta = -2000

    # 800 width area, 400 is the middle, 400/2000 is 0.20
    if time_delta >= 0:
      offset = BAR_WIDTH_HALF
    else:
      offset = BAR_WIDTH_HALF + int(time_delta * BAR_SCALE)
    width = int((abs(time_delta) * BAR_SCALE))
    # TODO: consider only using hundredths to pick offset+width,
    # so that position changes only happen when the text changes as well

    if width > 0:
      ac.glColor4f(*colors)
      ac.glQuad(offset, BAR_Y, width, BAR_HEIGHT)  # starts at y=0, is 50 high

    if time_delta >= 0:
      ac.setPosition(self.data.label4,
                     min(offset + width - LABEL4_WIDTH_HALF,
                         APP_WIDTH - LABEL4_WIDTH),
                     LABEL4_Y)
      ac.setFontColor(self.data.label4, 1.0, 0.1, 0.1, 1.0)
    else:
      ac.setPosition(self.data.label4,
                     max(0, offset - LABEL4_WIDTH_HALF),
                     LABEL4_Y)
      ac.setFontColor(self.data.label4, 0.1, 1.0, 0.0, 1.0)

    plus = '-' if original_time_delta < 0 else '+'
    star = '*' if self.data.star else ""
    # NOTE: The below .format()s are too much magic.
    #       We want 234 to be '0.23' and 12345 to be '12.34'
    ms = '{:04d}'.format(abs(original_time_delta))
    ac.setText(self.data.label4,
               '{}{}{}.{}'.format(plus, star, ms[0:-3], ms[-3:-1]))

  def onRender(self, delta_t):
    if (self.lap is None or
        sim_info.info.graphics.status not in (sim_info.AC_LIVE,
                                              sim_info.AC_PAUSE)):
      # Clear out all visible text and bail out.
      self.clear_screen_data()
      return

    if hasattr(self.data, 't') and hasattr(self.data, 's'):
      self.draw_delta_bar(self.data.t, self.data.s)
    else:
      self.clear_screen_data()

    self.check_banner()

  def onClick(self):
    self.bar_mode += 1
    if self.bar_mode >= len(MODES):
      self.bar_mode = 0
    self.show_banner(2.0, MODES[self.bar_mode][1])


deltabar_app = Delta()
