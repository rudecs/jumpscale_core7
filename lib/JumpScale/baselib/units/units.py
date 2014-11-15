order = ['','K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']

class Sizes(object):
    _BASE = 1000.

    def toSize(self, value, input='', output='K'):
        """
        Convert value in other measurement
        """
        input = order.index(input)
        output = order.index(output)
        factor = input - output
        return value * (self._BASE ** factor)

    def converToBestUnit(self, value, input=''):
        devider = len(str(int(self._BASE))) - 1
        output = (len(str(value)) -2) / devider
        output += order.index(input)
        if output > len(order):
            output = len(order) - 1
        elif output < 0:
            output = 0
        output = order[output]
        return self.toSize(value, input, output), output

class Bytes(Sizes):
    _BASE = 1024.
