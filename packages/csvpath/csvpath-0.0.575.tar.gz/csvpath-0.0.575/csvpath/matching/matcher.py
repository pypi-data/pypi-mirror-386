""" Matching is the core of CsvPath. """

from typing import Any, List
from .productions import Equality, Matchable
from .functions.function import Function
from .util.expression_encoder import ExpressionEncoder
from .util.expression_utility import ExpressionUtility
from .util.exceptions import MatchException, ChildrenException
from .lark_parser import LarkParser
from .lark_transformer import LarkTransformer


class What:
    """holds info used in explain-mode"""

    def __init__(self, matcher, matchable) -> None:
        self._who = matchable
        self._matcher = matcher
        self._action = None
        self._left = None
        self._right = None
        self._because = None
        self._result = None
        if hasattr(matchable, "op"):
            self._left = matchable.left
            self._right = matchable.right

    def get_action(self):
        return self._action

    def action(self, a):
        self._action = a
        return self

    def get_because(self):
        return self._because

    def because(self, b):
        self._because = b
        return self

    def get_result(self):
        return self._result

    def result(self, r):
        self._result = r
        return self

    def __str__(self) -> str:
        between = ""
        if self._left is not None:
            between = self._left.named_value()
        if self._right is not None:
            between = f"between {between} and {self._right.named_value()}"
        because = ""
        if self._because is not None:
            because = f"because {self._because}"
        return f"{self._who.named_value()} did {self._action} {between} {because} resulting in {self._result}"


class Matcher:  # pylint: disable=R0902
    """Matcher implements the match component rules processing that
    is applied to files line-by-line. matchers are created at the
    beginning of a run and are reset and reused for every line.
    """

    # re: R0902: no obvious improvements

    def __init__(self, *, csvpath=None, data=None, line=None, headers=None, myid=None):
        if not headers:
            # this could be a dry-run or unit testing
            pass
        if not data:
            raise MatchException(f"Input needed: data: {data}")  # pragma: no cover
        self.path = data
        self.csvpath = csvpath
        self._line = line
        self._id = f"{myid}"
        self.expressions = []
        self.if_all_match = []
        #
        # skip shortcircuts the match and results in the line not matching
        # and potentially other match components being unconsidered (the general
        # intent; though not always the case).
        #
        # take is the same as skip, but matching the row. e.g. we might want to
        # scan a 0th line to collect the headers but no more than that. take()
        # let's us grab the line and not have to deflect the rest of the match
        # components.
        #
        self.skip = False
        self.take = False
        self.cachers = []
        self._explain = []
        self._AND = True  # pylint: disable=C0103
        self._validity_checked = False
        if data is not None:
            self.parser = LarkParser()
            tree = self.parser.parse(data)
            if self.csvpath:
                self.csvpath.logger.debug("Raw parse tree: %s", tree)
            transformer = LarkTransformer(self)
            es = transformer.transform(tree)
            # print(tree.pretty())
            expressions = []
            for e in es:
                expressions.append([e, None])
                #
                # expressions need to know when an error happens. they may be
                # explicitly configured to match or not match on error. errors
                # other than unexpected non-CsvPath exceptions (e.g. ValueError)
                # don't go through the expression, so the expression needs to be
                # notified so it can match accordingly. keep in mind that this
                # assumes the CsvPath internals (for any given CsvPath) are
                # single-threaded. 3rd party integration error listeners may and
                # often should be async, but we need each expression to know about
                # its errors before it completes processing and gives the Matcher
                # a determination.
                #
                if self.csvpath:
                    self.csvpath.error_manager.add_internal_listener(e)
            self.expressions = expressions
            self.check_valid()
        if self.csvpath:
            self.csvpath.logger.info("initialized Matcher")

    def __str__(self):
        return f"""{type(self)}:
            expressions: {self.expressions}
            line: {self.line}"""

    @property
    def validity_checked(self) -> bool:
        return self._validity_checked

    @validity_checked.setter
    def validity_checked(self, chked: bool) -> None:
        self._validity_checked = chked

    @property
    def AND(self) -> bool:  # pylint: disable=C0103
        return self._AND  # pragma: no cover

    @AND.setter
    def AND(self, a: bool) -> None:  # pylint: disable=C0103
        self._AND = a

    @property
    def line(self) -> List[List[Any]]:  # pylint: disable=C0116
        return self._line

    @line.setter
    def line(self, line: List[List[Any]]) -> None:
        self._line = line

    def to_json(self, e) -> str:  # pylint: disable=C0116
        return ExpressionEncoder().to_json(e)

    def dump_all_expressions_to_json(self) -> str:  # pylint: disable=C0116
        return ExpressionEncoder().valued_list_to_json(self.expressions)

    def reset(self):  # pylint: disable=C0116
        for expression in self.expressions:
            expression[1] = None
            expression[0].reset()
        self._explain = []

    #
    # exp!
    #
    #
    @property
    def explanation(self) -> list[tuple]:
        return self._explain

    @explanation.setter
    def explanation(self, es) -> None:
        self._explain = es

    def what(self, actor, action) -> What:
        what = What(self, actor)
        what.action(action)
        self._explain.append(what)
        return what

    #
    # end exp
    #

    def header_index(self, name: str) -> int:
        """returns the index of a header name in the current headers. remember that
        a header_reset() can change the indexes mid file.
        1, "1", "nameof1" are all acceptable. If not found, None. No raise.
        """
        i = None
        if isinstance(name, int):
            return name
        #
        # to_int is no longer going to raise exceptions. we can remove the try/except
        #
        try:
            i = ExpressionUtility.to_int(name)
            if isinstance(i, int):
                return i
        except ValueError:
            ...
        x = self.csvpath.header_index(name)
        return x

    def header_name(self, i: int) -> str:
        """returns the name of a header given an index into the current headers.
        remember that a header_reset() can change the indexes mid file."""
        if not self.csvpath.headers:
            return None
        if i < 0 or i >= len(self.csvpath.headers):
            return None
        return self.csvpath.headers[i]

    def get_header_value(self, m, name_or_index, quiet=False):
        nori = ExpressionUtility.to_int(name_or_index)
        if not isinstance(nori, int):
            nori = self.header_index(name_or_index)
        if nori is None:
            if quiet is False:
                hs = self.csvpath.headers
                msg = f"No headers match '{name_or_index}'. Current headers are: {hs}"
                self.csvpath.logger.error(msg)
                self.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.csvpath.do_i_raise():
                    raise MatchException(msg)
            return None
        if nori >= len(self.line):
            if quiet is False:
                hs = self.csvpath.headers
                msg = f"No headers match '{name_or_index}'. Current headers are: {hs}"
                self.csvpath.logger.error(msg)
                self.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.csvpath.do_i_raise():
                    raise MatchException(msg)
            return None
        v = self.line[nori]
        if ExpressionUtility.is_none(v):
            v = None
        if v is not None:
            v = v.strip()
        return v

    def _do_lasts(self) -> None:
        for et in self.expressions:
            e = et[0]
            self._find_and_actvate_lasts(e)

    def _find_and_actvate_lasts(self, e) -> None:
        self.csvpath.logger.debug("Looking for last()s to activate")
        cs = e.children[:]
        while len(cs) > 0:
            c = cs.pop()
            if (
                isinstance(c, Equality)
                and c.op == "->"
                and c.left
                and isinstance(c.left, Function)
                and c.left.name == "last"
            ):
                c.matches(skip=[])
            elif isinstance(c, Function) and c.name == "last":
                c.matches(skip=[])
            else:
                cs += c.children

    def _cache_me(self, matchable: Matchable) -> None:
        self.cachers.append(matchable)

    def clear_caches(self) -> None:
        for _ in self.cachers:
            _.clear_caches()
        self.cachers = []

    def matches(self) -> bool:  # pylint: disable=R0912
        """this is the main work of the Matcher. we enumerate the self.expressions.
        if all evaluate to True in an AND operation we return True."""
        # re: R0912 this method has been refactoring resistant and since it is
        # working stably there isn't a pressing reason to try again.
        #
        # is this a blank last line? if so, we just want to activate any/all
        # last() in the csvpath.
        #
        if self.csvpath.line_monitor.is_last_line_and_blank(self.line):
            self.csvpath.logger.debug(
                "Is last line and blank. Doing lasts and then returning True"
            )
            self._do_lasts()
            # self.clear_errors()
            return True
        ret = True
        failed = self._AND is not True
        # failed = False if self._AND else True
        self.csvpath.logger.debug(
            "Beginning %s match against line[%s]: %s",
            ("AND" if self._AND else "OR"),
            self.csvpath.line_monitor.physical_line_number,
            str(self.line),
        )
        for i, et in enumerate(self.expressions):
            self.csvpath.logger.debug(
                "Beginning to consider expression: expressions[%s]: %s: %s",
                i,
                et[0],
                et[1],
            )
            if self.csvpath and self.csvpath.stopped:
                #
                # stopped is like a system halt. this csvpath is calling it
                # quits on this CSV file. we don't continue to match the row
                # so we may miss out on some side effects. we just return
                # because the function already let the CsvPath know to stop.
                #
                pln = self.csvpath.line_monitor.physical_line_number
                self.csvpath.logger.debug("Stopped at line %s", pln)
                # self.clear_errors()
                return False
            if self.skip is True:
                #
                # skip is like the continue statement in a python loop
                # we're not only not matching, we don't want any side effects
                # we might gain from continuing to check for a match;
                # but we also don't want to stop the run or fail validation
                #
                pln = self.csvpath.line_monitor.physical_line_number
                self.csvpath.logger.debug("Skipping at line %s", pln)
                self.skip = False
                # self.clear_errors()
                if self.take is True:
                    self.take = False
                    return True
                else:
                    return False
            #
            # from here down we care what the expression tells us.
            # we can require concordance or we can allow executive
            # decisons.
            #
            if et[1] is True:
                # these are due to the onmatch qualifier doing its own matching cycle
                ret = True
            elif et[1] is False:
                # these are due to the onmatch qualifier doing its own matching cycle
                ret = False
            elif et[0].matches(skip=[]) is False:
                et[1] = False
                ret = False
            else:
                et[1] = True
                ret = True
            #
            # now ret holds this expression's vote
            #
            pln = self.csvpath.line_monitor.physical_line_number
            self.csvpath.logger.debug(
                "Matcher.matches: ready to adjudicate %s component %s match: ret: %s, failed: %s",
                "AND" if self._AND else "OR",
                str(et[0]),
                ret,
                failed,
            )
            if self._AND:
                if ret is False:
                    failed = True
            else:
                if ret is True:
                    failed = False

        #
        # here we could be set to do an OR, not an AND.
        # we would do that only in the case that the answer was False. if so, we
        # would recheck all self.expressions[.][1] for a True. if at least one
        # were found, we would respond True; else, False.
        #
        pln = self.csvpath.line_monitor.physical_line_number
        self.csvpath.logger.debug(
            "Matcher.matches: result (AND:%s) for line %s: %s",
            self._AND,
            pln,
            not failed,
        )
        # self.clear_errors()
        #
        # exp!  do we want to keep this?
        #
        if self.csvpath.explain:
            self.csvpath.logger.info("Dumping explanation:")
            for e in self.explanation:
                self.csvpath.logger.info(f"  {e}")
            self.explanation = []
        #
        # end exp
        #
        return not failed

    """
    def clear_errors(self) -> None:
        for es in self.expressions:
            es[0].handle_errors_if()
    """

    def check_valid(self) -> None:  # pylint: disable=C0116
        if self.csvpath:
            self.csvpath.logger.debug(
                "Matcher starting pre-iteration match components structure validation"
            )
        self.validity_checked = False
        for _ in self.expressions:
            _[0].check_valid()
        # self.clear_errors()
        if self.csvpath:
            self.csvpath.logger.debug(
                "Pre-iteration match components structure validation done"
            )
        self.validity_checked = True

    def get_variable(self, name: str, *, tracking=None, set_if_none=None) -> Any:
        """see CsvPath.get_variable"""
        return self.csvpath.get_variable(
            name, tracking=tracking, set_if_none=set_if_none
        )

    def set_variable(self, name: str, *, value: Any, tracking=None) -> None:
        """see CsvPath.set_variable"""
        return self.csvpath.set_variable(name, value=value, tracking=tracking)

    def last_header_index(self) -> int:  # pylint: disable=C0116
        if self.line and len(self.line) > 0:
            return len(self.line) - 1
        return None

    def last_header_name(self) -> str:  # pylint: disable=C0116
        if self.csvpath.headers and len(self.csvpath.headers) > 0:
            return self.csvpath.headers[self.last_header_index()]
        return None
