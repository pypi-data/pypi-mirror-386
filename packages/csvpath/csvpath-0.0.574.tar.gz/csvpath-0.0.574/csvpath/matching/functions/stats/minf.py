# pylint: disable=C0114
from typing import Any
from statistics import mean, median
from csvpath.matching.productions import Equality, Variable, Term, Header, Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class MinMax(ValueProducer):
    """base class for some of the math functions"""

    MAX = True
    MIN = False

    def _get_the_value(self) -> Any:
        if isinstance(self.children[0], Equality):
            return self.children[0].left.to_value()
        return self.children[0].to_value()

    def _get_the_value_conformed(self) -> Any:
        v = self._get_the_value()
        return ExpressionUtility.ascompariable(v)

    def _get_the_name(self) -> Any:
        if isinstance(self.children[0], Equality):
            return self.children[0].left.name
        return self.children[0].name

    def _get_the_line(self) -> int:
        if isinstance(self.children[0], Equality):
            v = self.children[0].right.to_value()
            v = f"{v}".strip()
            if v == "match":
                return self.matcher.csvpath.current_match_count
            if v == "scan":
                return self.matcher.csvpath.current_scan_count
            return self.matcher.csvpath.line_monitor.physical_line_number
        return self.matcher.csvpath.line_monitor.physical_line_number

    def is_match(self) -> bool:  # pylint: disable=C0116
        if self.onmatch:
            return True
        if isinstance(self.children[0], Equality):
            v = self.children[0].right.to_value()
            v = f"{v}".strip()
            return v == "match"
        return False

    def _ignore(self):
        if (
            self._get_the_name() in self.matcher.csvpath.headers
            and self.matcher.csvpath.line_monitor.physical_line_number == 0
        ):
            return True
        if self.is_match() and not self.line_matches():
            return True
        return False

    def _store_and_compare(self, v, maxormin: bool) -> Any:
        name = "min" if maxormin is MinMax.MIN else "max"
        #
        # track the val by line in func name
        #
        t = f"{self._get_the_line()}"
        self.matcher.set_variable("min", tracking=t, value=v)
        #
        # find the least/most
        #
        all_values = self.matcher.get_variable(name)
        m = None
        for k, val in enumerate(all_values.items()):
            val = val[1]
            if m is None or ((val < m) if maxormin is MinMax.MIN else (val > m)):
                m = val
        return m


# ===========================


class Average(MinMax):
    """returns the running average"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                f"""\
                Tracks the {self.ave_or_med} from the first physical line, scanned line, or match to
                the current line.

                The optional second argument is one of 'scan', 'match', or 'line'. It
                limits which lines will be compared.
            """
            ),
        ]

        self.description = [
            f"{self.name}() returns the running  from the first to the current line"
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="value to average",
            types=[Variable, Term, Header, Function],
            actuals=[int, float],
        )
        a.arg(
            name="match, scan, or line",
            types=[None, Variable, Term, Header, Function],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def __init__(
        self, matcher: Any, name: str, child: Matchable = None, ave_or_med="average"
    ) -> None:
        super().__init__(matcher, name, child)
        self.ave_or_med = ave_or_med

    def _produce_value(self, skip=None) -> None:
        v = self._get_the_value()
        # if we're watching a header and we're in the header row skip it.
        if (
            self._get_the_name() in self.matcher.csvpath.headers
            and self.matcher.csvpath.line_monitor.physical_line_number == 0
        ):
            return
        # if the line must match and it doesn't stop here and return
        if self.is_match() and not self.line_matches():
            return
        n = self.first_non_term_qualifier(self.ave_or_med)
        # set the "average" or "median" variable tracking the value by line, scan, or match count
        self.matcher.set_variable(n, tracking=f"{self._get_the_line()}", value=v)
        # get value for all the line counts
        all_values = self.matcher.get_variable(n)
        m = []
        for k, v in enumerate(all_values.items()):  # pylint: disable=W0612
            # re: W0612: can be changed, but not now
            v = v[1]
            try:
                v = float(v)
                m.append(v)
            except (ValueError, TypeError):
                pass
            if self.ave_or_med == "average":
                self.value = mean(m)
            else:
                self.value = median(m)

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_value()


class Median(Average):
    def __init__(self, matcher, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name, child, "median")
