# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Matchable
from ..function import Function
from ..args import Args


class Every(ValueProducer):
    """selects every N sightings of a
    value. results in a list of counts of values (potentially
    quite expensive) behind the scenes for generating the %.
    since there isn't an intrinsic state we're exposing and the
    values generated are useful, this is a ValueProducer.
    """

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                Matches every N times a value is seen.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="watch", types=[Matchable], actuals=[None, Any])
        a.arg(name="pick every N", types=[Term], actuals=[int, float])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        tracked_value = child.left.to_value(skip=skip)
        cnt = self.matcher.get_variable(
            self.me(), tracking=tracked_value, set_if_none=0
        )
        cnt += 1
        self.matcher.set_variable(self.me(), tracking=tracked_value, value=cnt)
        #
        # any conversion error will be caught by Args
        #
        every = child.right.to_value(skip=skip)
        i = ExpressionUtility.to_int(every)
        self.value = cnt % i

    def _decide_match(self, skip=None) -> None:
        cnt = self.to_value(skip=skip)
        if self.nocontrib:
            self.match = self.default_match()
        elif cnt == 0:
            self.match = True
        else:
            self.match = False

    def me(self):
        return self.first_non_term_qualifier(self.get_id(self))
