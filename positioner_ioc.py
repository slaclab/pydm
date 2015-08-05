from pcaspy import SimpleServer, Driver

prefix = 'MOTOR:'
pvdb = {
	'1:VAL': {
		'prec': 2
	},
	'2:VAL': {
		'prec': 2
	},
	'3:VAL': {
		'prec': 2
	}
}

class myDriver(Driver):
	def __init__(self):
		super(myDriver, self).__init__()
	
if __name__ == '__main__':
	server = SimpleServer()
	server.createPV(prefix, pvdb)
	driver = myDriver()
	print "Server is running... (ctrl+c to close)"
	while True:
		server.process(0.1)