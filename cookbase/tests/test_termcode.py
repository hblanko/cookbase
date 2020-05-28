import random
import string
import unittest

from cookbase.parsers import termcode


class Test(unittest.TestCase):
    """Test class for the :mod:`cookbase.parsers.termcode` module.

    """

    def test_termcode(self):
        """Tests the :meth:`cookbase.parsers.termcode.to_int` and
        :meth:`cookbase.parsers.termcode.to_str` methods.
        """
        for _ in range(10000):
            code = ""

            for _ in range(5):
                a = random.randint(0, 1)
                if not a:
                    code += random.choice(string.digits)
                else:
                    code += random.choice(string.ascii_letters)

            n = termcode.to_int(code)
            self.assertEqual(code.upper(), termcode.to_str(n))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
