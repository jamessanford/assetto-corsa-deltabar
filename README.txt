
DeltaBar v1.20 - iRacing-style delta bar with variable color

Uses the sim_info.py module from Rombik


Supported modes, click on the plugin repeatedly to toggle:
- vs all-time best lap
- vs all-time best sectors
- vs all-time optimal lap
- vs session best lap
- vs session best sectors
- vs session optimal lap

Works in multiplayer and offline modes.

The number itself is the improvement/loss for the current lap(or sector),
the bar length is a visual representation of that number.

The color of the bar is the fun bit:It shows if you are gaining or losing time.
(exit a corner slightly better and it will glow green,
 even if the delta itself is still in the red; exit a corner
 significantly faster and it will be bright green)

Best lap telemetry is stored locally in a JSON format.

Does not connect to any remote services, it's entirely local.

It doesn't affect my frame rate on my relatively-low-end CPU,
but let me know if something is not working right or it is
causing slowdowns.



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
https://github.com/jamessanford/assetto-corsa-deltabar/archive/deltabar_v120.zip

Source browser:
https://github.com/jamessanford/assetto-corsa-deltabar/
