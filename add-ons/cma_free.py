#!/usr/bin/python

import gdb

MAX_ORDER = 11
NR_FREE_CMA_PAGES = int(gdb.parse_and_eval("NR_FREE_CMA_PAGES"))
NR_FREE_PAGES = int(gdb.parse_and_eval("NR_FREE_PAGES"))

def print_zone(num):
	print str(gdb.parse_and_eval("contig_page_data->node_zones[" + str(num) + "]->name"))
	print "NR_FREE_CMA_PAGES = " + str(gdb.parse_and_eval("contig_page_data->node_zones[" + str(num) + "]->vm_stat[" + str(NR_FREE_CMA_PAGES) + "]"))
	count = 0
	print "cma_nr_free"
	for i in range(0, MAX_ORDER):
		page = int(gdb.parse_and_eval("contig_page_data->node_zones[" + str(num) + "]->free_area[" + str(i) + "].cma_nr_free"))
		print i, page, page << i
		count += page << i
	print count
	print ""
	print "NR_FREE_PAGES = " + str(gdb.parse_and_eval("contig_page_data->node_zones[" + str(num) + "]->vm_stat[" + str(NR_FREE_PAGES) + "]"))
	count = 0
	print "nr_free"
	for i in range(0, MAX_ORDER):
		page = int(gdb.parse_and_eval("contig_page_data->node_zones[" + str(num) + "]->free_area[" + str(i) + "].nr_free"))
		print i, page, page << i
		count += page << i
	print count
	print ""

print_zone(0)
print_zone(1)
