#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, inspect, os
sys.path.append(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
import kgtp_setup

kgtp_setup.main(sys.argv)