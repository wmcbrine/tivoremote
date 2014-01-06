Network Remote Control for TiVo Series 3+, v0.28
by William McBrine <wmcbrine@gmail.com>
January 5, 2014

An on-screen virtual remote control that can control your TiVo over the 
network. It works with the Series 3 or any later TiVo model.

Python 2.x is required (tested on 2.5 through 2.7), as well as Tkinter 
(normally part of Python's standard library) or GTK. Mac OS X and Linux 
users should have what they need already; Windows users should visit 
http://python.org/ . The remote has also been tested on Windows CE and 
other platforms.

This program uses the network remote control interface first made public 
by TCF user Omikron in this thread:

http://tivocommunity.com/tivo-vb/showthread.php?t=392385

which has doubled as the support thread for the app, and, previously, 
the only place where it was distributed. Nowadays, the latest version 
can be found at:

http://wmcbrine.com/tivo/

Released under the GPL 2+.


Quick Start
-----------

By default, the TiVo's network remote service is disabled. To enable it, 
go into the "Messages and Settings" menu, then "Settings", "Remote, 
CableCARD, & Devices", and finally "Network Remote Control", and check 
"Enabled".

Once Python is installed on your system, you should be able to just 
extract the Network Remote archive anywhere, and click on "Network 
Remote.pyw", or run it from the command line. (Mac users may have to use 
the context menu if starting it from the GUI.) No installation is 
required. Network Remote.pyw is the only required file, although 
Zeroconf.py is also needed if you want to use the "modern" style of TiVo 
autodetection, which I recommend.

If it's working properly, you should within a few seconds see a list of 
available TiVos from which to select, or be immediately connected to 
your TiVo if only one is found. If autodetection fails, you'll instead 
get a prompt for your TiVo's address. Alternatively, you can directly 
specify the TiVo's address on the command line (see below).

Zeroconf-based autodetection needs to send and recieve UDP on port 5353. 
Old-style autodetection sends and recieves TCP and UDP on port 2190, and 
recieves TCP on a randomly-chosen port. The core remote functionality 
will work as long as it can make outgoing TCP connections to port 31339.


Buttons
-------

The function of most buttons should be obvious, but a few may need 
explanation:

Zoom -- Also known as "Aspect" or "Window" on pre-Premiere remotes; they
        all use the same code.

Aspect -- Rather then sending the IRCODE, as the Zoom button does, this
          cycles between zoom modes by sending discrete codes for each
          mode. This is the only way to access the TiVo's hidden stretch
          mode, and it's useful in HME apps that do video streaming, but
          don't act on the Zoom IRCODE.

CC -- Closed-caption toggle; now uses discrete commands for this purpose
      instead of the Info-Down-etc. sequence used in older versions.

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

Clock should be used only when playing back a recording. Otherwise, the 
results are unpredictable.


Keyboard Shortcuts
------------------

Most buttons have keyboard shortcuts, which can be much more convenient 
to use than mousing around and clicking. Of course these don't work when 
the text input window has focus. Numbers, letters (A/B/C/D buttons only; 
not for direct text input) and arrow keys are what you'd expect (use 
uppercase for A/B/C/D); other shortcuts are:

TiVo          t, F1, or F11
Zoom          z or w
Info          i or F10
LiveTV        l or F2
Guide         g or F3
Select        Enter/Return
Thumbs Down   d or F6
Thumbs Up     u or F5
Channel Up    PgUp or F7
Channel Down  PgDn or F8
Record        r or F9
Play          p
Reverse       v or [
Pause         Spacebar
Forward       f or ]
Replay        x or -
Slow          o
Skip          s or =
Clear         Esc
Enter         e or .
Aspect        a
CC            c
Quit          q

As a bonus, only available via keyboard shortcut:

Stop          `
Toggle graphical button labels      G
Switch between Landscape/Portrait   L

Some of these are taken from the keys used with TiVo's HME simulator 
from the Java SDK. The function keys are what the TiVo recognizes from 
an attached USB keyboard.

Buttons with no corresponding keyboard shortcuts: Clock and Standby.


Text Entry
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


Command-Line Options
--------------------

-v, --version    Print the version and exit.

-h, --help       Print help and exit.

-k, --keys       Print the list of keyboard shortcuts and exit.

-z, --nozeroconf Don't try the Zeroconf-based method of detecting TiVos.

-l, --landscape  Move the second half of the button display to a
                 position to the right of the first half, instead of 
                 below it. The default layout is similar to a real TiVo 
                 peanut, which makes for a very tall, narrow window -- 
                 too tall for some environments.

-g, --graphics   Force "graphical" labels for some buttons. Normally
                 they'll be used automatically on suitable platforms.

-p, --plaintext  Force plain text labels for all buttons. If both -g
                 and -p are specified, the last one on the command
                 line takes precedence.

-c, --nocolor    Don't use color to highlight any buttons.

-t, --force-tk   Use the Tkinter GUI even if GTK is available.

-2, --force-gtk2 Use the GTK 2 (PyGTK) GUI even if GTK 3 is available.

-o, --old-tk     Use the pre-ttk Tkinter code even if ttk is available.

<address>        Any other command-line option is treated as the IP
                 address (name or numeric) of the TiVo to connect to.
                 Connection is automatic on startup, and disconnection
                 on exit.


Changes
-------

0.28 -- The Mac app bundle is now signed (for compatibility with
        Gatekeeper), and sandboxed -- its only permissions are network
        access.

        GTK 3+ and ttk widgets for Tkinter are now supported, with
        fallbacks to the old APIs and options to select them. ttk often
        looks quite a bit nicer than the old Tk version. (ttk requires
        Python 2.7, AFAIK.)

        Color highlights are now used for a few keys (A/B/C/D, Thumbs,
        Rec, Pause), where available (can be disabled by option).

        The "graphical" button labels are now the default for most
        environments, selectable via option and, now, togglable at
        runtime by pressing "G" (capitalized -- lowercase "g" is still
        Guide).

        Landscape mode can also now be toggled at runtime, by pressing
        "L" (capitalized -- lowercase "l" is still LiveTV). In addition,
        at startup, if the remote is too "tall" for the screen, it will
        switch to landscape mode automatically.

        Restored shortcut keys for Aspect ("a") and CC ("c").

        More robust Zeroconf.

0.27 -- Enhancements for the Mac -- now builds a proper app bundle.

        The "Aspect" button is back, but it does something different
        from "Zoom" (which is also still present); see the "Buttons"
        section for details. To make a place for this, I've dropped the
        SPS30S macro button. (Since the setting is preserved across
        reboots now, it's less needed.)

        Some buttons now have an alternate, "graphical" rendering, via
        Unicode glyphs, selected by the "-g" command-line option. (This
        is on by default with the Mac app version.)

        Bug: The Thumbs Down shortcut 'd' was overridden by the one for
        the 'D' button. Fix: The A/B/C/D shortcuts are now capital
        (shifted) keys.

        Various minor fixes, reorganization, and doc changes.

        The program's name is now standardized as "Network Remote
        Control for TiVo", or "Network Remote" for short.

        Dropped support for Python 2.3 and 2.4.

0.26 -- In some Tkinter installations, with versions 0.24 and 0.25,
        pressing the space bar (to pause) would also invoke the default
        button widget response of the space bar selecting the button
        (in this case, the "Enter" button). First reported by "mjh".

0.25 -- The closed caption toggle is no longer a macro, but instead uses
        IRCODE CC_ON/OFF to change the mode directly. (The program
        assumes that captions are off at startup; if not, it just takes
        an extra button press to synchronize with the TiVo's state.)

0.24 -- Back to using the KEYBOARD command on the Premiere (only), as it
        turns out it's not quite equivalent after all. This new mode
        allows direct input of mixed case (instead of uppercasing
        everything, as previously, and still on pre-Premiere units), and
        of all standard keyboard symbols -- very close to the behavior
        of a Slide remote or other USB keyboard.

        The rearrangement of widget creation (?) in 0.20 effectively
        broke the setting of focus to the label in Tk -- since tabbing
        no longer went directly to the text entry field. Especialy
        noticeable on Macs, where there's no button highlighting. So, I
        now use focus_button, as in Gtk. Reported by "MelSmith".

        Changed the "SPS30", "Clock", and "CC" buttons from hardwired
        functions to ones built from a tuple, "MACROS". Perhaps these
        will be easier to redefine?

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
