# run python setup.py py2exe to build executable version

# setup(windows=['CUCM-GUI.py'])

from distutils.core import setup
import py2exe
import os, sys

# Find GTK+ installation path
__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]

setup(
    name = 'CUCM-GUI',
    description = 'GUI to CUCM',
    version = '1.1',

    windows = [
                  {
                      'script': 'CUCM-GUI.py',
                      #'icon_resources': [(1, "handytool.ico")],
                  }
              ],

    options = {
                  'py2exe': {
                      'packages':'encodings',
                      # Optionally omit gio, gtk.keysyms, and/or rsvg if you're not using them
                      'includes': 'cairo, pango, pangocairo, atk, gobject, gio, gtk.keysyms, rsvg, sqlite3.dump',
                  }
              },

    data_files=[
                   'CUCM.glade',
                   #'readme.txt',
                   # If using GTK+'s built in SVG support, uncomment these
                   #os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'gdk-pixbuf-query-loaders.exe'),
                   #os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'libxml2-2.dll'),
               ]
)