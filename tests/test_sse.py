import asyncio
import json

from schemas.events import ProgressEvent, ProgressStep, RecommendedWork, WorksEvent
from serving.sse import HEARTBEAT, format_event, sse_stream


async def collect(events, heartbeat):
    return [frame async for frame in sse_stream(events, heartbeat)]


def test_format_is_camel_case_sse_frame():
    frame = format_event(WorksEvent(recommended_works=[RecommendedWork(rank=1, work_id=10, reason="r")],
                                    candidate_work_ids=[10, 11], pipeline_version="v1"))

    name, data = frame.removesuffix("\n\n").split("\n")
    assert name == "event: works"
    payload = json.loads(data.removeprefix("data: "))
    assert payload["recommendedWorks"][0]["workId"] == 10
    assert payload["candidateWorkIds"] == [10, 11]


def test_heartbeat_while_waiting():
    async def slow():
        await asyncio.sleep(0.25)
        yield ProgressEvent(step=ProgressStep.SEARCHING, message="찾는 중")

    frames = asyncio.run(collect(slow(), heartbeat=0.1))

    assert frames[0] == HEARTBEAT
    assert frames[-1].startswith("event: progress")


def test_unexpected_exception_becomes_error_event():
    async def broken():
        yield ProgressEvent(step=ProgressStep.SEARCHING, message="찾는 중")
        raise RuntimeError("터짐")

    frames = asyncio.run(collect(broken(), heartbeat=1))

    assert frames[-1].startswith("event: error")
    assert '"code":"INTERNAL"' in frames[-1]


def test_closing_stream_stops_the_pipeline():
    stopped = asyncio.Event()

    async def endless():
        try:
            while True:
                await asyncio.sleep(0.01)
                yield ProgressEvent(step=ProgressStep.SEARCHING, message="찾는 중")
        finally:
            stopped.set()

    async def scenario():
        stream = sse_stream(endless(), heartbeat_seconds=1)
        await anext(stream)
        await stream.aclose()
        return stopped.is_set()

    assert asyncio.run(scenario())
