#!/usr/bin/env python3

from zOS import zOS

zSpark = {
    "deployment": "Production",
    "logger": "PROD",
    "zMode": "Terminal",  # Use Terminal mode for testing
    "app_storage": True,
    "zVaFolder": "@",
    "zVaFile": "zUI.lists",
    "zBlock": "Lists_block",
}
# Initialize zOS and run init sequence
z = zOS(zSpark)
z.run()
