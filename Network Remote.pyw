#!/usr/bin/env python

# Network Remote Control for TiVo Series 3+, v0.31
# Copyright 2008-2014 William McBrine
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You didn't receive a copy of the license with this program because 
# you already have dozens of copies, don't you? If not, visit gnu.org.

""" Network Remote Control for TiVo Series 3+

    A GTK/Tkinter-based virtual remote control for the TiVo Series 3,
    TiVo HD or TiVo Premiere, using the port 31339 TCP/IP interface as 
    reverse-engineered by TCF user Omikron.

    Command-line options:

    -v, --version    Print the version and exit.

    -h, --help       Print help and exit.

    -k, --keys       Print the list of keyboard shortcuts and exit.

    -z, --nozeroconf Don't try the Zeroconf-based method of detecting
                     TiVos.

    -l, --landscape  Move the second half of the button display to a
                     position to the right of the first half, instead of
                     below it. The default layout is similar to a real
                     TiVo peanut, which makes for a very tall, narrow
                     window -- too tall for some environments. The
                     "landscape" variable specifies the default.

    -g, --graphics   Force "graphical" labels for some buttons. Normally
                     they'll be used automatically on suitable platforms.

    -p, --plaintext  Force plain text labels for all buttons. If both -g
                     and -p are specified, the last one on the command
                     line takes precedence.

    -c, --nocolor    Don't use color to highlight any buttons.

    -t, --force-tk   Use the Tkinter GUI even if GTK is available. As
                     an alternative to using this option, you can set
                     the "use_gtk" variable to False.

    -2, --force-gtk2 Use the GTK 2 (PyGTK) GUI even if GTK 3 is
                     available. As an alternative to using this option,
                     you can set the "use_gtk3" variable to False.

    -o, --old-tk     Use the pre-ttk Tkinter code even if ttk is available.

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

    To use the new direct text entry method, set "Cols:" to zero. Note
    that this may not work on all input fields.

"""

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '0.31'
__license__ = 'GPL'

import random
import re
import select
import socket
import struct
import sys
import thread
import time

tivo_address = ''
tivo_port = 31339
tivo_name = ''
tivo_ports = {}
tivo_swversions = {}
landscape = False
use_gtk = True
use_gtk3 = True
has_ttk = True
use_gr = None
use_color = True
have_zc = True
captions_on = False
aspect_ratio = 0
sock = None
outer = None
focus_button = None   # This is just a widget to jump to when leaving 
                      # key_text.
exit_all = False
first_size = True
screen_width = 0
screen_height = 0

# Other globals: window, label, key_text, key_width (all widgets)

# Colors for special buttons

COLOR = {'red': '#d00', 'blue': '#00a', 'green': '#070', 'yellow': '#aa0'}

TITLE = 'Network Remote'

# About box text, for OS X only

ABOUT = """Network Remote Control for TiVo
Version %s
Copyright 2008-2014 %s
http://wmcbrine.com/tivo/""" % (__version__, __author__)

# IR codes for direct aspect ratio control

ASPECT_CODES = ['ASPECT_CORRECTION_ZOOM', 'ASPECT_CORRECTION_PANEL',
                'ASPECT_CORRECTION_FULL', 'ASPECT_CORRECTION_WIDE_ZOOM']

# IR codes to toggle closed captions

CC_CODES = ['CC_OFF', 'CC_ON']

# IR codes to switch video modes

VMODE_CODES = ['VIDEO_MODE_FIXED_480i', 'VIDEO_MODE_FIXED_480p',
               'VIDEO_MODE_FIXED_720p', 'VIDEO_MODE_FIXED_1080i',
               'VIDEO_MODE_HYBRID', 'VIDEO_MODE_HYBRID_720p',
               'VIDEO_MODE_HYBRID_1080i', 'VIDEO_MODE_NATIVE']

# Text, IR codes (if different from the text), number of columns (if 
# greater than one), function (if not irsend()), alternate graphical 
# representation (if defined), and color (if not black), for each 
# button. The ACTION_ buttons have an extra parameter, which is the 
# button "width" in "text units", vs. the default of 5. This is used 
# only in Tk, to align the buttons.

# Each list is a group, each inner list is a row, each dict is a button.

BUTTONS = [
           [ #0
               [{'t': 'TiVo', 'cols': 3}],
               [{'t': 'Zoom', 'val': 'WINDOW'},
                {'t': 'Info'}, {'t': 'LiveTV'}],
               [{'t': 'Back'}, {'t': 'Guide'},
                {'t': 'Misc', 'titles': ['Clock', 'SPS30', 'Find remote',
                 'Netflix'],
                 'codes': [['SELECT', 'PLAY', 'SELECT', 'NUM9', 
                 'SELECT', 'CLEAR'], ['SELECT', 'PLAY', 'SELECT', 
                 'NUM3', 'NUM0', 'SELECT', 'CLEAR'], ['FIND_REMOTE'],
                 ['NETFLIX']]}]
           ],

           [ #1
               [{}, {'t': 'Up', 'gr': u'\u2191'}],
               [{'t': 'Left', 'gr': u'\u2190'}, {'t': 'Select'},
                {'t': 'Right', 'gr': u'\u2192'}],
               [{'t': 'ThDn', 'val': 'THUMBSDOWN', 'gr': u'\u261f',
                 's': 'red'},
                {'t': 'Down', 'gr': u'\u2193'},
                {'t': 'ThUp', 'val': 'THUMBSUP', 'gr': u'\u261d',
                 's': 'green'}]
           ],

           [ #2
               [{'t': 'Aspt', 'titles': ['Zoom', 'Panel', 'Full', 'Stretch'],
                 'codes': ASPECT_CODES},
                {'t': 'CC', 'titles': ['Off', 'On'], 'codes': CC_CODES},
                {'t': 'Ch+', 'val': 'CHANNELUP'}],
               [{'t': 'Vid', 'titles': ['480i Fixed', '480p Fixed',
                 '720p Fixed', '1080i Fixed', 'Hybrid', '720p Hybrid',
                 '1080i Hybrid', 'Native'], 'codes': VMODE_CODES},
                {'t': 'Rec', 'val': 'RECORD', 'gr': u'\u25c9', 's': 'red'},
                {'t': 'Ch-', 'val': 'CHANNELDOWN'}]
           ],

           [ #3
               [{}, {'t': 'Play', 'gr': u'\u25b6'}],
               [{'t': 'Rev', 'val': 'REVERSE', 'gr': u'\u25c0\u25c0'},
                {'t': 'Pause', 'gr': u'\u2759\u2759', 's': 'yellow'},
                {'t': 'FF', 'val': 'FORWARD', 'gr': u'\u25b6\u25b6'}],
               [{'t': 'Replay', 'gr': u'\u21bb'},
                {'t': 'Slow', 'gr': u'\u2759\u25b6'},
                {'t': 'Adv', 'val': 'ADVANCE', 'gr': u'\u21e5'}]
           ],

           [ #4
               [{'t': 'A', 'val': 'ACTION_A', 'width': 3, 's': 'yellow'},
                {'t': 'B', 'val': 'ACTION_B', 'width': 3, 's': 'blue'},
                {'t': 'C', 'val': 'ACTION_C', 'width': 3, 's': 'red'},
                {'t': 'D', 'val': 'ACTION_D', 'width': 3, 's': 'green'}]
           ],

           [ #5
               [{'t': '1', 'val': 'NUM1'}, {'t': '2', 'val': 'NUM2'},
                {'t': '3', 'val': 'NUM3'}],
               [{'t': '4', 'val': 'NUM4'}, {'t': '5', 'val': 'NUM5'},
                {'t': '6', 'val': 'NUM6'}],
               [{'t': '7', 'val': 'NUM7'}, {'t': '8', 'val': 'NUM8'},
                {'t': '9', 'val': 'NUM9'}],
               [{'t': 'Clear'}, {'t': '0', 'val': 'NUM0'}, {'t': 'Enter'}]
           ],

           #6 - Text entry widgets will be added here
           [[], [{}, {}, {'t': 'Kbd', 'fn': 'keyboard'}]],

           #7
           [[{'t': 'Standby', 'cols': 2}, {}, {'t': 'Quit', 'fn': 'go_away'}]]
]

# Keyboard shortcuts and their corresponding IR codes

KEYS = {'t': 'TIVO',
        'z': 'WINDOW', 'i': 'INFO', 'l': 'LIVETV',
        'b': 'BACK', 'g': 'GUIDE',

        'Up': 'UP',
        'Left': 'LEFT', 'Return': 'SELECT', 'Right': 'RIGHT',
        'Down': 'DOWN',
        'd': 'THUMBSDOWN', 'u': 'THUMBSUP',

        'Page_Up': 'CHANNELUP', 'r': 'RECORD',
        'Page_Down': 'CHANNELDOWN',

        'Prior': 'CHANNELUP', 'Next': 'CHANNELDOWN',

        'p': 'PLAY', 'v': 'REVERSE',
        'space': 'PAUSE', 'f': 'FORWARD',
        'x': 'REPLAY', 'o': 'SLOW', 's': 'ADVANCE',

        'A': 'ACTION_A', 'B': 'ACTION_B', 'C': 'ACTION_C', 'D': 'ACTION_D',

        '1': 'NUM1', '2': 'NUM2', '3': 'NUM3',
        '4': 'NUM4', '5': 'NUM5', '6': 'NUM6',
        '7': 'NUM7', '8': 'NUM8', '9': 'NUM9',
        'Escape': 'CLEAR', '0': 'NUM0', 'period': 'ENTER',

        'KP_Up': 'UP',
        'KP_Left': 'LEFT', 'KP_Enter': 'SELECT', 'KP_Right': 'RIGHT',
        'KP_Down': 'DOWN',

        'KP_Page_Up': 'CHANNELUP', 'KP_Page_Down': 'CHANNELDOWN',

        'KP_1': 'NUM1', 'KP_2': 'NUM2', 'KP_3': 'NUM3',
        'KP_4': 'NUM4', 'KP_5': 'NUM5', 'KP_6': 'NUM6',
        'KP_7': 'NUM7', 'KP_8': 'NUM8', 'KP_9': 'NUM9',
        'KP_0': 'NUM0', 'KP_Decimal': 'ENTER',

        'bracketleft': 'REVERSE', 'bracketright': 'FORWARD',
        'minus': 'REPLAY', 'equal': 'ADVANCE', 'e': 'ENTER',
        'w': 'WINDOW', 'grave': 'STOP',

        'F1': 'TIVO', 'F2': 'LIVETV', 'F3': 'GUIDE', 'F5': 'THUMBSUP',
        'F6': 'THUMBSDOWN', 'F7': 'CHANNELUP', 'F8': 'CHANNELDOWN',
        'F9': 'RECORD', 'F10': 'INFO', 'F11': 'TIVO'}

# Keyboard shortcuts for functions

FUNCKEYS = {'q': 'go_away', 'a': 'aspect_change', 'c': 'closed_caption',
            'L': 'orient_change', 'G': 'graphics_change'}

# Named symbols for direct text input -- these work with IRCODE and
# KEYBOARD commands

SYMBOLS = {'-': 'MINUS', '=': 'EQUALS', '[': 'LBRACKET',
           ']': 'RBRACKET', '\\': 'BACKSLASH', ';': 'SEMICOLON',
           "'": 'QUOTE', ',': 'COMMA', '.': 'PERIOD', '/': 'SLASH',
           '`': 'BACKQUOTE', ' ': 'SPACE', '1': 'NUM1', '2': 'NUM2',
           '3': 'NUM3', '4': 'NUM4', '5': 'NUM5', '6': 'NUM6',
           '7': 'NUM7', '8': 'NUM8', '9': 'NUM9', '0': 'NUM0'}

# When in shift mode (with KEYBOARD command only), the same names
# map to a different set of symbols

SHIFT_SYMS = {'_': 'MINUS', '+': 'EQUALS', '{': 'LBRACKET',
              '}': 'RBRACKET', '|': 'BACKSLASH', ':': 'SEMICOLON',
              '"': 'QUOTE', '<': 'COMMA', '>': 'PERIOD', '?': 'SLASH',
              '~': 'BACKQUOTE', '!': 'NUM1', '@': 'NUM2', '#': 'NUM3',
              '$': 'NUM4', '%': 'NUM5', '^': 'NUM6', '&': 'NUM7',
              '*': 'NUM8', '(': 'NUM9', ')': 'NUM0'}

# Beacon template for find_tivos() and get_namever()

ANNOUNCE = """tivoconnect=1
method=%(method)s
platform=pc
identity=remote-%(port)x
services=TiVoMediaServer:%(port)d/http
"""

def go_away(widget=None):
    """ Non-error GUI exit. """
    global exit_all
    if sock:
        sock.close()
    if use_gtk:
        gtk.main_quit()
    else:
        window.quit()
    exit_all = True

def check_port():
    """ If tivo_address specifies a port, split it off and set
        tivo_port.

    """
    global tivo_address, tivo_port
    if ':' in tivo_address:
        tivo_address, port = tivo_address.split(':')
        try:
            tivo_port = int(port)
        except:
            pass

def connect():
    """ Connect to the TiVo within five seconds or report error. """
    global sock
    check_port()
    try:
        sock = socket.socket()
        sock.settimeout(5)
        sock.connect((tivo_address, tivo_port))
        sock.settimeout(None)
    except Exception, msg:
        msg = 'Could not connect to %s:\n%s' % (tivo_name, msg)
        error_window(msg)

def send(message):
    """ The core output function, called from irsend(). Re-connect if
        necessary (including restarting the status_update thread), send
        message, sleep, and check for errors.

    """
    if not sock:
        connect()
        thread.start_new_thread(status_update, ())
    try:
        sock.sendall(message)
        time.sleep(0.1)
    except Exception, msg:
        error_window(str(msg))

def irsend(*codes):
    """ Expand a command sequence for send(). """
    for each in codes:
        if type(each) == list:
            irsend(*each)
        else:
            send('IRCODE %s\r' % each)

def kbsend(*codes):
    """ Expand a KEYBOARD command sequence for send(). """
    for each in codes:
        send('KEYBOARD %s\r' % each)
        time.sleep(0.1)

def closed_caption(widget=None):
    """ Toggle closed captioning. """
    global captions_on
    captions_on = not captions_on
    irsend(CC_CODES[captions_on])

def aspect_change(widget=None):
    """ Toggle aspect ratio mode. """
    global aspect_ratio
    irsend(ASPECT_CODES[aspect_ratio])
    aspect_ratio += 1
    if aspect_ratio == len(ASPECT_CODES):
        aspect_ratio = 0

def kbd_arrows(text, width):
    """ Translate 'text' to a series of cursor motions for the on-screen
        keyboard. Assumes the standard A-Z layout, with 'width' number
        of columns. The cursor must be positioned on 'A' at the start,
        or Bad Things will happen. This mode is now only needed with old
        code (mostly old HME apps) that hasn't been updated to support
        direct keyboard input.

    """
    current_x, current_y = 0, 0

    for ch in text.upper():
        if 'A' <= ch <= 'Z':
            pos = ord(ch) - ord('A')
            target_y = pos / width
            target_x = pos % width
            if target_y > current_y:
                for i in xrange(target_y - current_y):
                    irsend('DOWN')
            else:
                for i in xrange(current_y - target_y):
                    irsend('UP')
            if target_x > current_x:
                for i in xrange(target_x - current_x):
                    irsend('RIGHT')
            else:
                for i in xrange(current_x - target_x):
                    irsend('LEFT')
            irsend('SELECT')
            current_y = target_y
            current_x = target_x
        elif '0' <= ch <= '9':
            irsend('NUM' + ch)
        elif ch == ' ':
            irsend('FORWARD')

def kbd_direct(text):
    """ Send 'text' directly using the IRCODE command. Select this mode
        by setting 'Cols' to 0.

    """
    for ch in text.upper():
        if 'A' <= ch <= 'Z':
            irsend(ch)
        elif ch in SYMBOLS:
            irsend(SYMBOLS[ch])

def kbd_direct_new(text):
    """ Send 'text' directly using the KEYBOARD command (Premiere only).
        Select this mode by setting 'Cols' to 0.

    """
    for ch in text:
        if 'A' <= ch <= 'Z':
            kbsend('LSHIFT', ch)
        elif 'a' <= ch <= 'z':
            kbsend(ch.upper())
        elif ch in SYMBOLS:
            kbsend(SYMBOLS[ch])
        elif ch in SHIFT_SYMS:
            kbsend('LSHIFT', SHIFT_SYMS[ch])

def keyboard(widget=None):
    """ Take input from the key_text Entry widget and send it to the
        TiVo. The key_width widget specifies the number of columns.

    """
    if use_gtk:
        text = key_text.get_text()
        width = key_width.get_value_as_int()
    else:
        text = key_text.get()
        width = int(key_width.get())

    if width:
        kbd_arrows(text, width)
    else:
        if tivo_swversions.get(tivo_name, 0.0) >= 12.0:
            kbd_direct_new(text)
        else:
            kbd_direct(text)

    if use_gtk:
        key_text.set_text('')
        focus_button.grab_focus()
    else:
        key_text.delete(0, 'end')
        focus_button.focus_set()

def make_button(widget, y, x, t, val=None, cols=1, width=5, fn=None, 
                gr=None, s=None, titles=None, codes=None):
    """ Create one button, given its coordinates, text, and command, or
        menu items.

    """
    def command(code):
        return lambda w=None: irsend(code)

    def popup(menu):
        return lambda w=None: menu.popup(None, None, None, 0, 0)

    if titles:
        # Menu button
        if use_gr and gr:
            t = gr
        if use_gtk:
            menu = gtk.Menu()
            if use_gtk3:
                button = gtk.MenuButton(t)
                button.set_popup(menu)
            else:
                button = gtk.Button(t)
                button.connect('clicked', popup(menu))
        else:
            button = ttk.Menubutton(widget, text=t, width=4)
            menu = Tkinter.Menu(button, tearoff=0)
            button['menu'] = menu

        for title, code in zip(titles, codes):
            if use_gtk:
                item = gtk.MenuItem(title)
                menu.append(item)
                item.connect('activate', command(code))
                item.show()
            else:
                menu.add_command(label=title, command=command(code))
    else:
        # Simple button
        if fn:
            fn = eval(fn)
        else:
            if not val:
                val = t.upper()
            fn = command(val)
        if use_gr and gr:
            t = gr

        if use_gtk:
            button = gtk.Button(t)
            button.connect('clicked', fn)
        else:
            button = ttk.Button(widget, text=t, command=fn, width=width)

    # Common
    if use_color and s:
        if use_gtk:
            button.get_child().modify_fg(norm, gdk.color_parse(COLOR[s]))
        else:
            if has_ttk:
                button.configure(style=s + '.TButton')
            else:
                button.config(foreground=COLOR[s])

    if use_gtk:
        button.connect('key_press_event', handle_gtk_key)
        widget.attach(button, x, x + cols, y, y + 1)
    else:
        button.bind('<Key>', handle_tk_key)
        button.grid(column=x, row=y, columnspan=cols, sticky='news')

    if t == 'Enter':
        global focus_button
        focus_button = button

def handle_key(key):
    """ Look up the code or other command for a keyboard shortcut.
        Unhandled keys (mainly, tab) are passed on.

    """
    if key in KEYS:
        irsend(KEYS[key])
    elif key in FUNCKEYS:
        eval(FUNCKEYS[key])()
    else:
        return False
    return True

def handle_tk_key(event):
    """ Tk only -- This function is connected to the <Key> event
        for each button.

    """
    key = event.keysym
    if handle_key(key):
        return 'break'

def handle_gtk_key(widget, event):
    """ Gtk only -- This function is connected to the key_press_event
        for each button.

    """
    key = gdk.keyval_name(event.keyval)
    return handle_key(key)

def handle_escape(widget, event):
    """ Gtk only -- when in key_text, take focus away if the user
        presses the Escape key. Other keys are passed on.

    """
    key = gdk.keyval_name(event.keyval)
    if key == 'Escape':
        focus_button.grab_focus()
        return True
    return False

def status_update():
    """ Read incoming messages from the socket in a separate thread and 
        display them.

    """
    global sock
    while True:
        try:
            status = sock.recv(80)
        except:
            status = ''
        status = status.strip().title()
        if use_gtk:
            gdk.threads_enter()
            label.set_text(status)
            gdk.threads_leave()
        else:
            label.config(text=status)
        if not status:
            sock.close()
            sock = None
            break

def recv_bytes(sock, length):
    """ Read length bytes from the socket. """
    block = ''
    while len(block) < length:
        add = sock.recv(length - len(block))
        if not add:
            break
        block += add
    return block

def recv_packet(sock):
    """ Read a packet with a length header from the socket. """
    length = struct.unpack('!I', recv_bytes(sock, 4))[0]
    return recv_bytes(sock, length)

def send_packet(sock, packet):
    """ Write a packet to the socket with a length header. """
    sock.sendall(struct.pack('!I', len(packet)) + packet)

def get_namever(address):
    """ Exchange TiVo Connect Discovery beacons, and extract the machine
        name and software version.

    """
    method = 'connected'
    port = 0
    our_beacon = ANNOUNCE % locals()
    machine_name = re.compile('machine=(.*)\n').findall
    swversion = re.compile('swversion=(\d*.\d*)').findall

    try:
        tsock = socket.socket()
        tsock.settimeout(2)
        tsock.connect((address, 2190))
        send_packet(tsock, our_beacon)
        tivo_beacon = recv_packet(tsock)
        tsock.settimeout(None)
        tsock.close()
        name = machine_name(tivo_beacon)[0]
        version = float(swversion(tivo_beacon)[0])
    except:
        name = address
        version = 0.0

    return name, version

def find_tivos():
    """ Find TiVos on the LAN by broadcasting an announcement, and
        setting up a fake HTTP server to catch the replies. (This is
        much, much faster than waiting for beacons from the TiVos.)

    """
    global tivo_swversions

    tcd_id = re.compile('TiVo_TCD_ID: (.*)\r\n').findall
    tcds = {}

    # Find and bind a free port for our fake server.
    hsock = socket.socket()
    attempts = 0
    while True:
        port = random.randint(0x8000, 0xffff)
        try:
            hsock.bind(('', port))
            break
        except:
            attempts += 1
            if attempts == 5:
                return None   # Can't bind a port.

    hsock.listen(5)

    # Broadcast an announcement.
    method = 'broadcast'
    try:
        usock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        usock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        usock.sendto(ANNOUNCE % locals(), ('255.255.255.255', 2190))
        usock.close()
    except:
        hsock.close()
        return None   # Broadcast failed.

    # Collect the queries made in response. These come quickly.
    while True:
        isock, junk1, junk2 = select.select([hsock], [], [], 1)
        if not isock:
            break
        client, address = hsock.accept()
        message = client.recv(1500)
        client.close()  # This is rather rude.
        tcd = tcd_id(message)[0]
        if tcd[0] >= '6' and tcd[:3] != '649':  # We only support S3+.
            tcds[tcd] = address[0]

    hsock.close()

    # Unfortunately the HTTP requests don't include the machine names, 
    # so we find them by making direct TCD connections to each TiVo.

    tivos = {}
    for tcd, address in tcds.items():
        name, version = get_namever(address)
        tivos[name] = address
        tivo_swversions[name] = version

    return tivos

def find_tivos_zc():
    """ Find TiVos on the LAN using Zeroconf. This is simpler and
        cleaner than the fake HTTP method, but slightly slower, and
        requires the Zeroconf module. (It's still much faster than
        waiting for beacons.)

    """
    global tivo_swversions, tivo_ports

    class ZCListener:
        def __init__(self, names):
            self.names = names

        def removeService(self, server, type, name):
            self.names.remove(name)

        def addService(self, server, type, name):
            self.names.append(name)

    REMOTE = '_tivo-remote._tcp.local.'

    tivos = {}
    tivos_rev = {}
    tivo_names = []

    # Get the names of TiVos offering network remote control
    try:
        serv = zeroconf.Zeroconf()
        browser = zeroconf.ServiceBrowser(serv, REMOTE, ZCListener(tivo_names))
    except:
        return tivos

    # Give them a second to respond
    time.sleep(1)

    # For proxied TiVos, remove the original
    for t in tivo_names[:]:
        if t.startswith('Proxy('):
            try:
                t = t.replace('.' + REMOTE, '')[6:-1] + '.' + REMOTE
                tivo_names.remove(t)
            except:
                pass

    # Now get the addresses -- this is the slow part
    swversion = re.compile('(\d*.\d*)').findall
    for t in tivo_names:
        s = serv.getServiceInfo(REMOTE, t)
        if s:
            name = t.replace('.' + REMOTE, '')
            address = socket.inet_ntoa(s.getAddress())
            try:
                version = float(swversion(s.getProperties()['swversion'])[0])
            except:
                version = 0.0
            tivos[name] = address
            tivos_rev[address] = name
            tivo_ports[name] = s.getPort()
            tivo_swversions[name] = version

    # For proxies with numeric names, remove the original
    for t in tivo_names:
        if t.startswith('Proxy('):
            address = t.replace('.' + REMOTE, '')[6:-1]
            if address in tivos_rev:
                tivos.pop(tivos_rev[address])

    serv.close()
    return tivos

def init_window():
    """ Create the program's window. """
    global window, screen_width, screen_height
    if use_gtk:
        window = gtk.Window()
        window.connect('destroy', go_away)
        window.set_title(TITLE)
        if use_gtk3:
            screen_width = gdk.Screen.width()
            screen_height = gdk.Screen.height()
        else:
            screen_width = gdk.screen_width()
            screen_height = gdk.screen_height()
    else:
        window = Tkinter.Tk()
        if 'aqua' == window.tk.call('tk', 'windowingsystem'):
            mac_setup()
        elif 'win32' == sys.platform:
            window.iconbitmap('remote.ico')
        window.title(TITLE)
        window.protocol('WM_DELETE_WINDOW', go_away)
        if use_color and has_ttk:
            s = ttk.Style()
            for name, color in COLOR.items():
                s.map(name + '.TButton', foreground=[('!active', color)])
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

def mac_setup():
    """ Tk / OS X only -- Mac-specific setup. """
    global window

    # Hide the console
    try:
        window.tk.call('console', 'hide')
    except:
        pass

    # Set up the "About" box
    try:
        window.createcommand('tkAboutDialog', about_window)
    except:
        pass

    # Provide only the help menu (plus the application menu)
    main_menu = Tkinter.Menu()
    window.configure(menu=main_menu)
    help_menu = Tkinter.Menu(main_menu, name='help')
    main_menu.add_cascade(label='Help', menu=help_menu)

def about_window():
    """ Tk / OS X only -- pop up the "About" box. """
    tkMessageBox.showinfo('', ABOUT)

def make_widget_expandable(widget):
    """ Tk only -- mark each cell as expandable. """
    width, height = widget.grid_size()
    for i in xrange(width):
        widget.columnconfigure(i, weight=1)
    for i in xrange(height):
        widget.rowconfigure(i, weight=1)

def make_label(label, y=0):
    """ Add a label at line y. """
    if use_gtk:
        vbox = gtk.VBox()
        for l in label.split('\n'):
            vbox.add(gtk.Label(l))
        outer.attach(vbox, 0, 1, y, y + 1)
    else:
        ttk.Label(outer, text=label).grid(column=0, row=y)

def make_small_window(label):
    """ Common init for list_tivos() and error_window(). """
    global outer
    if use_gtk:
        outer = gtk.Table()
        outer.set_border_width(10)
    else:
        outer = ttk.Frame(window, borderwidth=10)
        outer.pack(fill='both', expand=1)
    make_label(label)
    if use_gtk:
        window.add(outer)

def main_window_clear():
    """ Remove all widgets from the inside of the window. """
    global outer
    if outer:
        if use_gtk:
            outer.destroy()
            gtk.main_quit()
        else:
            outer.forget()
            window.quit()
        outer = None

def error_window(message):
    """ Display an error message, and exit the program. """
    main_window_clear()
    make_small_window(message)
    if use_gtk:
        button = gtk.Button('Ok')
        button.connect('clicked', gtk.main_quit)
        outer.attach(button, 0, 1, 1, 2)
        window.show_all()
        gtk.main()
    else:
        button = ttk.Button(outer, text='Ok', command=window.quit)
        button.grid(column=0, row=1, sticky='news')
        make_widget_expandable(outer)
        window.mainloop()
    sys.exit()

def orient_change(widget=None):
    """ Toggle between landscape and portrait orientations. """
    global landscape
    main_window_clear()
    landscape = not landscape

def graphics_change(widget=None):
    """ Toggle the use of "special" characters as button labels. """
    global use_gr
    main_window_clear()
    use_gr = not use_gr

def list_tivos(tivos):
    """ TiVo chooser -- show buttons with TiVo names, if available, plus 
        an entry box for the user to specify an address if needed.

    """
    def choose_tivo(window, name, address):
        global tivo_name, tivo_address, tivo_port
        tivo_name = name
        tivo_address = address
        if name in tivo_ports:
            tivo_port = tivo_ports[name]
        main_window_clear()

    def set_address(window, address_box):
        global tivo_address
        if use_gtk:
            tivo_address = address_box.get_text()
        else:
            tivo_address = address_box.get()
        main_window_clear()

    def make_tivo_button(widget, window, y, name, address):
        command = lambda w=None: choose_tivo(window, name, address)
        text = '%s: %s' % (name, address)
        if use_gtk:
            button = gtk.Button(text)
            button.connect('clicked', command)
            widget.attach(button, 0, 1, y, y + 1)
        else:
            button = ttk.Button(widget, text=text, command=command)
            button.grid(column=0, row=y, sticky='news')

    if tivos:
        make_small_window('Choose a TiVo:')

        names = tivos.keys()
        names.sort()
        for i, name in enumerate(names):
            make_tivo_button(outer, window, i + 1, name, tivos[name])
        make_label('Or enter an address:', i + 2)
        i += 3
    else:
        make_small_window('Enter a TiVo address:')
        i = 1

    if use_gtk:
        address_box = gtk.Entry()
        outer.attach(address_box, 0, 1, i, i + 1)
    else:
        address_box = ttk.Entry(outer)
        address_box.grid(column=0, row=i, sticky='news')
        if not tivos:
            address_box.focus_set()

    command = lambda w=None: set_address(window, address_box)

    if use_gtk:
        address_box.connect('activate', command)
        window.show_all()
        gtk.main()
    else:
        address_box.bind('<Return>', command)
        make_widget_expandable(outer)
        window.mainloop()

def pick_tivo():
    """ Find the desired TiVo's name and address, using several possible
        methods; if none is set, exit the program.

    """
    global tivo_name, tivo_swversions
    if not tivo_address:
        tivos = {}
        if have_zc:
            tivos = find_tivos_zc()
        if not tivos:
            tivos = find_tivos()
        list_tivos(tivos)

    if not tivo_address:
        sys.exit()

    if not tivo_name:
        tivo_name, version = get_namever(tivo_address)
        tivo_swversions[tivo_name] = version

def too_tall(h):
    """ If the window is too tall for the screen, switch to landscape 
        mode (only used when the main window is first drawn).

    """
    global first_size
    if first_size:
        first_size = False
        if not landscape and (screen_width > screen_height and
                              h > screen_height):
            orient_change()
            return True

def main_window():
    """ Draw the main window and handle its events. """
    global window, outer, label, key_text, key_width, first_size

    if use_gtk:
        # Init
        window.set_title(tivo_name)
        window.resize(1, 1)
        outer = gtk.VBox()
        vbox1 = gtk.VBox()
        vbox2 = gtk.VBox()
        label = gtk.Label()
        table = [gtk.Table(homogeneous=True) for i in xrange(8)]
        outer.set_border_width(10)
        for tb in table:
            tb.set_border_width(5)
        for i in xrange(4):
            vbox1.add(table[i])
            vbox2.add(table[i + 4])
        vbox1.set_border_width(5)
        vbox2.set_border_width(5)
        window.add(outer)
        if landscape:
            hbox = gtk.HBox(homogeneous=True)
            hbox.add(vbox1)
            hbox.add(vbox2)
            outer.add(hbox)
            vbox2.add(label)
        else:
            outer.add(vbox1)
            outer.add(vbox2)
            outer.add(label)

        # Text entry
        table[6].attach(gtk.Label('Text:'), 0, 1, 0, 1)
        table[6].attach(gtk.Label('Cols:'), 0, 1, 1, 2)

        key_text = gtk.Entry()
        key_text.connect('activate', keyboard)
        key_text.connect('key_press_event', handle_escape)
        table[6].attach(key_text, 1, 3, 0, 1)

        adj = gtk.Adjustment(lower=0, upper=9, step_incr=1)
        key_width = gtk.SpinButton(adjustment=adj)
        table[6].attach(key_width, 1, 2, 1, 2)
    else:
        # Init
        window.title(tivo_name)
        outer = ttk.Frame(window, borderwidth=10)
        outer.pack(fill='both', expand=1)
        vbox1 = ttk.Frame(outer, borderwidth=5)
        vbox2 = ttk.Frame(outer, borderwidth=5)
        table = [ttk.Frame(box, borderwidth=5)
                 for box in (vbox1, vbox2) for i in xrange(4)]
        for tb in table:
            tb.grid(sticky='news')
        if landscape:
            label = ttk.Label(vbox2)
            vbox1.grid(row=0, sticky='news')
            vbox2.grid(row=0, column=1, sticky='news')
            label.grid(row=4)
        else:
            label = ttk.Label(outer)
            vbox1.grid(row=0, sticky='news')
            vbox2.grid(row=1, sticky='news')
            label.grid(row=2)

        # Text entry
        ttk.Label(table[6], text='Text:').grid(column=0, row=0)
        ttk.Label(table[6], text='Cols:').grid(column=0, row=1)

        key_text = ttk.Entry(table[6], width=15)
        key_text.bind('<Return>', keyboard)
        key_text.bind('<Escape>', lambda w: focus_button.focus_set())
        key_text.grid(column=1, row=0, columnspan=2, sticky='news')

        if has_ttk:
            key_width = ttk.Combobox(table[6], width=2,
                values=[str(i) for i in xrange(10)])
            key_width.current(0)
        else:
            key_width = Tkinter.Spinbox(table[6], from_=0, to=9, width=2)
        key_width.grid(column=1, row=1, sticky='news')

    for z, button_group in enumerate(BUTTONS):
        for y, row in enumerate(button_group):
            for x, each in enumerate(row):
                if each:
                    make_button(table[z], y, x, **each)

    if not use_gtk:
        for w in table + [vbox1, vbox2, outer]:
            make_widget_expandable(w)

        focus_button.focus_set()

    thread.start_new_thread(status_update, ())

    if use_gtk:
        window.show_all()
        focus_button.grab_focus()
        if first_size:
            window.connect('size-allocate', lambda w, e: too_tall(e.height))
        gtk.main()
    else:
        if first_size:
            window.update()
            if too_tall(window.winfo_height()):
                return
        window.mainloop()

def key_print(keyl):
    """ Print descriptions for a block of keyboard shortcuts. """
    keynames = keyl.keys()
    keynames.sort()
    for i, each in enumerate(keynames):
        print '   ', each.ljust(15), keyl[each].ljust(15),
        if i & 1:
            print
    print

if __name__ == '__main__':
    # Process the command line

    if len(sys.argv) > 1:
        for opt in sys.argv[1:]:
            if opt in ('-v', '--version'):
                print 'Network Remote Control for TiVo Series 3+', __version__
                sys.exit()
            elif opt in ('-h', '--help'):
                print __doc__
                sys.exit()
            elif opt in ('-k', '--keys'):
                key_print(KEYS)
                key_print(FUNCKEYS)
                sys.exit()
            elif opt in ('-z', '--nozeroconf'):
                have_zc = False
            elif opt in ('-l', '--landscape'):
                landscape = True
            elif opt in ('-g', '--graphics'):
                use_gr = True
            elif opt in ('-p', '--plaintext'):
                use_gr = False
            elif opt in ('-c', '--nocolor'):
                use_color = False
            elif opt in ('-t', '--force-tk'):
                use_gtk = False
            elif opt in ('-2', '--force-gtk2'):
                use_gtk3 = False
            elif opt in ('-o', '--old-tk'):
                has_ttk = use_gtk = False
            else:
                tivo_address = opt

    # Zeroconf or not?

    try:
        assert(have_zc)
        import zeroconf
    except:
        have_zc = False

    # Gtk or Tk?

    try:
        assert(use_gtk)
        try:
            assert(use_gtk3)
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import GObject as gobject
            from gi.repository import Gtk as gtk
            from gi.repository import Gdk as gdk
            norm = gtk.StateType.NORMAL
        except:
            use_gtk3 = False
            import pygtk
            pygtk.require('2.0')
            import gobject
            import gtk
            from gtk import gdk
            norm = gtk.STATE_NORMAL
        gobject.threads_init()
    except:
        import Tkinter
        import tkMessageBox
        use_gtk = False
        try:
            assert(has_ttk)
            import ttk
        except:
            global ttk
            ttk = Tkinter
            has_ttk = False

    # use_gr if not -g or -p?

    if use_gr == None:
        use_gr = (use_gtk or sys.platform == 'darwin' or
            (sys.platform == 'win32' and sys.getwindowsversion()[0] >= 6))

    init_window()
    pick_tivo()
    connect()
    while not exit_all:
        main_window()
