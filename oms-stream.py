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
global taginject

#
#  Helper Functions
#

# Update song metadata when track changes
def TrackChange(Track):
	# Parse necessary metadata
	global track, artist
	global taginject
	try:
		artist = Track["artist"]
	except:
		artist = "Unknown Artist"
	try:
		track = Track["title"]
	except:
		track = Track["URI"]
	# Update GUI with artist and track name
	taginject.set_property("tags","title=" + track + ",artist=" + artist)
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
		# Update track information
		TrackChange(player.GetMetadata())
	# Update Connected state
	connected = True

#
#  Widget Callbacks
#

# Widget Callback -- Connect toggle button clicked
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

#
#  GStreamer initialization
#

# New GStreamer Pipeline
pipeline = gst.Pipeline("gstpipe")

# Our source is pulse audio
pulsesrc = gst.element_factory_make("pulsesrc", "pulse")
pulsesrc.set_property("device","alsa_input.pci-0000_00_06.0.analog-stereo") # Audio input
pipeline.add(pulsesrc)

# Convert audio module
audioconvert = gst.element_factory_make("audioconvert", "ac")
pipeline.add(audioconvert)

# Inject tags onto the stream
taginject = gst.element_factory_make("taginject", "ti")
taginject.set_property("tags","ARTIST=Test,TITLE=Also Test")
pipeline.add(taginject)

# Encode the stream as vorbis
vorbisenc = gst.element_factory_make("vorbisenc", "venc")
pipeline.add(vorbisenc)

# mux the stream to .ogg format
oggmux = gst.element_factory_make("oggmux", "omux")
pipeline.add(oggmux)

# Sink is icecast 
shout2send = gst.element_factory_make("shout2send", "s2s")
shout2send.set_property("mount","/omsradio.ogg")
shout2send.set_property("port",8000)
shout2send.set_property("password","hackme")
shout2send.set_property("ip","localhost")
shout2send.set_property("streamname","OMS Radio")
shout2send.set_property("genre","Eclectic")
shout2send.set_property("description","Eclectic blend of musical goodness")
pipeline.add(shout2send);
gst.element_link_many(pulsesrc,audioconvert,taginject,vorbisenc,oggmux,shout2send)
pipeline.set_state(gst.STATE_PLAYING)

#                  #
####  MAIN LOOP ####
#                  #

gtk.main() 
