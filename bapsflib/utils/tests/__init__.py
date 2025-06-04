import unittest as ut

from typing import Callable, Union


class BaPSFTestCase(ut.TestCase):
    def assert_runner(
        self,
        _assert: Union[str, Callable],
        attr: Callable,
        args: tuple,
        kwargs: dict,
        expected,
    ):
        with self.subTest(
            test_attr=attr.__name__,
            args=args,
            kwargs=kwargs,
            expected=expected,
        ):
            if isinstance(_assert, str) and hasattr(self, _assert):
                _assert = getattr(self, _assert)
            elif isinstance(_assert, str):
                self.fail(
                    f"The given assert name '{_assert}' does NOT match an "
                    f"assert method on self."
                )

            if _assert == self.assertRaises:
                with self.assertRaises(expected):
                    attr(*args, **kwargs)
            else:
                _assert(attr(*args, **kwargs), expected)
