"""Running one check over every buyer, and writing the verdict onto the pipeline.

Relevance and availability ask different questions of different agents, but the shape of
asking is the same: one call per buyer, a few in flight at a time, a verdict written onto the
buyer's pipeline. That shape lives here so the two checks only have to say what is different
about them.
"""

import asyncio
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel

from shared.schemas.blocks.pipeline import Pipeline
from shared.schemas.buyer import Buyer
from shared.schemas.common.enums import CheckResult, CheckStatus

# Which pair of pipeline fields a check writes. Not `Stage`, whose values are "relevance" and
# "availability": these are the field prefixes on `Pipeline`, and they differ.
CheckField = Literal["relevant", "available"]

DEFAULT_CONCURRENCY = 10


class Agent(Protocol):
    """The part of an agent a check uses."""

    async def run(self, prompt: str) -> Any: ...


@dataclass(frozen=True)
class Check:
    """Everything that differs between one check and another.

    `prompt` is a callable rather than a template because relevance needs the brief and
    availability does not; a check that needs more context closes over it.
    """

    agent: Agent
    result: type[BaseModel]
    prompt: Callable[[Buyer], str]
    reason: Callable[[Any], str]
    field: CheckField
    by: str
    concurrency: int = DEFAULT_CONCURRENCY


async def run_check(buyers: list[Buyer], check: Check) -> list[Buyer]:
    """Run `check` over every buyer and return them all, each carrying its verdict.

    One list rather than two: no buyer is lost by being checked, and the status field already
    says which of verified, excluded and failed each one got. Splitting them would say the
    same thing twice and force the caller to put them back together to write the run.
    """
    print(f"[{check.field}] checking {len(buyers)} buyers, {check.concurrency} at a time", flush=True)
    limit = asyncio.Semaphore(check.concurrency)
    checked = list(await asyncio.gather(*(_check_one(buyer, check, limit) for buyer in buyers)))

    tally = Counter(getattr(b.pipeline, f"{check.field}_status").value for b in checked)
    print(f"[{check.field}] done: {dict(tally)}", flush=True)
    return checked


async def _check_one(buyer: Buyer, check: Check, limit: asyncio.Semaphore) -> Buyer:
    async with limit:
        try:
            response = await check.agent.run(check.prompt(buyer))
            verdict = check.result.model_validate(response.value or {})
        except Exception as error:
            # The buyer survives as unchecked rather than as excluded: nothing was established,
            # which is not the same as establishing there is nothing there.
            print(f"[{check.field}]   {buyer.identity.name}: FAILED {type(error).__name__}: {error}", flush=True)
            return write_verdict(buyer, check, CheckStatus.FAILED, reason=None)

        excluded = verdict.result is CheckResult.EXCLUDED
        reason = check.reason(verdict) if excluded else None
        print(
            f"[{check.field}]   {buyer.identity.name}: "
            f"{'excluded' if excluded else 'verified'}{f' ({reason})' if reason else ''}",
            flush=True,
        )
        return write_verdict(
            buyer,
            check,
            CheckStatus.EXCLUDED if excluded else CheckStatus.VERIFIED,
            reason=reason,
        )


def write_verdict(buyer: Buyer, check: Check, status: CheckStatus, reason: str | None) -> Buyer:
    """Write a verdict onto the buyer's pipeline, revalidating as it goes.

    Through `model_validate` rather than `model_copy` so the rule that a reason accompanies an
    exclusion, and only an exclusion, is enforced here too rather than trusted.
    """
    pipeline = Pipeline.model_validate(
        buyer.pipeline.model_dump()
        | {
            f"{check.field}_status": status,
            f"{check.field}_at": datetime.now(UTC),
            f"{check.field}_by": check.by,
            f"{check.field}_reason": reason,
        }
    )
    return buyer.model_copy(update={"pipeline": pipeline})
