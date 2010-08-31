TCP/IP remote for TiVo Series 3+, v0.23
by William McBrine <wmcbrine@gmail.com>
August 31, 2010

An on-screen virtual remote control that can control your TiVo over the 
network. It works with the Series 3 or any later TiVo model.

Python 2.x is required (tested on 2.3 through 2.6), as well as Tkinter 
(normally part of Python's standard library) or PyGTK. Mac OS X and 
Linux users should have what they need already; Windows users should 
visit http://python.org/ . The remote has also been tested on Windows CE 
and other platforms.

This program uses the network remote control interface first made public 
by TCF user Omikron in this thread:

http://tivocommunity.com/tivo-vb/showthread.php?t=392385

which has doubled as the support thread for the app, and, previously, 
the only place where it was distributed.

Released under the GPL 2+.


Quick Start
-----------

By default, the TiVo's network remote service is disabled. To enable it, 
go into the "Messages and Settings" menu, then "Settings", "Remote, 
CableCARD, & Devices", and finally "Network Remote Control", and check 
"Enabled".

Once Python is installed on your system, you should be able to just 
extract the TiVo Remote archive anywhere, and click on "remote.pyw", or 
run it from the command line. (Mac users may have to use the context 
menu if starting it from the GUI. If you have Xcode, consider building 
an applet.) No installation is required. remote.pyw is the only required 
file, although Zeroconf.py is also needed if you want to use the 
"modern" style of TiVo autodetection, which I recommend.

If it's working properly, you should within a few seconds see a list of 
available TiVos from which to select, or be immediately connected to 
your TiVo if only one is found. If autodetection fails, you'll instead 
get a prompt for your TiVo's address. Alternatively, you can directly 
specify the TiVo's address on the command line (see below).

Zeroconf-based autodetection needs to send and recieve UDP on port 5353. 
Old-style autodetection sends and recieves TCP and UDP on port 2190, and 
recieves TCP on a randomly-chosen port. The core remote functionality 
will work as long as it can make outgoing TCP connections on port 31339.


Buttons
-------

The function of most buttons should be obvious, but a few may need 
explanation:

Zoom -- Also known as "Aspect" or "Window" on pre-Premiere remotes; they
        all use the same code.

SPS30 -- Sends the famous Select-Play-Select-3-0-Select sequence to
         toggle the behavior of the "Skip" button, so you don't have to 
         do it manually.

CC -- Closed-caption toggle; sends Clear-Info-Down-Down-Down-Down-
      Select-Clear, which works to toggle the closed captioning during
      either LiveTV or recordings (but will produce a couple of error
      bongs when applied during recordings).

Clock -- Sends Select-Play-Select-9-Select, to toggle the on-screen clock.

Skip -- Also known as "Advance" and "the button with an arrow pointing
        to a line". This is your 30-second skip/slip or catch-up button,
        also used to enter the dash for OTA channels.

A/B/C/D -- The multicolored buttons found on the latest TiVo remotes.

Kbd -- Sends the text in the "Text:" window (see below). Note that you
       can just hit "Enter" on your keyboard when the text field is in
       focus to accomplish the same thing (not to be confused with
       "Enter" on the remote).

Standby -- Puts the TiVo into standby mode, or pulls it out of it (into
           LiveTV) if it already was. This function is available as a
           discrete remote code for universal remotes, but isn't on the 
           standard peanuts.

Quit -- Exits the remote program; doesn't send anything to the TiVo.

SPS30, CC and Clock should be used only when playing back a recording or 
in LiveTV mode. Otherwise, the results are unpredictable.


Keyboard Shortcuts
------------------

Most buttons have keyboard shortcuts, which can be much more convenient 
to use than mousing around and clicking. Of course these don't work when 
the text input window has focus. Numbers, letters (A/B/C/D) and arrow 
keys are what you'd expect; other shortcuts are:

TiVo          T, F1, or F11
Zoom          Z or W
Info          I or F10
LiveTV        L or F2
Guide         G or F3
Select        Enter/Return
Thumbs Down   D or F6
Thumbs Up     U or F5
Channel Up    PgUp or F7
Channel Down  PgDn or F8
Record        R or F9
Play          P
Reverse       V or [
Pause         Spacebar
Forward       F or ]
Replay        X or -
Slow          O
Skip          S or =
Clear         Esc
Enter         E or .
Quit          Q

As a bonus, only available via keyboard shortcut:

Stop          `

Some of these are taken from the keys used with TiVo's HME simulator 
from the Java SDK. The function keys are what the TiVo recognizes from 
an attached USB keyboard.

Buttons with no corresponding keyboard shortcuts: SPS30, CC, Clock, and 
Standby.


Text entry
----------

For the TiVo's on-screen keyboards, instead of moving the cursor around 
manually to select each letter, you can type your text here, and the 
program will enter it for you. The typical case now is to use the TiVo's 
new direct text entry method, which is selected by setting "Cols:" to 
zero (the default). This now works on the Series 3, HD and Premiere, and 
even works in HME apps if they've been updated to support it.

For apps that still require the old method, set "Cols:" to the number of 
columns in the keyboard, and ensure that the selector is on 'A' when you 
start sending the text. If these aren't set correctly, the results are 
unpredicatble.

The new method should be used when possible, since it's faster and 
reduces the risk of arrowing into the wrong place. Where it's not 
supported, only spaces and numbers will come through in this mode.


Command-line options
--------------------

-t, --force-tk   Use the Tkinter GUI even if PyGTK is available.

-l, --landscape  Move the second half of the button display to a
                 position to the right of the first half, instead of 
                 below it. The default layout is similar to a real TiVo 
                 peanut, which makes for a very tall, narrow window -- 
                 too tall for some environments.

-h, --help       Print help and exit.

-k, --keys       Print the list of keyboard shortcuts and exit.

-v, --version    Print the version and exit.

-z, --nozeroconf Don't try the Zeroconf-based method of detecting TiVos.

<address>        Any other command-line option is treated as the IP
                 address (name or numeric) of the TiVo to connect to.
                 Connection is automatic on startup, and disconnection
                 on exit.


Changes
-------

0.23 -- Direct text input for all supported TiVos, now based on the
        IRCODE command instead of the KEYBOARD command (which is
        equivalent except for being limited to the Premiere). This even
        works in HME apps now (if they're updated to recognize it), so
        this mode is now the default. Thanks to CT McCurdy for
        discovering this.

0.22 -- The new keyboard shortcut for the 'C' button conflicted with the
        one to toggle closed captions. Maybe closed caption toggling is
        too dangerous to have a keyboard shortcut anyway.

        Attempt to reconnect automatically.

        Report more (hopefully all) errors to the GUI instead of the 
        console.

        Expand elements of small windows in Tk, as with the main window.

        Some restructuring of the code, hopefully easier to follow.

        Finally added a README.txt.

0.21 -- Use a single window instead of creating and destroying multiple
        windows (eliminates the losing focus problem). Note that this
        causes some weirdness with Tkinter: if you manually resize the
        selector window, the new size is retained for the full window,
        otherwise the full window resizes itself properly.

0.20 -- A, B, C and D buttons for the Premiere; new layout with less
        excess space; function key shortcuts; "Aspect" becomes "Zoom".

0.19 -- Space and numbers weren't working in direct text input.

0.18 -- Direct text input for the Premiere; minor Zeroconf fixes;
        support for Australian/NZ TiVos and the Premiere in non-Zeroconf
        autodection.

0.17 -- Zeroconf-based autodetection. (This was the last version for 14
        months, until the release of the Premiere motivated me to resume
        development.)

0.16 -- Add TiVo HD XL to the supported list.

0.15 -- Make it compatible with Python 2.3; suppress the console window
        on Macs.

0.14 -- Adapt CC button for 9.4; pop up error on connection failure.

0.13 -- Autoconnect was failing on single-TiVo networks.

0.12 -- Delay between commands to address crashing TiVos; prompt for
        address if autodetect fails; minor fixes.

0.11 -- Autodetect TiVos; fix -h.

0.10 -- Fixes for numeric keypad in Tkinter on some platforms.

0.9  -- Shortcuts from the HME simulator, fix for Gtk in Windows, CLEAR
        at end of SPS30 and Clock, support numeric keypad.

0.8  -- More command-line options, fixes for keyboard shortcuts.

0.7  -- Landscape mode.

0.6  -- Keyboard shortcuts.

0.5  -- Text entry.

0.4  -- CC, SPS30, Clock.

0.3  -- Show status messages; allow address on command line; minor
        layout changes.

0.2  -- Added Tkinter support.
