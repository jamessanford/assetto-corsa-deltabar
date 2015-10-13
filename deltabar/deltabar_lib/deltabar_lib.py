import ac
import acsys
import sys
import time

from deltabar_lib import sim_info

from deltabar_lib import config
from deltabar_lib import deltabar_ui
from deltabar_lib import lap
from deltabar_lib import lap_serialize
from deltabar_lib import statusbox


__author__ = 'James Sanford (jsanfordgit@froop.com)'


class Track:
  """
  Track info.
  """

  def __init__(self):
    self.name = self._get_track_name()
    self.sector_count = self._get_sector_count()

  @staticmethod
  def _get_track_name():
    track = ac.getTrackName(0)
    track_config = ac.getTrackConfiguration(0)
    if track_config:
      track = '{}-{}'.format(track, track_config)
    return track

  @staticmethod
  def _get_sector_count():
    return max(1, sim_info.info.static.sectorCount)


class LabelTracker:
  """Simple 'smoothing' for delta text changes.

  Avoid switching rapidly between two values like '-0.01' and '-0.02',
  just pick one and stick to it.
  """

  def __init__(self):
    self.bar_smooth = True
    self.old = ""
    self.last = ""

  def should_update(self, text):
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
    self.track = None
    self.lap = None
    self.last_sector = -1
    self.last_session = -1
    self.lap_wait = None  # Delay when bailing out of invalid laps.
    self.sector_wait = None
    self.sector_lookup = None
    self.bar_mode = config.FASTEST_LAP
    self.bar_moves = True
    self.banner_time = 0
    self.first_update = True
    self.label_tracker = LabelTracker()
    self.statusbox = None
    self.ui = deltabar_ui.DeltaBarUI(self.data, self.label_tracker)

  def acMain(self, version):
    return 'deltabar'

  def acShutdown(self):
    self.data.config['bar_mode'] = self.bar_mode
    self.data.config['bar_moves'] = self.bar_moves
    self.data.config['bar_smooth'] = self.label_tracker.bar_smooth
    if self.sector_lookup is not None:
      lookup = self.data.config.setdefault('sectors', {})
      lookup[self.track.name] = self.sector_lookup
    config.save(self.data.config)

    if hasattr(self.data, 'fastest_lap') and not self.data.fastest_lap.fromfile:
      lap_serialize.save(self.data.fastest_lap, 'best')

    for sector_number, lap in enumerate(self.data.fastest_splits):
      if lap is not None and not lap.fromfile:
        lap_serialize.save(lap, 'q{}'.format(sector_number + 1))

  def reinitialize_app(self):
    self.track = Track()

    # Avoid a "sector change" until it actually changes.
    self.last_sector = sim_info.info.graphics.currentSectorIndex

    # Note AC_PRACTICE/AC_QUALIFY/AC_RACE transitions.
    self.last_session = sim_info.info.graphics.session

    if not hasattr(self.data, 'sectors_available'):
      # Yes, keep this in self.data, so we can hot reload and still know it.
      self.data.sectors_available = False  # auto-set to True when available

    # Only one sector? We know what sector you are in.
    if self.track.sector_count == 1:
      self.data.sectors_available = True

    track = self.track.name

    if not hasattr(self.data, 'config'):
      self.data.config = config.load()
      if 'bar_mode' in self.data.config:
        self.bar_mode = self.data.config['bar_mode']
      if 'bar_moves' in self.data.config:
        self.bar_moves = self.data.config['bar_moves']
      if 'bar_smooth' in self.data.config:
        self.label_tracker.bar_smooth = self.data.config['bar_smooth']
      if ('sectors' in self.data.config and
              track in self.data.config['sectors']):
        self.sector_lookup = self.data.config['sectors'][track]

    if not hasattr(self.data, 'fastest_lap'):
      rlap = lap_serialize.load(track, ac.getCarName(0), 'best',
                                sector_count=self.track.sector_count)
      if rlap is not None:
        self.data.fastest_lap = rlap

    if not hasattr(self.data, 'fastest_splits'):
      self.data.fastest_splits = []
      for sector_number in range(self.track.sector_count):
        rlap = lap_serialize.load(track,
                                  ac.getCarName(0),
                                  'q{}'.format(sector_number + 1),
                                  sector_count=self.track.sector_count)
        self.data.fastest_splits.append(rlap)  # May be None

    if not hasattr(self.data, 'session_splits'):
      self.data.session_splits = [None] * self.track.sector_count

  def reinitialize_statusbox(self):
    field = 'enable_timing_window'
    if field not in self.data.config:
      self.data.config[field] = False

    if not self.data.config[field]:
      # Window is explicitly disabled, bail out.
      return

    if not hasattr(self.data, 'app_id2'):
      app_id2 = ac.newApp('deltabar timer')
      if app_id2 < 0:
        return  # bail out, new window did not work
      else:
        self.data.app_id2 = app_id2

    ac.setTitle(self.data.app_id2, "")
    ac.setBackgroundOpacity(self.data.app_id2, 0.5)
    ac.drawBorder(self.data.app_id2, 0)
    ac.setIconPosition(self.data.app_id2, 0, -10000)
    ac.setSize(self.data.app_id2, 300, 200)

    self.statusbox = statusbox.StatusBox(self.data, self.track.sector_count,
                                         bar_mode=self.bar_mode)
    self.statusbox.update_all(self.bar_mode)

  def init_lap(self):
    self.lap.track = self.track.name
    self.lap.car = ac.getCarName(0)
    self.lap.lap_number = ac.getCarState(0, acsys.CS.LapCount)
    self.lap.splits = [0] * self.track.sector_count
    self.lap.invalid_sectors = [False] * self.track.sector_count

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
      self.ui.reinitialize()
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
    if (current_lap < self.lap.lap_number or
            sim_info.info.graphics.session != self.last_session):
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
      if self.sector_lookup is None:
        # sectors not available
        return -1
      elif pos >= self.sector_lookup[self.last_sector]:
        if self.last_sector < self.track.sector_count - 1:
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

      if self.sector_lookup is None:
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
      sector_number = self.track.sector_count - 1

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
    self.ui.hide_delta_label()
    self.ui.reset_delta_label_text()
    if hasattr(self.data, 't'):
      del self.data.t
    if hasattr(self.data, 's'):
      del self.data.s

  def show_banner(self, duration, text):
    self.banner_time = time.time() + duration
    self.ui.set_banner_label_text(text)

  def check_banner(self):
    if self.banner_time != 0 and time.time() >= self.banner_time:
      self.banner_time = 0
      self.ui.reset_banner_label_text()

  def onRender(self, delta_t):
    if self.first_update:
      return  # bail out, nothing is ready

    if (sim_info.info.graphics.status not in (sim_info.AC_LIVE,
                                              sim_info.AC_PAUSE)):
      self.ui.hide_bar_area()
      self.ui.hide_delta_label()
      self.clear_screen_data()
    elif hasattr(self.data, 't') and hasattr(self.data, 's'):
      self.ui.show_bar_area()
      self.ui.draw_bar_area_caps()
      self.ui.show_delta_label()
      self.ui.draw_delta_bar(self.data.t, self.data.s, self.bar_moves)
    else:
      self.ui.show_bar_area()
      self.ui.draw_bar_area_caps()
      self.clear_screen_data()

    if self.banner_time == 0:
      self.ui.hide_app_background()

    self.check_banner()

  def onClick(self):
    if self.first_update:
      return  # bail out, nothing is ready

    if self.banner_time == 0:
      current_mode = config.MODES[self.bar_mode][1]
      self.show_banner(2.2, '{} (click to toggle)'.format(current_mode))
      return

    self.bar_mode += 1
    if self.bar_mode >= len(config.MODES):
      self.bar_mode = 0
    self.show_banner(2.2, config.MODES[self.bar_mode][1])

    if self.statusbox is not None:
      # TODO FIXME NOTE statusbox: call update_all whenever lap = None is set
      self.statusbox.update_all(self.bar_mode)


deltabar_app = Delta()
