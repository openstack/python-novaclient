
from novaclient.v1_1 import limits
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class LimitsTest(utils.TestCase):

    def test_get_limits(self):
        obj = cs.limits.get()
        cs.assert_called('GET', '/limits')
        self.assertTrue(isinstance(obj, limits.Limits))

    def test_absolute_limits(self):
        obj = cs.limits.get()

        expected = (
            limits.AbsoluteLimit("maxTotalRAMSize", 51200),
            limits.AbsoluteLimit("maxServerMeta", 5),
            limits.AbsoluteLimit("maxImageMeta", 5),
            limits.AbsoluteLimit("maxPersonality", 5),
            limits.AbsoluteLimit("maxPersonalitySize", 10240),
        )

        abs_limits = list(obj.absolute)
        self.assertEqual(len(abs_limits), len(expected))

        for limit in abs_limits:
            self.assertTrue(limit in expected)

    def test_rate_limits(self):
        obj = cs.limits.get()

        expected = (
            limits.RateLimit('POST', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('PUT', '*', '.*', 10, 2, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('DELETE', '*', '.*', 100, 100, 'MINUTE',
                             '2011-12-15T22:42:45Z'),
            limits.RateLimit('POST', '*/servers', '^/servers', 25, 24, 'DAY',
                             '2011-12-15T22:42:45Z'),
        )

        rate_limits = list(obj.rate)
        self.assertEqual(len(rate_limits), len(expected))

        for limit in rate_limits:
            self.assertTrue(limit in expected)
