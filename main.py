#!/usr/bin/env python3
import time
from RadioSaver import RadioSaver

saver = RadioSaver()

while True:
    saver.process_music()
    time.sleep(180)
