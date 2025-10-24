# pylint: disable=C0114
import hashlib
from typing import Any
from csvpath.matching.productions import Header, Variable, Equality
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider, ValueProducer
from ..args import Args


#
# count dups produces a number of dups
# dup_lines produces a stack of line numbers
# has_dups decides match based on dups > 1
# all use fingerprinter to do the work
#
class CountDups(ValueProducer):
    """returns a count of duplicates."""

    def check_valid(self) -> None:
        self.name_qualifier = True
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Produces the number of duplicate lines or the number of
                    lines where there are duplicate subsets of header values.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset().arg(
            name="check this", types=[None, Header], actuals=[None, Any]
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        if self.name == "count_dups":
            self.match = self.default_match()
        elif self.name == "has_dups":
            self.match == self.get_value(skip=skip) > 1

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        self.value = len(lines)


class HasDups(MatchDecider):
    """returns True if there are duplicates."""

    def check_valid(self) -> None:
        self.name_qualifier = True
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Evaluates to True if there are duplicate lines or duplicate
                    subsets of header values.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset().arg(name="check", types=[None, Header], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        self.match = len(lines) > 1

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)


class DupLines(ValueProducer):
    """returns a list of duplicate lines seen so far."""

    def check_valid(self) -> None:
        self.name_qualifier = True
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                dups_lines() returns a list of the numbers of duplicate lines or lines
                with duplicate subsets of header values.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset().arg(name="check", types=[None, Header], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        lines = lines[:]
        if len(lines) == 1:
            self.value = []
        else:
            self.value = lines

    def _decide_match(self, skip=None) -> None:
        self.match = len(self.to_value(skip=skip)) > 0


class FingerPrinter:
    @classmethod
    def _capture_line(
        cls, mc, name: str, skip=None, sibs=None
    ) -> tuple[str, list[int]]:
        values = mc.matcher.get_variable(name, set_if_none={})
        fingerprint = FingerPrinter._fingerprint(mc, skip=skip, sibs=sibs)
        if fingerprint not in values:
            values[fingerprint] = []
        pln = mc.matcher.csvpath.line_monitor.physical_line_number
        if pln not in values[fingerprint]:
            values[fingerprint].append(pln)
        mc.matcher.set_variable(name, value=values)
        return (fingerprint, values[fingerprint])

    @classmethod
    def _fingerprint(cls, mc, skip=None, sibs=None) -> str:
        if sibs and len(sibs) > 0:
            fingerprint = FingerPrinter._fingerprint_for_children(sibs, skip=skip)
        elif len(mc.children) == 1:
            if isinstance(mc.children[0], Equality):
                siblings = mc.children[0].commas_to_list()
                fingerprint = FingerPrinter._fingerprint_for_children(
                    siblings, skip=skip
                )
            elif isinstance(mc.children[0], Header):
                fingerprint = FingerPrinter._fingerprint_for_children(
                    [mc.children[0]], skip=skip
                )
        else:
            fingerprint = FingerPrinter._fingerprint_for_line(mc.matcher.line)
        return fingerprint

    @classmethod
    def _fingerprint_for_children(cls, sibs, skip=None) -> str:
        string = ""
        for _ in sibs:
            string += f"{_ if not hasattr(_, 'to_value') else _.to_value(skip=skip)}"
        return hashlib.sha256(string.encode("utf-8")).hexdigest()

    @classmethod
    def _fingerprint_for_line(cls, line) -> str:
        string = ""
        for _ in line:
            string += f"{_}"
        return hashlib.sha256(string.encode("utf-8")).hexdigest()
