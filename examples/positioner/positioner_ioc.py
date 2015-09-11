from pcaspy import SimpleServer, Driver
import time

prefix = 'MOTOR:'
pvdb = {
	'1:VAL': {
		'val': 0.0,
		'prec': 2,
		'hihi' : 180,
		'high' : 170,
		'low'  : -170,
		'lolo' : -180
	},
	'2:VAL': {
		'val': 0.0,
		'prec': 2,
		'hihi' : 180,
		'high' : 170,
		'low'  : -170,
		'lolo' : -180
	},
	'3:VAL': {
		'val': 0.0,
		'prec': 2,
		'hihi' : 180,
		'high' : 170,
		'low'  : -170,
		'lolo' : -180
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