# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Put(ValueProducer):
    """Sets a variable with or without a tracking value"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Sets a variable tracking value.

                    A tracking value is similar to a dictionary key. It usually keys a
                    count, calculation, or transformation.

                    While get() and put() make it possible to create and use tracking-value
                    variables in an ad hoc dict-like way, this is not recommended unless there
                    is no simplier solution based on more specific functions.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="var name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="var value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, bool, tuple],
        )
        a = self.args.argset(3)
        a.arg(
            name="var name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="tracking key",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="tracking value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, bool, tuple],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        varname = None
        c1 = self._child_one()
        varname = c1.to_value(skip=skip)
        c2 = self._child_two()
        key = c2.to_value(skip=skip)
        value = None
        if len(self.children[0].children) > 2:
            value = self.children[0].children[2].to_value(skip=skip)
        else:
            value = key
            key = None
        self.matcher.set_variable(varname, value=value, tracking=key)
        self.value = self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
