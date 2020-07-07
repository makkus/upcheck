# -*- coding: utf-8 -*-
import logging
from typing import Dict, Iterable

from sortedcontainers import SortedList
from upcheck.exceptions import UpcheckException
from upcheck.targets import CheckTarget
from upcheck.url_check import CheckResult, UrlCheck, UrlChecks


log = logging.getLogger("upcheck")


class Upcheck(object):
    def __init__(
        self,
        url_checks: Iterable[UrlCheck],
        targets: Iterable[CheckTarget],
        parallel: bool = False,
    ):

        self._url_checks: UrlChecks = UrlChecks(*url_checks, parallel=parallel)
        self._targets: Dict[str, CheckTarget] = {}
        for _t in targets:
            if _t in self._targets.keys():
                raise UpcheckException(
                    msg=f"Can't create target with id '{_t.get_id()}'.",
                    reason="Duplicate id.",
                )
            self._targets[_t.get_id()] = _t

    async def connect(self):

        failed: Dict[CheckTarget, Exception] = {}
        for _target in self._targets.values():
            log.debug(f"Trying to connect to target: {_target.get_id()}")
            try:
                log.debug(f"Connecting to target: {_target.get_id()}")
                await _target.connect()
            except Exception as e:
                failed[_target] = e
        if failed:
            if len(failed) == 1:
                _ft = list(failed.keys())[0]
                _fe = failed[_ft]
                msg = f"Can't connect to target '{_ft.get_id()}'."
                reason = str(_fe)
            else:
                failed_ids = [_ft.get_id() for _ft in failed.keys()]
                msg = f"Can't connect to targets: {', '.join(failed_ids)}"
                _reason = []
                for _ft, _fe in failed.items():
                    _reason.append(f"  [bold]{_ft.get_id()}[/bold]:")
                    _reason.append(f"       {_fe}")
                reason = "\n".join(_reason)
            raise UpcheckException(msg=msg, reason=reason)

    async def disconnect(self):

        for _target in self._targets.values():

            try:
                await _target.disconnect()
            except Exception as e:
                log.warning(f"Failed to disconnect target '{_target.get_id()}': {e}")

    async def perform_checks(self) -> "SortedList[CheckResult]":

        results: SortedList[CheckResult] = await self._url_checks.perform_checks()

        for _target in self._targets.values():
            log.debug(f"Writing results to target '{_target.get_id()}'...")
            await _target.write(*results)
            log.debug(f"Results written to target '{_target.get_id()}'")

        return results
