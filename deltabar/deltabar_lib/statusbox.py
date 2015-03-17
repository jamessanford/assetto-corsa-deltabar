
import ac
import acsys

from deltabar_lib import config


# WARNING: This code is a giant mess at the moment!  Beware!
#
# Full of bugs!  BETA!


class TextBox:
  """
MODE
   1:    -.---   -.---    <- each frame
   2:   17.294   -1.17    <- on sector changes
   3:  *18.995   -0.32
Last:    -.---            <- on lap changes
Best: 1:37.832   +1.43    <- on lap changes
 Opt: 1:34.598    -.--    <- on sector changes
  """

  def __init__(self, window_id, data):
    self.window_id = window_id
    self.data = data
    self._next_line = 0
    self._font_size = 22
    self._line_size = self._font_size + 4

  def set(self, col, text):
    ac.setText(getattr(self.data, col), text)

  def add(self, text, x1, x2, x3):
    single_column = not any((x2, x3))

    for column_number, col in enumerate((x1, x2, x3)):
      if col is None:
        continue
      if not hasattr(self.data, col):
        setattr(self.data, col, ac.addLabel(self.window_id, ""))
      ident = getattr(self.data, col)
      ac.setPosition(ident, column_number * 100, self._next_line)
      width = 300 if single_column else 100
      ac.setSize(ident, width, self._line_size)
      ac.setFontSize(ident, self._font_size)
      if not single_column:
        ac.setFontAlignment(ident, 'right')
      ac.setFontColor(ident, 1.0, 1.0, 1.0, 1.0)

    self._next_line += self._line_size
    self.set(x1, text)


def format_time(ms, invalid=False, delta=False):
  """change milliseconds into minutes:seconds.thousandths"""
  star = '*' if invalid else ''
  if ms < 0:
    sign = '-'
  elif delta:
    sign = '+'
  elif ms == 0:
    return "-.---"  # no absolute times should be zero
  else:
    sign = ''
  (minsec, thou) = divmod(abs(ms), 1000)
  (min, sec) = divmod(minsec, 60)
  if min != 0:
    return "{}{}{}:{:02d}.{:03d}".format(star, sign, min, sec, thou)
  else:
    return "{}{}{}.{:03d}".format(star, sign, sec, thou)


class StatusBox:
  def __init__(self, data, sector_count, bar_mode=None):
    self.data = data  # we add 'raw_optimal', 'raw_lap_time', 'last_lap_invalid'
    self.sector_count = sector_count
    self.bar_mode = bar_mode
    self.reinitialize()

  def reinitialize(self):
    self.data.textbox = TextBox(self.data.app_id2, self.data)
    textbox = self.data.textbox
    textbox.add('Title Heading', 'mode', None, None)
    for sector_number in range(self.sector_count):
      text = '{}:'.format(sector_number + 1)
      ident = 'i{}'.format(sector_number)
      textbox.add(text, ident, ident + '_1', ident + '_2')

    textbox.add('Last:', 'last', 'last_1', 'last_2')
    textbox.add('Best:', 'best', 'best_1', 'best_2')
    textbox.add('Opt:', 'opt', 'opt_1', 'opt_2')

  def update_optimal(self):
    # Update optimal display.
    if self.bar_mode in (config.FASTEST_LAP, config.FASTEST_SECTOR, config.FASTEST_OPTIMAL):
      fastest = self.data.fastest_splits
    else:
      fastest = self.data.session_splits
    opt = 0
    for _sector, _lap in enumerate(fastest):
      if _lap is None:
        opt = 0
        break
      value = _lap.splits[_sector]
      if value == 0:
        opt = 0
        break
      opt += value
    self.data.raw_optimal = opt
    self.data.textbox.set('opt_1', format_time(opt))

  def update_last(self, lap):
    self.update_best()

    if lap is None:
      if (not hasattr(self.data, 'raw_last_lap_time') or
          not hasattr(self.data, 'last_lap_invalid')):
        return
      lap_time = self.data.raw_last_lap_time
      invalid = self.data.last_lap_invalid
    else:
      lap_time = self.data.raw_last_lap_time = lap.lap_time
      invalid = self.data.last_lap_invalid = lap.invalid or not lap.complete

    if lap_time <= 0:
      # Well that is not right.
      self.data.textbox.set('last_1', format_time(0))
      self.data.textbox.set('best_2', "")
      self.data.textbox.set('opt_2', "")
      return

    self.data.textbox.set('last_1', format_time(lap_time, invalid=invalid))

  def update_best(self):
    if (hasattr(self.data, 'fastest_lap') and
        self.bar_mode in (config.FASTEST_LAP,
                          config.FASTEST_OPTIMAL,
                          config.FASTEST_SECTOR)):
      value = format_time(self.data.fastest_lap.lap_time)
    elif (hasattr(self.data, 'session_lap') and
          self.bar_mode in (config.SESSION_LAP,
                            config.SESSION_OPTIMAL,
                            config.SESSION_SECTOR)):
      value = format_time(self.data.session_lap.lap_time)
    else:
      value = ""
    self.data.textbox.set('best_1', value)

  def update_diff(self, lap):
    # just update the _2 items

    # TODO FIXME: 'best_2' should probably be 'last_2' everywhere,
    # especially because now last/best can be a new low, but best diff will show an offset

    # TODO FIXME code duplication with update_last
    if lap is None:
      if not hasattr(self.data, 'raw_last_lap_time') or not hasattr(self.data, 'last_lap_invalid'):
        self.data.textbox.set('best_2', "")
        self.data.textbox.set('opt_2', "")
        return
      lap_time = self.data.raw_last_lap_time
      invalid = self.data.last_lap_invalid
    else:
      lap_time = lap.lap_time
      invalid = lap.invalid

    if lap_time <= 0:
      # sigh?
      self.data.textbox.set('best_2', "")
      self.data.textbox.set('opt_2', "")
      return

    # The diff is either to 'best' or 'optimal'

    if self.bar_mode in (config.FASTEST_LAP, config.FASTEST_SECTOR, config.FASTEST_OPTIMAL):
      if hasattr(self.data, 'fastest_lap'):
        self.data.textbox.set('best_2', format_time(lap_time - self.data.fastest_lap.lap_time, invalid=invalid, delta=True))
    elif self.bar_mode in (config.SESSION_LAP, config.SESSION_SECTOR, config.SESSION_OPTIMAL):
      if hasattr(self.data, 'session_lap'):
        self.data.textbox.set('best_2', format_time(lap_time - self.data.session_lap.lap_time, invalid=invalid, delta=True))

    if hasattr(self.data, 'raw_optimal') and self.data.raw_optimal > 0:
      self.data.textbox.set('opt_2', format_time(lap_time - self.data.raw_optimal, invalid=invalid, delta=True))

  def update_frame(self, lap, elapsed_seconds, current_sector, pos, invalid):
    # TODO Should I generate all the numbers and then pick which one to show?

    if 0 in lap.splits[0:current_sector]:
      # our lap is missing times for the previous sectors!
      self.data.textbox.set('i{}_1'.format(current_sector),
                            format_time(0, invalid=invalid))
      self.data.textbox.set('i{}_2'.format(current_sector), "")
      return

    current_sector_time = elapsed_seconds - sum(lap.splits[0:current_sector])
    self.data.textbox.set('i{}_1'.format(current_sector),
                          format_time(current_sector_time, invalid=invalid))

    # TODO: Save EVERY KIND of benchmark calculation in raw_sector{}_XXX
    benchmark_sector_time = 0
    if self.bar_mode == config.FASTEST_LAP:
      if hasattr(self.data, 'fastest_lap'):
        idx = self.data.fastest_lap.index_for_offset(pos)
        benchmark_sector_time = self.data.fastest_lap.elapsed_seconds[idx] - sum(self.data.fastest_lap.splits[0:current_sector])
    elif self.bar_mode == config.SESSION_LAP:
      if hasattr(self.data, 'session_lap'):
        idx = self.data.session_lap.index_for_offset(pos)
        benchmark_sector_time = self.data.session_lap.elapsed_seconds[idx] - sum(self.data.session_lap.splits[0:current_sector])
    else:
      fastest = None
      if self.bar_mode in (config.FASTEST_SECTOR, config.FASTEST_OPTIMAL):
        fastest = self.data.fastest_splits[current_sector]
      elif self.bar_mode in (config.SESSION_SECTOR, config.SESSION_OPTIMAL):
        fastest = self.data.session_splits[current_sector]
      if fastest is not None:
        idx = fastest.index_for_offset(pos)
        benchmark_sector_time = fastest.elapsed_seconds[idx] - sum(fastest.splits[0:current_sector])

    if benchmark_sector_time > 0:
      self.data.textbox.set('i{}_2'.format(current_sector), format_time(current_sector_time - benchmark_sector_time, invalid=invalid, delta=True))
    else:
      self.data.textbox.set('i{}_2'.format(current_sector), "")

  def update_all(self, bar_mode):
    self.bar_mode = bar_mode

    self.data.textbox.set(
      'mode', '{}: {} (BETA)'.format(bar_mode, config.MODES[bar_mode][1]))

    # update_frame...or...just zero.  the diff times are wrong.
    for _sector in range(self.sector_count):
      # TODO: FIXME
      self.data.textbox.set('i{}_2'.format(_sector), "")  # sector diff times
    self.data.textbox.set('best_2', "")  # diff time
    self.data.textbox.set('opt_2', "")   # diff time
    self.data.textbox.set('best_1', format_time(0))  # clear session vs all-time best

    self.update_optimal()
    self.update_diff(None)
    self.update_last(None)  # update_best implied


# BUG: when we set a New Best lap, the delta should be the delta to the OLD best lap.  right now we show +0.000
# BUG: same thing with optimal, diff should be to "last optimal"

# BUG: when we update optimal in the middle of a lap, the diff becomes wrong
#      should we update the diff too?  we do have the "last" time.

# also, the optimal lap display diff, should we really reset it?
#  or should it just keep going "more optimal"?
#  ...probably should "set the optimal lap at the beginning of each lap",
#  then drive against it, then reset the optimal lap at the end?

# BUG: back to pits -> drive, thiks I am in sector 3.
#  reset last_sector??

# BUG: 'session' is really 'in this instance of the game',
#  should we reset the session on 'reset session' and for 'practice/quali/race'

# BUG: still some bug where, in sector 3, it thinks my 'sector time'
#      is my lap time, ie instead of 30 seconds, it's 2 minutes 10 seconds.
#    the diffs are based off of that too.
#    maybe has something to do with off track early sectors,
#    so that the sector time is not recorded properly in the lap.
#      ie, sum (splits) is wrong.
# if any of the splits are wrong, it should abandon the calculation really...


# I think the current status is:
#   works, but changing modes zeroes all the delta times.
#   (and best/opt deltas get reset to "against current best/opt") (instead of "delta against what it was when the lap was being driven)
#
#  can fix changing modes by...using the old "lap" + current lap
#  to regenerate...  times will still be "against currently best", but OK.
#
#  needs old lap for sectors not driven yet, and current lap for
#  sectors driven up to current sector.

# TODO: colors of 'old driven sectors' should be gray
#   current sector should be 'yellow'/gold
#
#
