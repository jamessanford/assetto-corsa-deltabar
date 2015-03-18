import ac
import acsys
import sys
import time

from deltabar_lib import sim_info

from deltabar_lib import config
from deltabar_lib import lap
from deltabar_lib import lap_serialize
from deltabar_lib import statusbox


__author__ = 'James Sanford (jsanfordgit@froop.com)'


def getSectorCount():
  return max(1, sim_info.info.static.sectorCount)


def getTrack():
  track = ac.getTrackName(0)
  track_config = ac.getTrackConfiguration(0)
  if track_config:
    track = '{}-{}'.format(track, track_config)

  return track


class LabelTracker:
  """Simple 'smoothing' for delta text changes.

  Avoid switching rapidly between two values like '-0.01' and '-0.02',
  just pick one and stick to it.
  """

  def __init__(self):
    self.bar_smooth = True
    self.old = ""
    self.last = ""

  def update(self, text):
    """Returns True if you should update the label with the new text."""
    if not self.bar_smooth:
      return True

    # We used to have a time expiration here, but it was unnecessary.
    if text == self.last or text == self.old:
      return False

    self.old = self.last
    self.last = text
    return True


class Delta:
  def __init__(self):
    self.data = sys.modules['deltabar'].deltabar_data
    self.lap = None
    self.last_sector = -1
    self.last_session = -1
    self.lap_wait = None # Delay when bailing out of invalid laps.
    self.sector_wait = None
    self.bar_mode = config.FASTEST_LAP
    self.bar_moves = True
    self.banner_time = 0
    self.first_update = True
    self.label = LabelTracker()
    self.statusbox = None

  def acMain(self, version):
    ac.setTitle(self.data.app_id, "")
    ac.setBackgroundOpacity(self.data.app_id, 0.0)
    ac.drawBorder(self.data.app_id, 0)
    ac.setIconPosition(self.data.app_id, 0, -10000)
    ac.setSize(self.data.app_id, config.APP_WIDTH, config.APP_HEIGHT)

    return 'deltabar'

  def acShutdown(self):
    self.data.config['bar_mode'] = self.bar_mode
    self.data.config['bar_moves'] = self.bar_moves
    self.data.config['bar_smooth'] = self.label.bar_smooth
    if hasattr(self, 'sector_lookup'):
      lookup = self.data.config.setdefault('sectors', {})
      lookup[getTrack()] = self.sector_lookup
    config.save(self.data.config)

    if hasattr(self.data, 'fastest_lap') and not self.data.fastest_lap.fromfile:
      lap_serialize.save(self.data.fastest_lap, 'best')

    for sector_number, lap in enumerate(self.data.fastest_splits):
      if lap is not None and not lap.fromfile:
        lap_serialize.save(lap, 'q{}'.format(sector_number + 1))

  def reinitialize_app(self):
    # Avoid a "sector change" until it actually changes.
    self.last_sector = sim_info.info.graphics.currentSectorIndex

    # Note AC_PRACTICE/AC_QUALIFY/AC_RACE transitions.
    self.last_session = sim_info.info.graphics.session

    if not hasattr(self.data, 'sectors_available'):
      # Yes, keep this in self.data, so we can hot reload and still know it.
      self.data.sectors_available = False  # auto-set to True when available

    # Only one sector? We know what sector you are in.
    if getSectorCount() == 1:
      self.data.sectors_available = True

    if not hasattr(self.data, 'clicklabel'):
      self.data.clicklabel = ac.addLabel(self.data.app_id, "")
      ac.addOnClickedListener(self.data.clicklabel, sys.modules['deltabar'].onClick)
    ac.setPosition(self.data.clicklabel, 0, 0)
    ac.setSize(self.data.clicklabel, config.APP_WIDTH, config.APP_HEIGHT)

    if not hasattr(self.data, 'bar_area'):
      self.data.bar_area = ac.addLabel(self.data.app_id, "")
    ac.setPosition(self.data.bar_area, 0, 0)
    ac.setSize(self.data.bar_area, config.APP_WIDTH, config.BAR_HEIGHT)
    # Fill 100% #999999, Fill color erase 5.7 four times
    ac.setBackgroundTexture(self.data.bar_area,
                            'apps/python/deltabar/background.png')

    if not hasattr(self.data, 'label4'):
      self.data.label4 = ac.addLabel(self.data.app_id, "")
    ac.setPosition(self.data.label4,
                   config.BAR_WIDTH_HALF - config.LABEL4_WIDTH_HALF,
                   config.LABEL4_Y)
    ac.setSize(self.data.label4,
               config.LABEL4_WIDTH,
               config.LABEL4_FONT_SIZE + 4)
    ac.setFontAlignment(self.data.label4, 'center')
    ac.setFontSize(self.data.label4, config.LABEL4_FONT_SIZE)
    # Fill 100% #999999, Fill color erase 5.7 four times
    ac.setBackgroundTexture(self.data.label4,
                            'apps/python/deltabar/textbox.png')

    if not hasattr(self.data, 'label7'):
      self.data.label7 = ac.addLabel(self.data.app_id, 'p7')
    ac.setPosition(self.data.label7,
                   config.BAR_WIDTH_HALF - 100, config.BANNER_Y)
    ac.setSize(self.data.label7, 200, config.BANNER_FONT_SIZE)
    ac.setFontAlignment(self.data.label7, 'center')
    ac.setFontSize(self.data.label7, config.BANNER_FONT_SIZE)
    ac.setText(self.data.label7, "")

    ac.setFontColor(self.data.label4, 0.0, 0.0, 0.0, 1.0)
    ac.setFontColor(self.data.label7, 0.945, 0.933, 0.102, 1.0) # yellow

    track = getTrack()

    if not hasattr(self.data, 'config'):
      self.data.config = config.load()
      if 'bar_mode' in self.data.config:
        self.bar_mode = self.data.config['bar_mode']
      if 'bar_moves' in self.data.config:
        self.bar_moves = self.data.config['bar_moves']
      if 'bar_smooth' in self.data.config:
        self.label.bar_smooth = self.data.config['bar_smooth']
      if ('sectors' in self.data.config and
          track in self.data.config['sectors']):
        self.sector_lookup = self.data.config['sectors'][track]

    if not hasattr(self.data, 'fastest_lap'):
      rlap = lap_serialize.load(track, ac.getCarName(0), 'best',
                                sector_count=getSectorCount())
      if rlap is not None:
        self.data.fastest_lap = rlap

    if not hasattr(self.data, 'fastest_splits'):
      self.data.fastest_splits = []
      for sector_number in range(getSectorCount()):
        rlap = lap_serialize.load(track,
                                  ac.getCarName(0),
                                  'q{}'.format(sector_number + 1),
                                  sector_count=getSectorCount())
        self.data.fastest_splits.append(rlap)  # May be None

    if not hasattr(self.data, 'session_splits'):
      self.data.session_splits = [None] * getSectorCount()

  def reinitialize_statusbox(self):
    field = 'enable_timing_window'
    if field not in self.data.config:
      self.data.config[field] = True

    if not self.data.config[field]:
      # Window is explicitly disabled, bail out.
      return

    if not hasattr(self.data, 'app_id2'):
      app_id2 = ac.newApp('deltabar timer')
      if app_id2 < 0:
        return # bail out, new window did not work
      else:
        self.data.app_id2 = app_id2

    ac.setTitle(self.data.app_id2, "")
    ac.setBackgroundOpacity(self.data.app_id2, 0.5)
    ac.drawBorder(self.data.app_id2, 0)
    ac.setIconPosition(self.data.app_id2, 0, -10000)
    ac.setSize(self.data.app_id2, 300, 200)

    self.statusbox = statusbox.StatusBox(self.data, getSectorCount(),
                                         bar_mode=self.bar_mode)
    self.statusbox.update_all(self.bar_mode)

  def init_lap(self):
    self.lap.track = getTrack()
    self.lap.car = ac.getCarName(0)
    self.lap.lap_number = ac.getCarState(0, acsys.CS.LapCount)
    self.lap.splits = [0] * getSectorCount()
    self.lap.invalid_sectors = [False] * getSectorCount()

  def finalize_lap(self):
    if sim_info.info.graphics.iLastTime:
      self.lap.complete = True
      self.lap.lap_time = sim_info.info.graphics.iLastTime
      # Splits come from update_sector.

    self.lap.tires = sim_info.info.graphics.tyreCompound
    self.lap.timestamp = time.time()

    # Update statusbox before we update the fastest lap times,
    # so that the statusbox can show deltas to what "was" the fastest.
    if self.statusbox is not None:
      self.statusbox.update_diff(self.lap)

    if self.lap.complete and not self.lap.invalid:
      if (not hasattr(self.data, 'fastest_lap') or
          self.lap.lap_time < self.data.fastest_lap.lap_time):
        self.data.fastest_lap = self.lap
      if (not hasattr(self.data, 'session_lap') or
          self.lap.lap_time < self.data.session_lap.lap_time):
        self.data.session_lap = self.lap

    # Now show the actual last lap time...
    if self.statusbox is not None:
      self.statusbox.update_last(self.lap)

  def acUpdate(self, delta_t):
    if sim_info.info.graphics.status != sim_info.AC_LIVE:
      return

    if self.first_update:
      self.first_update = False
      self.reinitialize_app()
      self.reinitialize_statusbox()

    pos = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)

    if self.lap is None:
      if self.lap_wait is not None:
        if time.time() < self.lap_wait:
          return
        else:
          self.lap_wait = None

      if ac.getCarState(0, acsys.CS.LapTime) == 0:
        # Only record once the clock is ticking.
        return
      elif pos > 0.5:
        # It appears we have not reached the start line yet.
        # Or at least, not that we know about.
        return
      else:
        self.lap = lap.Lap()
        self.init_lap()

    current_lap = ac.getCarState(0, acsys.CS.LapCount)
    current_sector = sim_info.info.graphics.currentSectorIndex

    # NOTE: When acsys.CS.LapInvalidated works, add here or at numberOfTyresOut.
    # Exceptional cases that we need to handle first.
    if (current_lap < self.lap.lap_number
        or sim_info.info.graphics.session != self.last_session):
      # Lap number decreased?
      # Session was reset or changed between practice/qualifying/race?
      self.last_session = sim_info.info.graphics.session

      # Abandon the lap and start over.
      self.clear_screen_data()
      self.lap = None
      self.lap_wait = time.time() + 2.0  # Do not begin a new lap for 2 seconds.
      return

    if not self.data.sectors_available:
      # See if they have become available now.
      if current_sector > 0:
        self.data.sectors_available = True
      else:
        # Use lookup table.
        # However, beware of the car jumping position (vallelunga).
        current_sector = self.get_sector(current_lap, pos)

    use_sector = self.check_sector(current_lap, current_sector, pos)

    if self.lap.lap_number != current_lap:
      self.finalize_lap()
      self.lap = None
      self.clear_screen_data()
      return

    elapsed_seconds = ac.getCarState(0, acsys.CS.LapTime)
    speed_ms = ac.getCarState(0, acsys.CS.SpeedMS)
    self.lap.add(pos, elapsed_seconds, speed_ms,
                 ac.getCarState(0, acsys.CS.Gas),
                 ac.getCarState(0, acsys.CS.Brake),
                 sim_info.info.physics.steerAngle,
                 ac.getCarState(0, acsys.CS.Gear),
                 sim_info.info.graphics.distanceTraveled)

    if sim_info.info.physics.numberOfTyresOut > 2:
      self.lap.invalid = True
      if use_sector:
        self.lap.invalid_sectors[current_sector] = True

    if self.statusbox is not None and use_sector and current_sector >= 0:
      self.statusbox.update_frame(self.lap, elapsed_seconds, current_sector,
                                  pos, self.lap.invalid_sectors[current_sector])

    if self.bar_mode == config.FASTEST_LAP:
      if hasattr(self.data, 'fastest_lap'):
        self.update_bar_data(self.data.fastest_lap, -1, pos,
                             elapsed_seconds, speed_ms, 0, 0)
      else:
        self.clear_screen_data()
    elif self.bar_mode == config.SESSION_LAP:
      if hasattr(self.data, 'session_lap'):
        self.update_bar_data(self.data.session_lap, -1, pos,
                             elapsed_seconds, speed_ms, 0, 0)
      else:
        self.clear_screen_data()
    elif not use_sector:
      self.clear_screen_data()
    else:
      if self.bar_mode == config.FASTEST_SECTOR:
        fastest = self.data.fastest_splits[current_sector]
      elif self.bar_mode == config.SESSION_SECTOR:
        fastest = self.data.session_splits[current_sector]
      elif self.bar_mode == config.FASTEST_OPTIMAL:
        # TODO: Clean this up!  It is not pretty but it works.
        fastest = self.data.fastest_splits[current_sector]
        if fastest is None:
          self.clear_screen_data()
          return
        min1 = 0
        min2 = sum(fastest.splits[0:current_sector])
        for _sector in range(current_sector):
          _sector_lap = self.data.fastest_splits[_sector]
          if _sector_lap is None:
            self.clear_screen_data()
            return
          min1 += _sector_lap.splits[_sector]
        self.update_bar_data(fastest, -1, pos,  # -1 means use lap.invalid.
                             elapsed_seconds, speed_ms, min1, min2)
        return
      elif self.bar_mode == config.SESSION_OPTIMAL:
        fastest = self.data.session_splits[current_sector]
        if fastest is None:
          self.clear_screen_data()
          return
        min1 = 0
        min2 = sum(fastest.splits[0:current_sector])
        for _sector in range(current_sector):
          _sector_lap = self.data.session_splits[_sector]
          if _sector_lap is None:
            self.clear_screen_data()
            return
          min1 += _sector_lap.splits[_sector]
        self.update_bar_data(fastest, -1, pos,  # -1 means use lap.invalid.
                             elapsed_seconds, speed_ms, min1, min2)
        return
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
        if self.last_sector < getSectorCount() - 1:
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
      if self.data.sectors_available:
        # On a new lap, lastSectorTime is not immediately available
        sector_time = ac.getLastSplits(0)[-1]
      else:
        sector_time = sim_info.info.graphics.iLastTime - sum(self.lap.splits)
        sector_time = max(0, sector_time)

      if not hasattr(self, 'sector_lookup'):
        self.generate_sector_lookup()
    else:
      # Normal new sector update
      if self.data.sectors_available:
        sector_time = sim_info.info.graphics.lastSectorTime
      else:
        sector_time = ac.getCarState(0, acsys.CS.LapTime) - sum(self.lap.splits)
        sector_time = max(0, sector_time)
    # ^ TODO? refactor above to "get_sector_time"?

    sector_number = new_sector - 1  # 'last'
    if sector_number == -1:
      sector_number = getSectorCount() - 1

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

    # Now show the actual optimal time...
    if self.statusbox is not None:
      self.statusbox.update_optimal()

  def clear_screen_data(self):
    ac.setVisible(self.data.label4, 0) # delta text
    ac.setText(self.data.label4, "")
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
    plus = '-' if time_delta < 0 else '+'
    # NOTE: The below .format()s are too much magic.
    #       We want 234 to be '0.23' and 12345 to be '12.34'
    ms = '{:04d}'.format(abs(int(time_delta)))
    label_text = '{}{}{}.{}'.format(plus, self.data.star, ms[0:-3], ms[-3:-1])
    label_changed = self.label.update(label_text)

    # NOTE: Scale from 0.0 meters/sec = 1.0  to  5.0 meters/sec = 0.0
    #       If you change 5.0, change 0.2 to 1/new_value
    x = 1.0 - (min(abs(speed_delta), 5.0) * 0.2)
    if speed_delta >= 0.0:
      colors = (x, 1.0, x, 1.0)
    else:
      colors = (1.0, x, x, 1.0)

    if time_delta > 2000:
      time_delta = 2000
    elif time_delta < -2000:
      time_delta = -2000

    # 800 width area, 400 is the middle, 400/2000 is 0.20
    if time_delta < 0:
      offset = config.BAR_WIDTH_HALF
    else:
      offset = config.BAR_WIDTH_HALF - int(time_delta * config.BAR_SCALE)
    width = int((abs(time_delta) * config.BAR_SCALE))

    if width > 0:
      ac.glColor4f(*colors)
      ac.glQuad(offset, config.BAR_Y, width, config.BAR_HEIGHT)

    if not label_changed:
      # bail out, do not change the actual label (and do not move it)
      return

    if time_delta < 0:
      ac.setFontColor(self.data.label4, 0.3, 1.0, 0.3, 1.0)
      if self.bar_moves:
        ac.setPosition(self.data.label4,
                       min(offset + width - config.LABEL4_WIDTH_HALF,
                           config.APP_WIDTH - config.LABEL4_WIDTH),
                       config.LABEL4_Y)
    else:
      ac.setFontColor(self.data.label4, 0.85, 0.15, 0.15, 1.0)
      if self.bar_moves:
        ac.setPosition(self.data.label4,
                       max(0, offset - config.LABEL4_WIDTH_HALF),
                       config.LABEL4_Y)

    ac.setText(self.data.label4, label_text)

  def onRender(self, delta_t):
    if self.first_update:
      return # bail out, nothing is ready

    if (sim_info.info.graphics.status not in (sim_info.AC_LIVE,
                                              sim_info.AC_PAUSE)):
      ac.setVisible(self.data.bar_area, 0)
      ac.setVisible(self.data.label4, 0)
      self.clear_screen_data()
    elif hasattr(self.data, 't') and hasattr(self.data, 's'):
      ac.setVisible(self.data.bar_area, 1)
      ac.setVisible(self.data.label4, 1)
      self.draw_delta_bar(self.data.t, self.data.s)
    else:
      ac.setVisible(self.data.bar_area, 1)
      self.clear_screen_data()

    if self.banner_time == 0:
      ac.setBackgroundOpacity(self.data.app_id, 0.0)

    self.check_banner()

  def onClick(self):
    if self.first_update:
      return # bail out, nothing is ready

    if self.banner_time == 0:
      current_mode = config.MODES[self.bar_mode][1]
      self.show_banner(2.2, '{}\n(click again to toggle)'.format(current_mode))
      return

    self.bar_mode += 1
    if self.bar_mode >= len(config.MODES):
      self.bar_mode = 0
    self.show_banner(2.2, config.MODES[self.bar_mode][1])

    if self.statusbox is not None:
      # TODO FIXME NOTE statusbox: call update_all whenever lap = None is set
      self.statusbox.update_all(self.bar_mode)


deltabar_app = Delta()
