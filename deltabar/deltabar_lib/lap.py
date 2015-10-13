
import array
import bisect


class Lap:

  def __init__(self):
    self.car = ""
    self.track = ""
    self.tires = ""
    self.timestamp = 0
    self.lap_number = 0

    # may not need these...
    self.complete = False  # true when entire lap has been recorded
    self.invalid = False   # true if lap is invalidated by going off
    self.invalid_sectors = []  # should be False * sectorCount
    self.lap_time = 0      # added when complete
    self.splits = []       # added when available
    self.wrapped = False   # normalizedSplinePosition has wrapped during lap
    self.fromfile = False  # true when loaded from lap serializer

    # internal state for reusing the objects during add()
    self._next_index = 0   # where in the array()s we currently are

    # Part of me makes me want to make it even more optimal with
    # an anonymous mmap area and ctypes structure, so only one thing grows,
    # but growing the array.array works fine.

    # offset=0.0134, item=0: all item 0 entries will be for "offset 0.0134"
    self.offset = array.array('d')  # normalized spline point
    self.elapsed_seconds = array.array('L')
    self.speed_ms = array.array('d')  # meters/second
    self.throttle = array.array('d')
    self.brake = array.array('d')
    self.steering = array.array('d')
    self.gear = array.array('b')
    self.distance_traveled = array.array('d')  # for this lap only.

  def position_wrapped(self, offset):
    if self.wrapped:
      return True

    if self._next_index > 1:
      first = self.offset[0]
      last = self.offset[self._next_index - 1]

      if offset < first and (offset - 0.05) < 0.0 and (last + 0.05) > 1.0:
        self.wrapped = True
        return True

    return False

  def next_offset_ok(self, offset):
    if self._next_index > 0:
      last = self.offset[self._next_index - 1]
      if offset <= last:
        return False
      if offset >= last + 0.10:
        return False
    return True

  def add(self, offset, elapsed_seconds, speed_ms,
          throttle, brake, steering, gear, distance_traveled):
    if not self.next_offset_ok(offset):
      # We jumped.  Do not record it.  See: Vallelunga pit exit.
      # TODO: Mark lap as invalid when this continues?
      return

    # NOTE: Maybe too fancy here...
    for item in ('offset', 'elapsed_seconds', 'speed_ms',
                 'throttle', 'brake', 'steering',
                 'gear', 'distance_traveled'):
      value = locals()[item]
      getattr(self, item).append(value)

    self._next_index += 1

  def get_index(self):
    return self._next_index

  def index_for_offset(self, offset):
    # might be -1
    # also might not be anywhere close...cause -1 error if not close.
    idx = bisect.bisect_right(self.offset, offset,
                              lo=0, hi=self._next_index) - 1
    return idx

  def offset_for_elapsed(self, elapsed_time):
    idx = bisect.bisect_right(self.elapsed_seconds, elapsed_time,
                              lo=0, hi=self._next_index) - 1
    if idx < 0:
      return 0.0
    return self.offset[idx]
