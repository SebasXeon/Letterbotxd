#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------------
# Import modules
# ---------------------------
#from bot.config import Settings
#from bot import versus as vs
#from bot import tournament as tr
#from bot import versus_video as vs_video
from bot import post as lb_post

import typer
import json

# ---------------------------
# setup
# ---------------------------
app = typer.Typer()


# ---------------------------
# Commands
# ---------------------------
@app.command()
def post():
    lb_post.post()

# ---------------------------
# run
# ---------------------------

if __name__ == "__main__":
    app()