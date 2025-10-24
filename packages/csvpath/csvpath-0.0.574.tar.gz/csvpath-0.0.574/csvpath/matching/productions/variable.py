# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException


class Variable(Matchable):
    """a variable that persists for the life of the csvpath run.
    variables may live longer bound to results when they are in
    the context of a CsvPaths, rather than just a single
    CsvPath.
    """

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        n, qs = ExpressionUtility.get_name_and_qualifiers(name)
        self.name = n
        self.qualifiers = qs
        #
        # don't see any way this could happen outside dev so not checking do_i_raise()
        #
        if n is None:
            raise ChildrenException("Name cannot be None")
        if n.strip() == "":
            raise ChildrenException("Name cannot be the empty string")

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}({self.qualified_name})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        #
        # clearing self.value is obviously not the same as resetting
        # the underlying variable value. if we have a reset qualifier
        # we reset the variable in self.matcher.csvpath at each line.
        #
        if self.renew:
            self.matcher.csvpath.set_variable(self.name, value=None)
        super().reset()

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            ret = self._noop_match()
            self.matching().result(ret).because("skip")
            return ret
        if self.match is None:
            if self.asbool:
                v = self.to_value(skip=skip)
                self.match = ExpressionUtility.asbool(v)
                self.matching().result(self.match).because("onbool")
            else:
                self.match = self.to_value(skip=skip) is not None
                self.matcher.csvpath.logger.debug(
                    "Variable %s returning existance test result of %s",
                    self.name,
                    self.match,
                )
                self.matching().result(self.match)
        return self.match

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            ret = self._noop_value()
            self.valuing().result(ret).because("skip")
            return ret
        if not self.value:
            track = self.first_non_term_qualifier(None)
            self.value = self.matcher.get_variable(self.name, tracking=track)
            if self.value is None:
                # if it looks like a bool let's try that and
                # take the answer if not None.
                # in principle we could do this with numbers too.
                retry = None
                if track == "True":
                    retry = self.matcher.get_variable(self.name, tracking=True)
                elif track == "False":
                    retry = self.matcher.get_variable(self.name, tracking=False)
                if retry is not None:
                    self.value = retry
        self.valuing().result(self.value)
        return self.value
