# pylint: disable=C0114
import datetime
import dateutil.parser
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from ..function_focus import ValueProducer
from ..args import Args
from ..function import Function
from .type import Type


class Date(ValueProducer, Type):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.value_qualifiers.append("notnone")
        self.match_qualifiers.append("notnone")
        self.description = [
            self._cap_name(),
            f"{self.name}() has two purposes.",
            "First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.",
            "Alternatively, it may generate a date from a string.",
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="date",
            types=[Header, Variable, Function, Reference],
            actuals=[None, datetime.datetime, datetime.date],
        )
        a = self.args.argset(2)
        a.arg(
            name="date string",
            types=[Term, Header, Variable, Function, Reference],
            actuals=[None, str],
        )
        a.arg(
            name="format",
            types=[None, Term, Header, Function, Reference],
            actuals=[str],
        )
        self.args.explain = "It must be a date object or a date string with a format."
        self.args.validate(self.siblings())
        #
        #
        #
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        isheader = self._is_header(skip=skip)
        sibs = self.siblings()
        inaline = ExpressionUtility.get_ancestor(self, "Line") is not None
        if inaline:
            v = self._from_header_if(skip=skip)
        else:
            quiet = not isheader
            v = self._from_header_if(skip=skip, quiet=quiet)
            if not v and not isheader and len(sibs) == 1:
                v = self._from_one()
            if not v and not isheader and len(sibs) == 2:
                v = self._from_two()
        if isinstance(v, (datetime.datetime, datetime.date)):
            if isinstance(v, datetime.datetime) and not self.name == "datetime":
                v = v.date()
            self.value = v
        elif ExpressionUtility.is_none(v):
            if self.notnone:
                self.value = None
                msg = "Date cannot be empty"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        else:
            msg = f"'{v}' is not a date or datetime"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)

    def _is_header(self, skip=None):
        h = self._value_one(skip=skip)
        h = f"{h}".strip()
        for _ in self.matcher.csvpath.headers:
            if _.strip() == h:
                return True
        return False

    def _from_one(self):
        v = self._value_one()
        if v and isinstance(v, (datetime.datetime, datetime.date)):
            return v
        if v and isinstance(v, str):
            return ExpressionUtility.to_date(v)
        return None

    def _from_two(self):
        v = self._value_one()
        v = f"{v}".strip()
        fmt = self._value_two()
        r = self._date_from_strings(v, fmt)
        return r

    def _date_from_strings(self, adate, aformat, quiet=False):
        try:
            aformat = f"{aformat}".strip()
            return datetime.datetime.strptime(adate, aformat)
        except ValueError:
            if adate == "" and not self.notnone:
                return None
            if quiet is True:
                return None
            msg = f"Cannot parse date '{adate}' using '{aformat}'"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return None

    def _from_header_if(self, skip=None, quiet=False):
        v = self._value_one(skip=skip)
        if not v:
            return None
        fmt = self._value_two(skip=skip)
        ret = None
        if fmt:
            ret = self._date_from_strings(v, fmt, quiet)
        else:
            ret = ExpressionUtility.to_datetime(v)
        return ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None

    #
    # we don't support the strict qualifier in the regular function, but for
    # testing values against types here we do. might be something to add.
    # strict == a date must not have time or a datetime must have a non-00:00:00z000 time
    #
    @classmethod
    def _is_match(
        cls, *, is_datetime: bool, value: str, strict: bool = True
    ) -> tuple[bool, str | None]:
        if value is None:
            return False
        d = None
        try:
            d = dateutil.parser.parse(value)
        except Exception:
            # import traceback
            # print(traceback.format_exc())
            return False
        d1 = ExpressionUtility.is_date_or_datetime_obj(d)
        if d1 == "unknown":
            return False
        elif (is_datetime is True and d1 != "datetime") and strict:
            return False
        elif (is_datetime is False and d1 != "date") and strict:
            return False
        return True
