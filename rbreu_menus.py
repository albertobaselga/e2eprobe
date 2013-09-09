#! /usr/bin/env python

import urwid.curses_display
import urwid
import sys


#If the alt key doesn't work:
#
#When the alt key is pressed, some terminals send <character code + 128>
#instead of prefixing the character with esc. Unfortunately, this conflicts
#with the use of 8 bit encodings that send characters in the range 128-255
#(used by ISO-8859-*, EUC-*, and other encodings).
#
#In xterm you can toggle the behavior with the "Meta Sends Escape" in
#ctrl+left-click menu, or by adding
#XTerm*metaSendsEscape: true
#to your .Xdefaults file.
#
#If you pass all keypresses that might contain alt key combinations to
#the following function (see the main event loop below), the alt key should
#work, but note that this will disable the input of 8-bit-characters.


#def filter_8bit_meta(k):
#    """Get Alt+<key> working."""
#    if urwid.is_mouse_event(k) or len(k) > 1:
#        return k
#    if ord(k)>=ord('a')+128 and ord(k)<=ord('z')+128:
#        return "meta " + chr(ord(k)-128)
#    return k



######################################################################
class SelText(urwid.Text):
    """
    A selectable text widget. See urwid.Text.
    """

    def selectable(self):
        return True

    def keypress(self, size, key):
        """
        Don't handle any keys.
        """
        return key


######################################################################
class Menu(urwid.WidgetWrap):
    """
    Creates a popup menu on top of another BoxWidget.

    Attributes:

    selected -- Contains the item the user has selected by pressing <RETURN>,
                or None if nothing has been selected.
    """

    selected = None
    
    def __init__(self, menu_list, attr, pos, body):
        """
        menu_list -- a list of strings with the menu entries
        attr -- a tuple (background, active_item) of attributes
        pos -- a tuple (x, y), position of the menu widget
        body -- widget displayed beneath the message widget
        """
        
        content = [urwid.AttrWrap(SelText(" " + w), None, attr[1])
                   for w in menu_list]

        #Calculate width and height of the menu widget:
        height = len(menu_list)
        width = 0
        for entry in menu_list:
            if len(entry) > width:
                width = len(entry)

        #Create the ListBox widget and put it on top of body:
        self._listbox = urwid.AttrWrap(urwid.ListBox(content), attr[0])
        overlay = urwid.Overlay(self._listbox, body, ('fixed left', pos[0]),
                                width + 2, ('fixed top', pos[1]), height)

        urwid.WidgetWrap.__init__(self, overlay)


    def keypress(self, size, key):
        """
        <RETURN> key selects an item, other keys will be passed to
        the ListBox widget.
        """

        if key == "enter":
            (widget, foo) = self._listbox.get_focus()
            (text, foo) = widget.get_text()
            self.selected = text[1:] #Get rid of the leading space...
        else:
            return self._listbox.keypress(size, key)


######################################################################
def menubar():
    """
    Menu bar at the top of the screen
    """

    menu_text = [('menuh', " P"), ('menu', "rogram   "),
                 ('menuh', "F"), ('menu', "oo   "),
                 ('menuh', "B"), ('menu', "ar   ")]

    return urwid.AttrWrap(urwid.Text(menu_text), 'menu')


######################################################################
def statusbar():
    """
    Status bar at the bottom of the screen.
    """
    
    status_text = "Statusbar -- Press Alt + <key> for menu entries"
    return urwid.AttrWrap(urwid.Text(status_text), 'menu')


######################################################################
def body():
    """
    Body (main part) of the screen
    """

    main_text = """ Main view.
    
 (Alt Key doesn't work? If you use xterm, enable \"Meta Sends Escape\" in
 xterm's ctrl+left-click menu. For further information, see the source code.)
 """
    
    return urwid.AttrWrap(urwid.Filler(urwid.Text(main_text)), 'bg')


######################################################################
class Dialog(urwid.WidgetWrap):
    """
    Creates a BoxWidget that displays a message

    Attributes:

    b_pressed -- Contains the label of the last button pressed or None if no
                 button has been pressed.
    edit_text -- After a button is pressed, this contains the text the user
                 has entered in the edit field
    """
    
    b_pressed = None
    edit_text = None

    _blank = urwid.Text("")
    _edit_widget = None
    _mode = None

    def __init__(self, msg, buttons, attr, width, height, body, ):
        """
        msg -- content of the message widget, one of:
                   plain string -- string is displayed
                   (attr, markup2) -- markup2 is given attribute attr
                   [markupA, markupB, ... ] -- list items joined together
        buttons -- a list of strings with the button labels
        attr -- a tuple (background, button, active_button) of attributes
        width -- width of the message widget
        height -- height of the message widget
        body -- widget displayed beneath the message widget
        """

        #Text widget containing the message:
        msg_widget = urwid.Padding(urwid.Text(msg), 'center', width - 4)

        #GridFlow widget containing all the buttons:
        button_widgets = []

        for button in buttons:
            button_widgets.append(urwid.AttrWrap(
                urwid.Button(button, self._action), attr[1], attr[2]))

        button_grid = urwid.GridFlow(button_widgets, 12, 2, 1, 'center')

        #Combine message widget and button widget:
        widget_list = [msg_widget, self._blank, button_grid]
        self._combined = urwid.AttrWrap(urwid.Filler(
            urwid.Pile(widget_list, 2)), attr[0])
        
        #Place the dialog widget on top of body:
        overlay = urwid.Overlay(self._combined, body, 'center', width,
                                'middle', height)
       
        urwid.WidgetWrap.__init__(self, overlay)


    def _action(self, button):
        """
        Function called when a button is pressed.
        Should not be called manually.
        """
        
        self.b_pressed = button.get_label()
        if self._edit_widget:
            self.edit_text = self._edit_widget.get_edit_text()

            
######################################################################
def confirm_quit(ui, dim, display):
    """
    \"Really quit?\"-dialog.

    Return values:
    False: Don't quit
    True: Quit
    """
    
    confirm = Dialog("Really quit?", ["Yes", "No"],
                     ('menu', 'bg', 'bgf'), 30, 5, display)

    keys = True

    #Event loop:
    while True:
        if keys:
            ui.draw_screen(dim, confirm.render(dim, True))
            
        keys = ui.get_input()
        if "window resize" in keys:
            dim = ui.get_cols_rows()
        if "esc" in keys:
            return False
        for k in keys:
            confirm.keypress(dim, k)

        if confirm.b_pressed == "Yes":
            return True
        if confirm.b_pressed == "No":
            return False


######################################################################
def program_menu(ui, dim, display):
    """
    Program menu
    """
    
    program_menu = Menu(["Foo", "Bar", "Quit"],
                        ('menu', 'menuf'), (0, 1), display)

    keys = True
    
    #Event loop:
    while True:
        if keys:
            ui.draw_screen(dim, program_menu.render(dim, True))
            
        keys = ui.get_input()

        if "window resize" in keys:
            dim = ui.get_cols_rows()
        if "esc" in keys:
            return

        for k in keys:
            #Send key to underlying widget:
            program_menu.keypress(dim, k)

        if program_menu.selected == "Quit":
            if confirm_quit(ui, dim, display):
                sys.exit(0)
            else:
                return
        
        if program_menu.selected == "Foo":
            #Do something
            return

        if program_menu.selected == "Bar":
            #Do something
            return


######################################################################
def foo_menu(ui, dim, display):
    """
    Program menu
    """
    
    foo_menu = Menu(["Blah", "Foo", "Stuff"],
                    ('menu', 'menuf'), (10, 1), display)

    keys = True
    
    #Event loop:
    while True:
        if keys:
            ui.draw_screen(dim, foo_menu.render(dim, True))
            
        keys = ui.get_input()

        if "window resize" in keys:
            dim = ui.get_cols_rows()
        if "esc" in keys:
            return

        for k in keys:
            #Send key to underlying widget:
            foo_menu.keypress(dim, k)

        if foo_menu.selected == "Blah":
            #Do something
            return

        if foo_menu.selected == "Foo":
            #Do something
            return

        if foo_menu.selected == "Stuff":
            #Do something
            return


######################################################################
def bar_menu(ui, dim, display):
    """
    Program menu
    """
    
    bar_menu = Menu(["Blah", "Foo", "Stuff"],
                        ('menu', 'menuf'), (16, 1), display)

    keys = True
    
    #Event loop:
    while True:
        if keys:
            ui.draw_screen(dim, bar_menu.render(dim, True))
            
        keys = ui.get_input()

        if "window resize" in keys:
            dim = ui.get_cols_rows()
        if "esc" in keys:
            return

        for k in keys:
            #Send key to underlying widget:
            bar_menu.keypress(dim, k)

        if bar_menu.selected == "Blah":
            #Do something
            return

        if bar_menu.selected == "Foo":
            #Do something
            return

        if bar_menu.selected == "Stuff":
            #Do something
            return


######################################################################
def run():
    """
    Main part.
    """
  
    #Set up displayed stuff:
    dim = ui.get_cols_rows()
    main_view = body()
    display = urwid.Frame(main_view, menubar(), statusbar())

        
    keys = True

    #Main event loop:
    while True:
        if keys:
            #Redraw screen after user input:
            display = urwid.Frame(main_view, menubar(), statusbar())
            ui.draw_screen(dim, display.render(dim, True))
        
        keys = ui.get_input()

        #Uncomment the following line and the corresponding function at the
        #top if you want to "fix" problems with Alt+<key>:
        #keys = [filter_8bit_meta(k) for k in keys]
            
        if "window resize" in keys:
            dim = ui.get_cols_rows()

        if "meta P" in keys or "meta p" in keys:
            #Show program menu:
            program_menu(ui, dim, display)

        if "meta F" in keys or "meta f" in keys:
            #Show foo menu:
            foo_menu(ui, dim, display)

        if "meta B" in keys or "meta b" in keys:
            #Show bar menu:
            bar_menu(ui, dim, display)

 
######################################################################
#Entry point. Perform some initialisation:                           #
######################################################################

#init screen:
ui = urwid.curses_display.Screen()
ui.register_palette(
    [('menu', 'black', 'dark cyan', 'standout'),
     ('menuh', 'yellow', 'dark cyan', ('standout', 'bold')),
     ('menuf', 'black', 'light gray'),
     ('bg', 'light gray', 'dark blue'),
     ('bgf', 'black', 'light gray', 'standout')])

#start main part:
ui.run_wrapper(run)
