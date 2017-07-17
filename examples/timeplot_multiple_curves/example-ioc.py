#!/usr/bin/env python3.4

'''
Example ioc
'''

PREC = 2
STRING_FORMAT = '% .'+str(PREC)+'f'

from pcaspy import Driver, SimpleServer

prefix = 'EX:'
pvdb = {
		'FUNC1' :
			{
			'value': 0.0,
			'scan' : 1,
			'hilim' : 9,
			'hihi' : 8,
			'high' : 7,
			'low'  : 3,
			'lolo' : 1,
			'lolim' : 0,
			},
		'FUNC2' :
			{
			'value': 10.0,
			'scan' : 0.5,
			'hilim' : 9,
			'hihi' : 8,
			'high' : 7,
			'low'  : 3,
			'lolo' : 1,
			'lolim' : 0,
			}
		}

class myDriver(Driver):
	def __init__(self):
		super(myDriver, self).__init__()

	def read(self, reason):
		value = self.getParam(reason)

		if reason == 'FUNC1':
			if value == 9:
				value = 0
			else:
				value = value + 1
			self.setParam('FUNC1', value)

		elif reason == 'FUNC2':
			if value == 19:
				value = 10
			else:
				value = value + 1
			self.setParam('FUNC2', value)

		return value
            
if __name__ == '__main__':
	server = SimpleServer()
	server.createPV(prefix, pvdb)
	driver = myDriver()

	# process CA transactions
	print("Server is running... (ctrl+c to close)")
	print("\nAvailable PVs:")
	print("EX:FUNC1")
	print("EX:FUNC2")
	while True:
		server.process(0.1)