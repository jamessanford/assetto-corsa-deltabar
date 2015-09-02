[python] collection of AC development tools


When I made the DeltaBar plugin, I wanted to be able to iterate fast.

Having to relaunch an AC session to reload the plugin
after each development cycle is excruciatingly slow.

Also, I am not a Windows developer, and am more comfortable with a Linux CLI.

So, I made a "hot reload" system.

I can develop on my Linux box, hit "send", and suddenly the new plugin
version is running within an AC session.  An error or a slight change?
Just "send" again and now it's updated.  I can read any exceptions
on the linux side, and also pop open an interactive console to test
the AC API with a REPL, while AC is running.

See README_DEBUG_TUTORIAL.txt for details.




I noticed that some other developers have made their own set of tools,
and I thought it would be worth collecting them in one place.

Here is what I know of:

View all AC API values inside the sim:
  http://www.assettocorsa.net/forum/index.php?threads/monitor-app-for-complete-ac-api.22249/

A stubbed out version of ac/acsys so you can smoke test your code:
  https://github.com/Turnermator13/AssettoCorsaDevLibs

An offline mode for ac/acsys that appears to record the calls in online mode
and replay valid return values when offline:
  ptracker ACSIM 'acsim.py' 'app_skeleton'

