def remove_protocol(addr):
	try:
		name = addr.split("://")[1]
	except IndexError:
		name = addr
	return name