# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import sys
import os.path as pth
import tempfile
from .runner import runScript, runAreaScript, runVectorScript, stipple
from collections import namedtuple

class CaptureStream:
    """
    ref: https://stackoverflow.com/a/57677370
    """
    def __init__(self, inp_stream=sys.stdout,
                 out_stream=open(os.devnull, 'w')):
        if inp_stream is sys.stdin:
            self.orig_stream_fileno = 0
        elif inp_stream is sys.stdout:
            self.orig_stream_fileno = 1
        elif inp_stream is sys.stderr:
            self.orig_stream_fileno = 2
        if out_stream is None:
            stream_file = pth.join(tempfile.gettempdir(),
                                   f"{os.urandom(3).hex()}.txt")
            if not pth.exists(stream_file):
                with open(stream_file, 'w'):
                    pass
            self.capture_stream = open(stream_file, "r+")
        else:
            self.capture_stream = out_stream

    def __enter__(self):
        self.open()

    def __exit__(self, type, value, traceback):
        self.close(type, value, traceback)

    def open(self):
        self.orig_stream_dup = os.dup(self.orig_stream_fileno)
        self.devnull = self.capture_stream
        os.dup2(self.devnull.fileno(), self.orig_stream_fileno)

    def close(self, *args):
        os.close(self.orig_stream_fileno)
        os.dup2(self.orig_stream_dup, self.orig_stream_fileno)
        os.close(self.orig_stream_dup)
        if not self.devnull.closed:
            self.devnull.close()
        if pth.exists(self.devnull.name):
            os.remove(self.devnull.name)
