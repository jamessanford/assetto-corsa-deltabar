DeltaBar v1.30 - iRacing-style delta bar with variable color

  Plugin for Assetto Corsa racing simulator.
  Released at http://www.racedepartment.com/downloads/deltabar.4842/
  Uses the sim_info.py module from Rombik.

DeltaBar shows time and speed difference compared to your best lap (or sector).

The color of the bar shows if you are currently gaining or losing time.
Exit a corner slightly better and it will glow green.
Exit a corner *significantly* faster and the bar will be bright green.

The number displayed is the time overall loss/improvement for the
current lap (or sector).  The length of the color bar is a visual
representation of this time loss/improvement.

!! Drive a complete lap before the bar will display data.

!! For sectors to work in multiplayer, drive the track in single player first.

Click on the bar repeatedly to toggle display mode.
(vs best lap, vs best sectors, vs overall optimal lap; all-time or this-session)

INSTALLATION

1. Move the entire deltabar folder into:

   C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python


2. Run Assetto Corsa, enable the deltabar plugin:

   Options -> General -> UI Modules -> deltabar <ENABLED>


3.  When in the car cockpit,
    activate the menus on the right side,
    scroll all the way near the bottom,
    <CLICK> on the icon with the 'deltabar' tooltip.

Usage:
   You should see a large rectangle appear.

   Drive a lap and then it will show data.

   Click on the rectangle to toggle between display modes.


CHANGELOG:
    v1.30: October 12 2015
           Support for AC 1.3
           Improved bar look and rounded corners thanks to Alexander
           Improved readability for delta value thanks to Alexander
           Internal refactoring thanks to Alexander

    v1.27: March 17 2015
           Support for AC 1.1.2.
           Support single sector tracks.
           BETA version of timing window: 'deltabar timing' app if you set:
             "enable_timing_window": true
             Documents/Assetto Corsa/plugins/deltabar/config.txt

    v1.20: January 7 2015
           Fix for many addon tracks, end-of-lap detection was not working.
           Fix for session resets and transitions between practice/quali/race.
           Fix for optimal lap mode when your early sectors were off track.
           Click to change modes uses more visible yellow color.
           Lightly smooth reported delta so it doesn't constantly flip
           between two values.
             You can disable this with "bar_smooth": false in
             Documents/Assetto Corsa/plugins/deltabar/config.txt
           Option to keep delta text in the center of the bar.
             You can set "bar_moves": false in
             Documents/Assetto Corsa/plugins/deltabar/config.txt

   v1.10: January 3 2015
          Improved visuals
          Optimal lap support
          Fixed left/right sides of bar to match plus/minus of iRacing.

   v1.01: December 31 2014
          Initial release


Download:
https://github.com/jamessanford/assetto-corsa-deltabar/archive/deltabar_v130.zip

Source browser:
https://github.com/jamessanford/assetto-corsa-deltabar/
