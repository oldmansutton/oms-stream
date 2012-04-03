#!/usr/bin/env python

import sys

import pygst
pygst.require("0.10")
import gst

import dbus
from dbus.mainloop.glib import DBusGMainLoop

try:
	import pygtk
	pygtk.require("2.24")
except:
	pass
try:
	import gtk
	import gtk.glade
except:
	sys.exit(1)

#
#  Global variables
#

global root, player, tracklist
global playing
global track, artist
global bus
global connected

#
#  Helper Functions
#

# Update song metadata when track changes
def TrackChange(Track):
	# the only mandatory metadata is "URI"
	global track, artist
	try:
		artist = Track["artist"]
	except:
		artist = "Unknown Artist"
	try:
		track = Track["title"]
	except:
		track = Track["URI"]
	l_artist.set_text(artist)
	l_title.set_text(track)

# Connect to Clementine
def Connect():
	global root, player, tracklist
	global playing
	global connected
	# Define clementine related variables
	clemname = 'org.mpris.clementine'
	mpris = 'org.freedesktop.MediaPlayer'
	# Take the bus to Clementine-Town
	root_o = bus.get_object(clemname, "/")
	player_o = bus.get_object(clemname, "/Player")
	tracklist_o = bus.get_object(clemname, "/TrackList")
	# Define interfaces to their respective objects
	root = dbus.Interface(root_o, mpris)
	player = dbus.Interface(player_o, mpris)
	tracklist = dbus.Interface(tracklist_o, mpris)
	# Listen for track change signals
	player_o.connect_to_signal("TrackChange", TrackChange, dbus_interface=mpris)
	# See if the player is currently playing
	playstatus = player.GetStatus()
	if playstatus[0] == 0:
		playing = True
		TrackChange(player.GetMetadata())
	# Update Connected state
	connected = True

#
#  Widget Callbacks
#

def clickConnect(widget):
	global connected
	if connected == False:
		try:
			Connect()
			widget.hide()
		except:
			connected = False
			widget.set_active(False)

# Widget Callback -- Destroy 
def destroy(widget):
    gtk.main_quit()

#
#  Window definitions
#

# Load Glade GUI XML
gladeXML = gtk.glade.XML("gui-oms-stream.glade")
window 		= gladeXML.get_widget('window1')
bt_connect 	= gladeXML.get_widget('togglebutton1')
l_artist 	= gladeXML.get_widget('label1')	
l_title		= gladeXML.get_widget('label2')
# Set default labels
l_artist.set_text("")
l_title.set_text("")
# Connect Window event handlers to widgets
window.connect('destroy', 		destroy)
bt_connect.connect('clicked', 	clickConnect)

#
#  D-bus connection
#

# Get on the bus
DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
connected = False
playing = False

####  MAIN LOOP ####
gtk.main() 
