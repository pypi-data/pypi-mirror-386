# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class Yes(ValueProducer):
    """returns True"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    yes() always evaluates to True. It is similar to no() and none().
            """
            ),
        ]

        self.aliases = ["yes", "true"]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = True
