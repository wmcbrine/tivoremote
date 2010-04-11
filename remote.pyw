#!/usr/bin/env python

# TCP/IP remote for TiVo Series 3+, v0.21
# Copyright 2010 William McBrine
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

""" TCP/IP remote for TiVo Series 3+

    A PyGTK/Tkinter-based virtual remote control for the TiVo Series 3,
    TiVo HD or TiVo Premiere, using the port 31339 TCP/IP interface as 
    reverse-engineered by TCF user Omikron.

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

"""

__author__ = 'William McBrine <wmcbrine@gmail.com>'
__version__ = '0.21'
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
tivo_name = ''
landscape = False
use_gtk = True
have_zc = True
focus_button = None   # This is just a widget to jump to when leaving 
                      # key_text in Gtk, since I can't focus on a Label 
                      # there. (Set in make_button().) I use 'Enter' so 
                      # that I can tab from there to key_text, as in Tk.

# Other globals: window, label, key_text, key_width (all widgets)

TITLE = 'TiVo Remote'

# Coordinates (Y, X), text, IR code (if different from the text) and
# number of columns (if greater than one) for each simple button -- this
# doesn't include the buttons that send a series of codes, or those that
# call anything other than irsend(). Finally, the ACTION_ buttons have a
# sixth parameter, which is the button "width" in "text units", vs. the 
# default of 5. This is used only in Tk, to align the buttons.

BUTTONS = (((0, 0, 'TiVo', 'TIVO', 3),
            (1, 0, 'Zoom', 'WINDOW'), (1, 1, 'Info'), (1, 2, 'LiveTV'),
            (2, 0, 'Guide', 'GUIDE', 3)),

           ((0, 1, 'Up'),
            (1, 0, 'Left'), (1, 1, 'Select'), (1, 2, 'Right'),
            (2, 1, 'Down'),
            (2, 0, 'ThDn', 'THUMBSDOWN'), (2, 2, 'ThUp', 'THUMBSUP')),

           ((0, 2, 'Ch+', 'CHANNELUP'), (1, 1, 'Rec', 'RECORD'),
            (1, 2, 'Ch-', 'CHANNELDOWN')),

           ((0, 1, 'Play'), (1, 0, 'Rev', 'REVERSE'),
            (1, 1, 'Pause'), (1, 2, 'FF', 'FORWARD'),
            (2, 0, 'Replay'), (2, 1, 'Slow'), (2, 2, 'Skip', 'ADVANCE')),

           ((0, 0, 'A', 'ACTION_A', 1, 3), (0, 1, 'B', 'ACTION_B', 1, 3),
            (0, 2, 'C', 'ACTION_C', 1, 3), (0, 3, 'D', 'ACTION_D', 1, 3)),

           ((0, 0, '1'), (0, 1, '2'), (0, 2, '3'),
            (1, 0, '4'), (1, 1, '5'), (1, 2, '6'),
            (2, 0, '7'), (2, 1, '8'), (2, 2, '9'), 
            (3, 0, 'Clear'), (3, 1, '0'), (3, 2, 'Enter')))

# Keyboard shortcuts and their corresponding IR codes

KEYS = {'t': 'TIVO',
        'z': 'WINDOW', 'i': 'INFO', 'l': 'LIVETV',
        'g': 'GUIDE',

        'Up': 'UP',
        'Left': 'LEFT', 'Return': 'SELECT', 'Right': 'RIGHT',
        'Down': 'DOWN',
        'd': 'THUMBSDOWN', 'u': 'THUMBSUP',

        'Page_Up': 'CHANNELUP', 'r': 'RECORD',
        'Page_Down': 'CHANNELDOWN',

        'p': 'PLAY', 'v': 'REVERSE',
        'space': 'PAUSE', 'f': 'FORWARD',
        'x': 'REPLAY', 'o': 'SLOW', 's': 'ADVANCE',

        'a': 'ACTION_A', 'b': 'ACTION_B', 'c': 'ACTION_C', 'd': 'ACTION_D',

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

# Beacon template for find_tivos() and get_name()

ANNOUNCE = """tivoconnect=1
method=%(method)s
platform=pc
identity=remote-%(port)x
services=TiVoMediaServer:%(port)d/http
"""

# Process the command line

if len(sys.argv) > 1:
    for opt in sys.argv[1:]:
        if opt in ('-v', '--version'):
            print 'TCP/IP remote for TiVo Series 3+', __version__
            exit()
        elif opt in ('-h', '--help'):
            print __doc__
            exit()
        elif opt in ('-k', '--keys'):
            keynames = KEYS.keys()
            keynames.sort()
            for i, each in enumerate(keynames):
                print '   ', each.ljust(15), KEYS[each].ljust(15),
                if i & 1:
                    print
            exit()
        elif opt in ('-t', '--force-tk'):
            use_gtk = False
        elif opt in ('-l', '--landscape'):
            landscape = True
        elif opt in ('-z', '--nozeroconf'):
            have_zc = False
        else:
            tivo_address = opt

# Zeroconf or not?

try:
    assert(have_zc)
    import Zeroconf
except:
    have_zc = False

# Gtk or Tk?

try:
    assert(use_gtk)
    import pygtk
    pygtk.require('2.0')
    import gobject
    import gtk
    gobject.threads_init()
except:
    import Tkinter
    use_gtk = False

def go_away(widget=None):
    if sock:
        sock.close()
    if use_gtk:
        gtk.main_quit()
    else:
        window.quit()

def irsend(*codes):
    for each in codes:
        sock.sendall('IRCODE %s\r' % each)
        time.sleep(0.1)

def closed_caption(widget=None):
    """ Toggle closed captioning. """
    irsend('CLEAR', 'INFO', 'DOWN', 'DOWN', 'DOWN', 'DOWN', 'SELECT', 'CLEAR')

def sps30(widget=None):
    """ Toggle the 30-second skip function of the Advance button. """
    irsend('SELECT', 'PLAY', 'SELECT', 'NUM3', 'NUM0', 'SELECT', 'CLEAR')

def sps9(widget=None):
    """ Toggle display of the on-screen clock. """
    irsend('SELECT', 'PLAY', 'SELECT', 'NUM9', 'SELECT', 'CLEAR')

def kbd_arrows(text, width):
    """ Translate 'text' to a series of cursor motions for the on-screen 
        keyboard. Assumes the standard A-Z layout, with 'width' number 
        of columns. The cursor must be positioned on 'A' at the start, 
        or Bad Things will happen.

    """
    current_x, current_y = 0, 0

    for ch in text.strip().upper():
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
    """ Send 'text' using the KEYBOARD command. As of now, this works 
        only on the TiVo Premiere, and not on HME menus there. Select 
        this mode by setting 'Cols' to 0.

    """
    for ch in text.strip().upper():
        if 'A' <= ch <= 'Z':
            sock.sendall('KEYBOARD %s\r' % ch)
            time.sleep(0.1)
        elif '0' <= ch <= '9':
            irsend('NUM' + ch)
        elif ch == ' ':
            irsend('FORWARD')

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
        kbd_direct(text)

    if use_gtk:
        key_text.set_text('')
        focus_button.grab_focus()
    else:
        key_text.delete(0, 'end')
        label.focus_set()

def make_button(widget, y, x, text, command, cols=1, width=5):
    """ Create one button, given its coordinates, text and command. """
    if use_gtk:
        button = gtk.Button(text)
        button.connect('clicked', command)
        button.connect('key_press_event', handle_gtk_key)
        widget.attach(button, x, x + cols, y, y + 1)
        if text == 'Enter':
            global focus_button
            focus_button = button
    else:
        button = Tkinter.Button(widget, text=text, command=command, width=width)
        button.grid(column=x, row=y, columnspan=cols, sticky='news')

def make_tk_key(key, code):
    """ Tk only -- bind handler functions for each keyboard shortcut.
        For convenience, they're bound to the label widget, which
        doesn't get highlighted when it receives focus.

    """
    key = key.replace('Page_Up', 'Prior').replace('Page_Down', 'Next')
    if len(key) > 1:
        key = '<' + key + '>'
    try:
        label.bind(key, lambda w: irsend(code))
    except:
        pass  # allow for unknown keys

def handle_gtk_key(widget, event):
    """ Gtk only -- look up the code or other command for a keyboard
        shortcut. This function is connected to the key_press_event for
        each button. Unhandled keys (mainly, tab) are passed on.

    """
    key = gtk.gdk.keyval_name(event.keyval)
    if key in KEYS:
        irsend(KEYS[key])
    elif key == 'c':
        closed_caption()
    elif key == 'q':
        go_away()
    else:
        return False
    return True

def handle_escape(widget, event):
    """ Gtk only -- when in key_text, take focus away if the user
        presses the Escape key. Other keys are passed on.

    """
    key = gtk.gdk.keyval_name(event.keyval)
    if key == 'Escape':
        focus_button.grab_focus()
        return True
    return False

def make_ircode(widget, y, x, text, value='', cols=1, width=5):
    """ Make an IRCODE command, then make a button with it. """
    if not value:
        if '0' <= text <= '9':
            value = 'NUM' + text
        else:
            value = text.upper()
    make_button(widget, y, x, text, lambda w=None: irsend(value), cols, width)

def status_update():
    """ Read incoming messages from the socket in a separate thread and 
        display them.

    """
    while True:
        status = sock.recv(80)
        if not status:
            break
        status = status.strip().title()
        if use_gtk:
            gtk.gdk.threads_enter()
            label.set_text(status)
            gtk.gdk.threads_leave()
        else:
            label.config(text=status)

def get_name(address):
    """ Exchange TiVo Connect Discovery beacons, and extract the machine
        name.

    """
    method = 'connected'
    port = 0
    our_beacon = ANNOUNCE % locals()
    machine_name = re.compile('machine=(.*)\n').search

    try:
        tsock = socket.socket()
        tsock.connect((address, 2190))

        tsock.send(struct.pack('!I', len(our_beacon)))
        tsock.send(our_beacon)

        length = struct.unpack('!I', tsock.recv(4))[0]
        tivo_beacon = tsock.recv(length)

        tsock.close()

        name = machine_name(tivo_beacon).groups()[0]
    except:
        name = address

    return name

def find_tivos():
    """ Find TiVos on the LAN by broadcasting an announcement, and
        setting up a fake HTTP server to catch the replies. (This is
        much, much faster than waiting for beacons from the TiVos.)

    """
    tcd_id = re.compile('TiVo_TCD_ID: (.*)\r\n').search
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
        isock, junk1, junk2 = select.select([hsock], [], [], 0.5)
        if not isock:
            break
        client, address = hsock.accept()
        message = client.recv(1500)
        client.close()  # This is rather rude.
        tcd = tcd_id(message).groups()[0]
        if tcd[0] >= '6' and tcd[:3] != '649':  # We only support S3/S4.
            tcds[tcd] = address[0]

    hsock.close()

    # Unfortunately the HTTP requests don't include the machine names, 
    # so we find them by making direct TCD connections to each TiVo.

    tivos = {}
    for tcd, address in tcds.items():
        tivos[get_name(address)] = address

    return tivos

def find_tivos_zc():
    """ Find TiVos on the LAN using Zeroconf. This is simpler and
        cleaner than the fake HTTP method, but slightly slower, and
        requires the Zeroconf module. (It's still much faster than
        waiting for beacons.)

    """
    class ZCListener:
        def __init__(self, names):
            self.names = names

        def removeService(self, server, type, name):
            self.names.remove(name)

        def addService(self, server, type, name):
            self.names.append(name)

    REMOTE = '_tivo-remote._tcp.local.'

    tivos = {}
    tivo_names = []

    # Get the names of TiVos offering network remote control
    serv = Zeroconf.Zeroconf()
    browser = Zeroconf.ServiceBrowser(serv, REMOTE, ZCListener(tivo_names))

    # Give them half a second to respond
    time.sleep(0.5)

    # Now get the addresses -- this is the slow part
    for t in tivo_names:
        name = t.replace('.' + REMOTE, '')
        address = socket.inet_ntoa(serv.getServiceInfo(REMOTE, t).getAddress())
        tivos[name] = address

    serv.close()
    return tivos

def make_widget_expandable(widget):
    """ Tk only -- mark each cell as expandable. """
    width, height = widget.grid_size()
    for i in xrange(width):
        widget.columnconfigure(i, weight=1)
    for i in xrange(height):
        widget.rowconfigure(i, weight=1)

def make_small_window(label):
    """ Common init for get_address() and list_tivos(). """
    if use_gtk:
        table = gtk.Table()
        table.set_border_width(10)
        vbox = gtk.VBox()
        for l in label.split('\n'):
            vbox.add(gtk.Label(l))
        table.attach(vbox, 0, 1, 0, 1)
        window.add(table)
    else:
        table = Tkinter.Frame(window, borderwidth=10)
        table.grid()
        Tkinter.Label(table, text=label).grid(column=0, row=0)

    return table

def error_window(message):
    table = make_small_window(message)
    if use_gtk:
        button = gtk.Button('Ok')
        button.connect('clicked', gtk.main_quit)
        table.attach(button, 0, 1, 1, 2)
        window.show_all()
        gtk.main()
    else:
        button = Tkinter.Button(table, text='Ok', command=window.quit)
        button.grid(column=0, row=1, sticky='ew')
        window.mainloop()
    exit()

def get_address():
    """ Prompt for an address. """
    def set_address(window, address):
        global tivo_address
        if use_gtk:
            tivo_address = address.get_text()
        else:
            tivo_address = address.get()
        if use_gtk:
            table.destroy()
            gtk.main_quit()
        else:
            table.grid_forget()
            window.quit()

    table = make_small_window('Enter a TiVo address:')

    if use_gtk:
        address = gtk.Entry()
        table.attach(address, 0, 1, 1, 2)
    else:
        address = Tkinter.Entry(table)
        address.grid(column=0, row=1, sticky='ew')
        address.focus_set()

    command = lambda w=None: set_address(window, address)

    if use_gtk:
        address.connect('activate', command)
        window.show_all()
        gtk.main()
    else:
        address.bind('<Return>', command)
        window.mainloop()

def list_tivos(tivos):
    """ TiVo chooser -- show buttons with TiVo names. """
    def choose_tivo(window, name, address):
        global tivo_name, tivo_address
        tivo_name = name
        tivo_address = address
        if use_gtk:
            table.destroy()
            gtk.main_quit()
        else:
            table.grid_forget()
            window.quit()

    def make_tivo_button(widget, window, y, name, address):
        command = lambda w=None: choose_tivo(window, name, address)
        text = '%s: %s' % (name, address)
        if use_gtk:
            button = gtk.Button(text)
            button.connect('clicked', command)
            widget.attach(button, 0, 1, y, y + 1)
        else:
            button = Tkinter.Button(widget, text=text, command=command)
            button.grid(column=0, row=y, sticky='ew')

    table = make_small_window('Choose a TiVo:')

    names = tivos.keys()
    names.sort()
    for i, name in enumerate(names):
        make_tivo_button(table, window, i + 1, name, tivos[name])

    if use_gtk:
        window.show_all()
        gtk.main()
    else:
        window.mainloop()

sock = None

if use_gtk:
    window = gtk.Window()
    window.connect('destroy', go_away)
    window.set_title(TITLE)
else:
    window = Tkinter.Tk()
    try:
        window.tk.call('console', 'hide')  # fix a problem on Mac OS X
    except Tkinter.TclError:
        pass
    window.title(TITLE)
    window.protocol('WM_DELETE_WINDOW', go_away)

if not tivo_address:
    tivos = {}
    if have_zc:
        tivos = find_tivos_zc()
    if not tivos:
        tivos = find_tivos()
    if not tivos:
        get_address()
    elif len(tivos) == 1:
        tivo_name, tivo_address = list(tivos.items())[0]
    else:
        list_tivos(tivos)

if not tivo_address:
    exit()

if not tivo_name:
    tivo_name = get_name(tivo_address)

try:
    sock = socket.socket()
    sock.settimeout(5)
    sock.connect((tivo_address, 31339))
    sock.settimeout(None)
except Exception, msg:
    msg = 'Could not connect to %s:\n%s' % (tivo_name, msg)
    error_window(msg)

if use_gtk:
    # Init
    window.set_title(tivo_name)
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

    adj = gtk.Adjustment(value=4, lower=0, upper=9, step_incr=1)
    key_width = gtk.SpinButton(adjustment=adj)
    table[6].attach(key_width, 1, 2, 1, 2)
else:
    # Init
    window.title(tivo_name)
    outer = Tkinter.Frame(window, borderwidth=10)
    outer.pack(fill='both', expand=1)
    vbox1 = Tkinter.Frame(outer, borderwidth=5)
    vbox2 = Tkinter.Frame(outer, borderwidth=5)
    table = ([Tkinter.Frame(vbox1, borderwidth=5) for i in xrange(4)] +
             [Tkinter.Frame(vbox2, borderwidth=5) for i in xrange(4)])
    for tb in table:
        tb.grid(sticky='news')
    if landscape:
        label = Tkinter.Label(vbox2)
        vbox1.grid(row=0, sticky='news')
        vbox2.grid(row=0, column=1, sticky='news')
        label.grid(row=4)
    else:
        label = Tkinter.Label(outer)
        vbox1.grid(row=0, sticky='news')
        vbox2.grid(row=1, sticky='news')
        label.grid(row=2)

    # Text entry
    Tkinter.Label(table[6], text='Text:').grid(column=0, row=0)
    Tkinter.Label(table[6], text='Cols:').grid(column=0, row=1)

    key_text = Tkinter.Entry(table[6], width=15)
    key_text.bind('<Return>', keyboard)
    key_text.bind('<Escape>', lambda w: label.focus_set())
    key_text.grid(column=1, row=0, columnspan=2, sticky='news')

    key_width = Tkinter.Spinbox(table[6], from_=0, to=9, width=2)
    key_width.delete(0, 'end')
    key_width.insert(0, '4')
    key_width.grid(column=1, row=1, sticky='news')

    # Keyboard shortcuts
    for each in KEYS:
        make_tk_key(each, KEYS[each])

    label.bind('c', closed_caption)
    label.bind('q', go_away)
    label.focus_set()

for i, button_group in enumerate(BUTTONS):
    for each in button_group:
        make_ircode(table[i], *each)

make_button(table[2], 0, 1, 'CC', closed_caption)
make_button(table[2], 0, 0, 'SPS30', sps30)
make_button(table[2], 1, 0, 'Clock', sps9)
make_button(table[6], 1, 2, 'Kbd', keyboard)
make_ircode(table[7], 0, 0, 'Standby', 'STANDBY', 2)
make_button(table[7], 0, 2, 'Quit', go_away)

if not use_gtk:
    for w in table + [vbox1, vbox2, outer]:
        make_widget_expandable(w)

thread.start_new_thread(status_update, ())

if use_gtk:
    window.show_all()
    focus_button.grab_focus()
    gtk.main()
else:
    window.mainloop()
