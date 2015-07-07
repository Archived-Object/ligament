class TaskExecutionException(Exception):
	def __init__(self, header, *args):
		self.header = header
		Exception.__init__(self, *args)
