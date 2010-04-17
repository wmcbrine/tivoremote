TCP/IP remote for TiVo Series 3+, v0.21
by William McBrine <wmcbrine@gmail.com>
April 17, 2010

A PyGTK/Tkinter-based virtual remote control for the TiVo Series 3,
TiVo HD or TiVo Premiere, using the port 31339 TCP/IP interface as
reverse-engineered by TCF user Omikron. Released under the GPL 2+.

    Command-line options:

    -t, --force-tk   Use the Tkinter GUI even if PyGTK is available. As
                     an alternative to using this option, you can set
                     the "use_gtk" variable to False.

    -l, --landscape  Move the second half of the button display to a
                     position to the right of the first half, instead of
                     below it. The default layout is similar to a real
                     TiVo peanut, which makes for a very tall, narrow
                     window -- too tall for some environments. The
                     "landscape" variable specifies the default.

    -h, --help       Print help and exit.

    -k, --keys       Print the list of keyboard shortcuts and exit.

    -v, --version    Print the version and exit.

    -z, --nozeroconf Don't try the Zeroconf-based method of detecting 
                     TiVos.

    <address>        Any other command-line option is treated as the IP
                     address (name or numeric) of the TiVo to connect
                     to. Connection is automatic on startup, and
                     disconnection on exit. The "tivo_address" variable
                     gives the default.

    Text entry:

    For the TiVo's on-screen keyboards, instead of moving the cursor
    around manually to select each letter, you can type your text here,
    and the program will do it automatically. Make sure that "Cols:"
    matches the number of columns in the keyboard, and that the selector
    is on 'A' at the start. Case changes are ignored.

    To use the new direct text entry method with a TiVo Premiere, set 
    "Cols:" to zero. Note that this may not work on all input fields.

    0               NUM0                1               NUM1           
    2               NUM2                3               NUM3           
    4               NUM4                5               NUM5           
    6               NUM6                7               NUM7           
    8               NUM8                9               NUM9           
    Down            DOWN                Escape          CLEAR          
    F1              TIVO                F10             INFO           
    F11             TIVO                F2              LIVETV         
    F3              GUIDE               F5              THUMBSUP       
    F6              THUMBSDOWN          F7              CHANNELUP      
    F8              CHANNELDOWN         F9              RECORD         
    KP_0            NUM0                KP_1            NUM1           
    KP_2            NUM2                KP_3            NUM3           
    KP_4            NUM4                KP_5            NUM5           
    KP_6            NUM6                KP_7            NUM7           
    KP_8            NUM8                KP_9            NUM9           
    KP_Decimal      ENTER               KP_Down         DOWN           
    KP_Enter        SELECT              KP_Left         LEFT           
    KP_Page_Down    CHANNELDOWN         KP_Page_Up      CHANNELUP      
    KP_Right        RIGHT               KP_Up           UP             
    Left            LEFT                Page_Down       CHANNELDOWN    
    Page_Up         CHANNELUP           Return          SELECT         
    Right           RIGHT               Up              UP             
    a               ACTION_A            b               ACTION_B       
    bracketleft     REVERSE             bracketright    FORWARD        
    c               ACTION_C            d               ACTION_D       
    e               ENTER               equal           ADVANCE        
    f               FORWARD             g               GUIDE          
    grave           STOP                i               INFO           
    l               LIVETV              minus           REPLAY         
    o               SLOW                p               PLAY           
    period          ENTER               r               RECORD         
    s               ADVANCE             space           PAUSE          
    t               TIVO                u               THUMBSUP       
    v               REVERSE             w               WINDOW         
    x               REPLAY              z               WINDOW         

Most keys should be obvious, but a few may need explanation:

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

A/B/C/D -- Currently these only work on the Premiere.

Kbd -- Sends the text in the "Text:" window. Note that you can just hit
       "Enter" on your keyboard when the text field is in focus to
       accomplish the same thing (not to be confused with "Enter" on the
       remote).

Standby -- Puts the TiVo into standby mode, or pulls it out of it (into
           LiveTV) if it already was. This function is available as a
           discrete remote code for universal remotes, but isn't on the 
           standard peanuts.

Quit -- Exits the remote program; doesn't send anything to the TiVo.

SPS30, CC and Clock should be used only when playing back a recording or 
in LiveTV mode. Otherwise, the results are unpredictable.
