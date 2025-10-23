import json

class Handler:

	def __init__(self, compiler):
		self.compiler = compiler
		self.program = compiler.program
		self.getToken = compiler.getToken
		self.nextToken = compiler.nextToken
		self.skip = compiler.skip
		self.peek = compiler.peek
		self.getValue = compiler.getValue
		self.nextValue = compiler.nextValue
		self.getConstant = compiler.getConstant
		self.getCondition = compiler.getCondition
		self.nextCondition = compiler.nextCondition
		self.tokenIs = compiler.tokenIs
		self.nextIs = compiler.nextIs
		self.isSymbol = compiler.isSymbol
		self.nextIsSymbol = compiler.nextIsSymbol
		self.getSymbolRecord = compiler.getSymbolRecord
		self.compileVariable = compiler.compileVariable
		self.rewindTo = compiler.rewindTo
		self.warning = compiler.warning
		self.getPC = compiler.getPC
		self.add = compiler.add
		self.getCommandAt = compiler.getCommandAt
		self.compileOne = compiler.compileOne
		self.compileFromHere = compiler.compileFromHere
		self.compileConstant = compiler.compileConstant

		self.code = self.program.code
		self.evaluate = self.program.evaluate
		self.getVariable = self.program.getSymbolRecord
		self.getRuntimeValue = self.program.getRuntimeValue
		self.testCondition = self.program.condition.testCondition
		self.symbols = self.program.symbols
		self.stack = self.program.stack
		self.getSymbolContent = self.program.getSymbolContent
		self.getSymbolValue = self.program.getSymbolValue
		self.putSymbolValue = self.program.putSymbolValue
		self.run = self.program.run

		self.nonNumericValueError = self.program.nonNumericValueError
		self.variableDoesNotHoldAValueError = self.program.variableDoesNotHoldAValueError
		self.noneValueError = self.program.noneValueError

	def nextPC(self):
		return self.program.pc + 1

	# Get a compile handler (raises an Exception if none)
	def keywordHandler(self, name):
		if hasattr(self, f'k_{name}'):
			return getattr(self, f'k_{name}')
		return None

	# Get a run handler
	def runHandler(self, name):
		return getattr(self, f'r_{name}')

	# Get a value handler
	def valueHandler(self, name):
		return getattr(self, f'v_{name}')

	# Get a condition handler
	def conditionHandler(self, name):
		return getattr(self, f'c_{name}')

	def isJson(value):
		try:
			json.loads(value)
		except ValueError as e:
			return False
		return True
