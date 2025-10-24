from typing import Any, Dict

from .exceptions import PrintParserException


class RuntimeDataCollector:
    @classmethod
    def collect(cls, csvpath, runtime: Dict[str, Any], local=False) -> None:
        identity = csvpath.identity
        #
        # Common to all csvpaths in results
        #
        if "delimiter" in runtime:
            if runtime["delimiter"] != csvpath.delimiter:
                raise PrintParserException(
                    f"Unalike delimiter: {identity}: {csvpath.delimiter}"
                )
        else:
            runtime["delimiter"] = csvpath.delimiter
        if "quotechar" in runtime:
            if runtime["quotechar"] != csvpath.quotechar:
                raise PrintParserException(
                    f"Unalike quotechar: {identity}: {csvpath.quotechar}"
                )
        else:
            runtime["quotechar"] = csvpath.quotechar
        #
        # exp
        #
        # runtime["file_name"] = csvpath.scanner.filename if csvpath.scanner else "unavailable"
        #
        # orig
        #
        if csvpath.scanner and csvpath.scanner.filename is not None:
            runtime["file_name"] = csvpath.scanner.filename
        #
        # end exp
        #
        cls._set(
            runtime, identity, "lines_time", round(csvpath.rows_time, 3), local, True
        )
        if csvpath.line_monitor:
            cls._set(
                runtime,
                identity,
                "total_lines",
                csvpath.line_monitor.data_end_line_count,
                True,
                True,
            )
        #
        # end of common-to-all
        #
        if csvpath.line_monitor:
            cls._set(
                runtime,
                identity,
                "count_lines",
                csvpath.line_monitor.physical_line_count,
                local,
                False,
            )
        if csvpath.line_monitor:
            cls._set(
                runtime,
                identity,
                "line_number",
                csvpath.line_monitor.physical_line_number,
                local,
                False,
            )
        cls._set(runtime, identity, "identity", identity, local, False)
        cls._set(runtime, identity, "count_matches", csvpath.match_count, local, False)
        cls._set(runtime, identity, "count_scans", csvpath.scan_count, local, False)
        cls._set(runtime, identity, "scan_part", csvpath.scan, local, False)
        cls._set(runtime, identity, "match_part", csvpath.match, local, False)
        cls._set(
            runtime,
            identity,
            "last_line_time",
            round(csvpath.last_row_time, 3),
            local,
            False,
        )
        #
        # headers can change. atm, we lose the changes but can at least capture the
        # potentially different end states
        #
        cls._set(runtime, identity, "headers", csvpath.headers, local, False)
        cls._set(runtime, identity, "valid", csvpath.is_valid, local, False)
        cls._set(runtime, identity, "stopped", csvpath.stopped, local, False)
        #
        #
        #
        cls._set(
            runtime,
            identity,
            "unmatched-mode",
            csvpath.unmatched_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "validation-mode",
            csvpath.validation_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "source-mode",
            csvpath.source_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "print-mode",
            csvpath.print_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "run-mode",
            csvpath.run_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "logic-mode",
            csvpath.logic_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "explain-mode",
            csvpath.explain_mode,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "return-mode",
            csvpath.return_mode,
            local,
            False,
        )
        started = f"{csvpath.run_started_at}"
        cls._set(runtime, identity, "run_started_at", started, local, False)
        cls._set(
            runtime,
            identity,
            "lines_collected",
            len(csvpath.lines) if csvpath.lines else -1,
            local,
            False,
        )
        cls._set(
            runtime,
            identity,
            "errors_count",
            csvpath.errors_count,
            local,
            False,
        )

    @classmethod
    def _set(
        cls, runtime, identity: str, name: str, value, local: bool, addative: False
    ) -> None:
        if local:
            runtime[name] = value
        else:
            if addative:
                if name in runtime:
                    runtime[name] += value
                else:
                    runtime[name] = value
            else:
                if name not in runtime:
                    runtime[name] = {}
                runtime[name][identity] = value
