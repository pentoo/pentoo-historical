#!/usr/bin/python

import sys
sys.path.append("..")
import GLIStorageDevice

if len(sys.argv) <= 1:
	print "You must call this script with a device name"
	sys.exit(1)

device = GLIStorageDevice.Device(sys.argv[1])
device.set_partitions_from_disk()
print "Device: " + sys.argv[1]
print "Disklabel: " + device.get_disklabel()
print "Length (MB): " + str(device.get_total_mb())
print "Length (sectors): " + str(device.get_num_sectors())
for partition in device.get_ordered_partition_list():
	print str(partition)
	print repr(device)
	print str(device[partition])
	partition = device[partition]
	print "--------------------"
	print "Minor: " + str(partition.get_minor())
	print "Type: " + str(partition.get_type())
	try:
		print "Start: " + str(partition.get_start())
		print "End: " + str(partition.get_end())
	except:
		pass
