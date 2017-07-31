#!/usr/bin/env python3.4

'''
Example ioc
'''

from pcaspy import Driver, SimpleServer, Severity

prefix = 'EX:'
pvdb = {
		'STATUS_INT' :{
			'type' : 'int',
			'value': 0,
			'scan' : 1
			},
		'STATUS_ENUM' : {
			'type' : 'enum',
			'scan' : 1,
			'enums':  ['OK', 'ERROR', 'WARNING'],
    		'states': [Severity.NO_ALARM, Severity.MAJOR_ALARM, Severity.MINOR_ALARM]
			}
		}

class myDriver(Driver):
	def __init__(self):
		super(myDriver, self).__init__()

	def read(self, reason):
		value = int(self.getParam(reason))

		if reason == 'STATUS_INT':
			if value == 2:
				value = 0
			else:
				value = value + 1
			self.setParam('STATUS_INT', value)

		elif reason == 'STATUS_ENUM':
			if value == 2:
				value = 0
			else:
				value = value + 1
			self.setParam('STATUS_ENUM', value)

		return value
            
if __name__ == '__main__':
	server = SimpleServer()
	server.createPV(prefix, pvdb)
	driver = myDriver()

	# process CA transactions
	print("Server is running... (ctrl+c to close)")
	print("\nAvailable PVs:")
	print("EX:STATUS_INT")
	print("EX:STATUS_ENUM")
	while True:
		server.process(0.1)