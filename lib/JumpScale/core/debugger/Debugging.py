from JumpScale import j

class Debugging:
    """JumpScale debugging tools"""

    def printTraceBack(self, message='No error message supplied'):
        j.logger.exception(message, 1)
        import traceback
        import sys
        traceback.print_exc(file=sys.stdout)

    def testPrintTraceBack(self):
        try:
            t = 1/0
        except:
            self.printTraceBack('Got Exception')
