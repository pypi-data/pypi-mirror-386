# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Concat(ValueProducer):
    """concats two strings"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
               Concatenates any number of strings, numbers, or bool values.
        """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, float, bool, self.args.EMPTY_STRING],
        )
        a.arg(
            name="append this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, float, bool, self.args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        v = ""
        for s in siblings:
            v = f"{v}{s.to_value(skip=skip)}"
        self.value = v

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
