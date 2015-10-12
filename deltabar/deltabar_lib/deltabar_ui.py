import ac
import math
import sys

from deltabar_lib import config


class DeltaBarUI:
  """
  User Interface of Delta Bar application.
  """

  def __init__(self, deltabar_data, label_tracker):
    self.data = deltabar_data
    self.label_tracker = label_tracker

  def reinitialize(self):
    ac.setTitle(self.data.app_id, "")
    self.hide_app_background()
    ac.drawBorder(self.data.app_id, 0)
    ac.setIconPosition(self.data.app_id, 0, -10000)
    ac.setSize(self.data.app_id, config.APP_WIDTH, config.APP_HEIGHT)

    # Click on app area handling - used for toggling modes
    if not hasattr(self.data, 'click_label'):
      self.data.click_label = ac.addLabel(self.data.app_id, '')
      ac.addOnClickedListener(self.data.click_label, sys.modules['deltabar'].onClick)
    ac.setPosition(self.data.click_label, 0, 0)
    ac.setSize(self.data.click_label, config.APP_WIDTH, config.APP_HEIGHT)

    # Delta bar main area
    if not hasattr(self.data, 'bar_area'):
      self.data.bar_area = ac.addLabel(self.data.app_id, '')
    ac.setPosition(self.data.bar_area, config.BAR_CORNER_RADIUS, 0)
    ac.setSize(self.data.bar_area,
               config.BAR_WIDTH - 2 * config.BAR_CORNER_RADIUS,
               config.BAR_HEIGHT)
    ac.setBackgroundColor(self.data.bar_area, *config.BACKGROUND_COLOR.rgb)
    ac.setBackgroundOpacity(self.data.bar_area, config.BACKGROUND_COLOR.alpha)

    # Delta label background area
    if not hasattr(self.data, 'delta_label_area'):
      self.data.delta_label_area = ac.addLabel(self.data.app_id, '')
    ac.setPosition(self.data.delta_label_area,
                   config.BAR_WIDTH_HALF - config.DELTA_LABEL_WIDTH_HALF,
                   config.DELTA_LABEL_Y)
    ac.setSize(self.data.delta_label_area, config.DELTA_LABEL_WIDTH, config.DELTA_LABEL_HEIGHT)
    ac.setBackgroundTexture(self.data.delta_label_area,
                            'apps/python/deltabar/background_delta.png')

    # Delta label text
    if not hasattr(self.data, 'delta_label'):
      self.data.delta_label = ac.addLabel(self.data.app_id, '')
    ac.setPosition(self.data.delta_label,
                   config.BAR_WIDTH_HALF - config.DELTA_LABEL_WIDTH_HALF,
                   config.DELTA_LABEL_TEXT_Y)
    ac.setSize(self.data.delta_label,
               config.DELTA_LABEL_WIDTH, config.DELTA_LABEL_FONT_SIZE)
    ac.setFontAlignment(self.data.delta_label, 'center')
    ac.setFontSize(self.data.delta_label, config.DELTA_LABEL_FONT_SIZE)

    # Banner label (displays current selected mode)
    if not hasattr(self.data, 'banner_label'):
      self.data.banner_label = ac.addLabel(self.data.app_id, '')
    ac.setPosition(self.data.banner_label,
                   config.BAR_WIDTH_HALF - config.BANNER_TEXT_WIDTH / 2,
                   config.BANNER_Y)
    ac.setSize(self.data.banner_label,
               config.BANNER_TEXT_WIDTH, config.BANNER_FONT_SIZE)
    ac.setFontAlignment(self.data.banner_label, 'center')
    ac.setFontSize(self.data.banner_label, config.BANNER_FONT_SIZE)
    ac.setFontColor(self.data.banner_label, *config.SLOW_COLOR.rgba)

  def hide_app_background(self):
    ac.setBackgroundOpacity(self.data.app_id, 0.0)

  # Delta label

  def show_delta_label(self):
    self._set_delta_label_visible(1)

  def hide_delta_label(self):
    self._set_delta_label_visible(0)

  def set_delta_label_text(self, text):
    ac.setText(self.data.delta_label, text)

  def reset_delta_label_text(self):
    self.set_delta_label_text('')

  def _set_delta_label_visible(self, visible):
    ac.setVisible(self.data.delta_label_area, visible)
    ac.setVisible(self.data.delta_label, visible)

  def _update_delta_label(self, time_delta, position, bar_moves):
    """
    Updates delta label with new value if needed.
    :param time_delta: time delta value
    :param position: x coordinate of label center
    """
    plus = '-' if time_delta < 0 else '+'
    # NOTE: The below .format()s are too much magic.
    #       We want 234 to be '0.23' and 12345 to be '12.34'
    ms = '{:04d}'.format(abs(int(time_delta)))
    label_text = '{}{}{}.{}'.format(plus, self.data.star, ms[0:-3], ms[-3:-1])
    label_changed = self.label_tracker.should_update(label_text)

    if not label_changed:
      # bail out, do not change the actual label (and do not move it)
      return

    font_color = self._delta_label_color(time_delta)
    ac.setFontColor(self.data.delta_label, *font_color)

    if bar_moves:
      if time_delta < 0:
        position = min(position - config.DELTA_LABEL_WIDTH_HALF,
                       config.BAR_WIDTH - config.DELTA_LABEL_WIDTH)
      else:
        position = max(0, position - config.DELTA_LABEL_WIDTH_HALF)
      self._set_delta_label_position(position)

    self.set_delta_label_text(label_text)

  @staticmethod
  def _delta_label_color(time_delta):
    """
    Calculates delta label color according to time delta value.
    :param time_delta: time delta value
    :return: calculated color
    """
    if time_delta < 0:
      return config.FAST_COLOR.rgba
    else:
      return config.SLOW_COLOR.rgba

  def _set_delta_label_position(self, x):
    ac.setPosition(self.data.delta_label_area, x, config.DELTA_LABEL_Y)
    ac.setPosition(self.data.delta_label, x, config.DELTA_LABEL_TEXT_Y)

  # Banner label

  def set_banner_label_text(self, text):
    ac.setText(self.data.banner_label, text)

  def reset_banner_label_text(self):
    self.set_banner_label_text('')

  # Delta bar

  def show_bar_area(self):
    self._set_bar_area_visible(1)

  def hide_bar_area(self):
    self._set_bar_area_visible(0)

  def _set_bar_area_visible(self, visible):
    ac.setVisible(self.data.bar_area, visible)

  def draw_bar_area_caps(self):
    ac.glColor4f(*config.BACKGROUND_COLOR.rgba)
    radius = config.BAR_CORNER_RADIUS
    segments = config.BAR_CORNER_SEGMENTS
    height = config.BAR_HEIGHT
    self._draw_horizontal_cap(radius, 0, -radius, height, radius, segments)
    self._draw_horizontal_cap(config.BAR_WIDTH - radius, 0, radius, height, radius, segments)

  def draw_delta_bar(self, time_delta, speed_delta, bar_moves):
    # Color
    if config.BAR_COLORS_OLD:
      bar_color = self._delta_stripe_color_old(speed_delta)
    else:
      bar_color = self._delta_stripe_color(speed_delta)
    ac.glColor4f(*bar_color)

    # Calculations
    clamped_time_delta = self._clamp_time_delta(time_delta)
    delta_stripe_width = int((abs(clamped_time_delta) * config.BAR_SCALE))
    delta_stripe_rect_width = delta_stripe_width
    should_draw_cap = delta_stripe_width > config.BAR_INNER_RECT_MAX_WIDTH

    if time_delta < 0:
      delta_rect_origin_x = config.BAR_WIDTH_HALF
      delta_label_position = delta_rect_origin_x + delta_stripe_width
    else:
      delta_rect_origin_x = config.BAR_WIDTH_HALF - delta_stripe_width
      delta_label_position = delta_rect_origin_x

    # Draw rounded cap and modify width and origin
    if should_draw_cap:
      delta_stripe_rect_width = config.BAR_INNER_RECT_MAX_WIDTH
      if time_delta > 0:
        delta_rect_origin_x = config.BAR_WIDTH_HALF - delta_stripe_rect_width

      self._draw_delta_stripe_cap(time_delta, delta_rect_origin_x, delta_stripe_width)

    # Draw stripe rect
    if delta_stripe_width > 0:
      ac.glQuad(delta_rect_origin_x, config.BAR_INNER_Y, delta_stripe_rect_width, config.BAR_INNER_HEIGHT)

    # Delta label
    self._update_delta_label(time_delta, delta_label_position, bar_moves)

  @staticmethod
  def _delta_stripe_color_old(speed_delta):
    """
    Calculates delta stripe color according to speed delta value.
    :param speed_delta: speed delta value
    :return: calculated color
    """
    # NOTE: Scale from 0.0 meters/sec = 1.0  to  5.0 meters/sec = 0.0
    #       If you change 5.0, change 0.2 to 1/new_value
    if not self.bar_new_colors:
      x = 1.0 - (min(abs(speed_delta), 5.0) * 0.2)
      if speed_delta >= 0.0:
        colors = (x, 1.0, x, 1.0)
      else:
        colors = (1.0, x, x, 1.0)
      return colors

  @staticmethod
  def _delta_stripe_color(speed_delta):
    """
    Calculates delta stripe color according to speed delta value.
    :param speed_delta: speed delta value
    :return: calculated color
    """
    # NOTE: Scale from 0.0 meters/sec = 1.0  to  5.0 meters/sec = 0.0
    #       If you change 5.0, change 0.2 to 1/new_value
    x = 1.0 - min(abs(speed_delta), 5.0) * 0.2
    if speed_delta >= 0.0:
      red = 0.1 + 0.9 * x
      blue = 0.1 + 0.9 * math.pow(x, 1.25)
      return red, 1.0, blue, 1.0  # From green to white
    else:
      green = x
      blue = math.pow(x, 2.0)
      return 1.0, green, blue, 1.0  # From red to white

  @staticmethod
  def _clamp_time_delta(time_delta):
    """
    Clamps time delta absolute value to 2 seconds.
    :param time_delta: time delta value
    :return: clamped value
    """
    if time_delta > 2000:
      return 2000
    elif time_delta < -2000:
      return -2000
    return time_delta

  @staticmethod
  def _draw_delta_stripe_cap(time_delta, delta_rect_origin_x, delta_stripe_width):
    """
    Draws left or right cap for delta bar stripe
    :param time_delta: time delta value
    :param delta_rect_origin_x: x coordinate of delta stripe's rectangular part
    :param delta_stripe_width: full delta stripe width
    """
    cap_origin_x = delta_rect_origin_x
    if time_delta < 0:
      cap_origin_x += config.BAR_INNER_RECT_MAX_WIDTH
    cap_width = - sign(time_delta) * (delta_stripe_width - config.BAR_INNER_RECT_MAX_WIDTH)

    DeltaBarUI._draw_horizontal_cap(cap_origin_x,
                                    config.BAR_INNER_Y,
                                    cap_width,
                                    config.BAR_INNER_HEIGHT,
                                    config.BAR_INNER_CORNER_RADIUS,
                                    config.BAR_INNER_CORNER_SEGMENTS)

  # Helpers

  @staticmethod
  def _draw_horizontal_cap(origin_x, origin_y, width, height, corner_radius, corner_segments):
    """
    Draws left or right cap for rectangle with rounded corners starting from straight border.
    :param origin_x: x coordinate of straight border
    :param origin_y: y coordinate of figure
    :param width: width of figure. The value < 0 means that cap is oriented leftwards.
      If width is less than corner radius - the cap is truncated
    :param height: height of the figure
    :param corner_radius: radius of cap corner
    :param corner_segments: number of segments in cap corner
    """
    reversed_normal_of_poly = width < 0  # Don't reorder points - just mark as reversed polygon's normal

    bottom_y = origin_y + height
    segment_angle = math.pi / (2 * corner_segments)
    last_segment_x = 0
    last_segment_y = 0
    completed = False

    for i in range(1, corner_segments + 1):
      if completed:
        break

      angle = math.pi / 2 - i * segment_angle
      segment_x = sign(width) * math.cos(angle) * corner_radius
      if abs(width) <= abs(segment_x):
        completed = True
        segment_x = width
        angle = math.acos(segment_x / corner_radius)

      segment_y = corner_radius * (1 - math.sin(angle))

      DeltaBarUI._draw_polygon((origin_x + last_segment_x, origin_y + last_segment_y),
                               (origin_x + last_segment_x, bottom_y - last_segment_y),
                               (origin_x + segment_x, bottom_y - segment_y),
                               (origin_x + segment_x, origin_y + segment_y),
                               reversed_normal_of_poly)

      last_segment_x = segment_x
      last_segment_y = segment_y

  @staticmethod
  def _draw_polygon(p1, p2, p3, p4, reversed_normal):
    ac.glBegin(3)
    if not reversed_normal:
      ac.glVertex2f(*p1)
      ac.glVertex2f(*p2)
      ac.glVertex2f(*p3)
      ac.glVertex2f(*p4)
    else:
      ac.glVertex2f(*p1)
      ac.glVertex2f(*p4)
      ac.glVertex2f(*p3)
      ac.glVertex2f(*p2)
    ac.glEnd()


def sign(x):
  return math.copysign(1, x)
