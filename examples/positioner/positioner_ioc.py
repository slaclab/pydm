from pcaspy import SimpleServer, Driver
import time

prefix = 'MOTOR:'
pvdb = {
	'1:VAL': {
		'val': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
	},
	'2:VAL': {
		'val': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
	},
	'3:VAL': {
		'val': 0.0,
		'prec': 2,
    'hilim' : 180,
		'hihi' : 140,
		'high' : 100,
		'low'  : -100,
		'lolo' : -140,
    'lolim' : -180,
    'unit' : 'deg'
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