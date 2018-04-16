#!/usr/bin/env python

from keyboard.layoutengine import KeyboardLayoutEngine

kle=KeyboardLayoutEngine()
kle.load_from_file('iso tkl.json')
kle.layout_switches()
