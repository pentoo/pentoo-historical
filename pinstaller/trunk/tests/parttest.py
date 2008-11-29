#!/usr/bin/python

import parted, sys

if len(sys.argv) <= 1:
	print "You must call this script with a device name"
	sys.exit(1)

parted_dev = parted.PedDevice.get(sys.argv[1])
parted_disk = parted.PedDisk.new(parted_dev)
print "Device: " + sys.argv[1]
print "Disklabel: " + parted_disk.type.name
print "Length (sectors): " + str(parted_dev.length)
partition = parted_disk.next_partition()
while partition:
	print "--------------------"
	print "Minor: " + str(partition.num)
	print "Type: " + str(partition.type)
	print "Type name: " + partition.type_name
	try:
		print "Start: " + str(partition.geom.start)
		print "End: " + str(partition.geom.end)
		print "FS type: " + partition.fs_type.name
		print "Name: " + partition.get_name()
	except:
		pass
	if partition.num > 0:
		print "Flags:"
		for flag in range(1, 10):
			if partition.is_flag_available(flag):
				if partition.get_flag(flag):
					print "\t" + str(flag) + " - ON"
				else:
					print "\t" + str(flag) + " - OFF"
			else:
				print "\t" + str(flag) + " - N/A"
#		print "System: " + str(partition.get_system())
	partition = parted_disk.next_partition(partition)
