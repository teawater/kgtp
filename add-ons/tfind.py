#!/usr/bin/python

import gdb
#import re

#gdb.execute("tfind -1", False, True)
#cpu_number = int(gdb.parse_and_eval("$cpu_number"))
#str(gdb.execute("p $rip", False, True))

#frame_count = gdb.execute("tstatus", False, True)
#frame_count = re.findall("Collected \d+ trace frames", frame_count)
#frame_count = re.findall("\d+", frame_count[0])
#frame_count = int(frame_count[0])

gdb.execute("set pagination off", True, False)

#for i in range(frame_count - 1, -1, -1):
while True:
	gdb.execute("tfind", True, False)
	#print gdb.parse_and_eval("$trace_frame")
	if long(gdb.parse_and_eval("work")) == 0x0:
		break

