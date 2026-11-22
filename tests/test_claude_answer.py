import asyncio
from types import SimpleNamespace

from schemas.search import ChatContext, ChatTurn, SearchPolicy
from serving.pipeline.answer import FALLBACK_BETA, AnswerDone, ClaudeAnswerer, TextDelta, history_messages, parse_picks
from serving.pipeline.prompt import RECOMMEND_TOOL_NAME
from serving.config import Settings
from serving.pipeline.state import Candidate


def message(stop_reason="tool_use", tool_input=None):
    content = [SimpleNamespace(type="text", text="골라 봤어요.")]
    if tool_input is not None:
        content.append(SimpleNamespace(type="tool_use", name=RECOMMEND_TOOL_NAME, input=tool_input))
    usage = SimpleNamespace(input_tokens=1200, output_tokens=80, cache_read_input_tokens=900)
    return SimpleNamespace(stop_reason=stop_reason, content=content, usage=usage, model="claude-sonnet-5-5")


VALID = {"works": [{"workId": 3, "reason": "계약결혼 소재", "matchedClues": [{"text": "계약결혼", "source": "TAG"}]}]}


def test_history_alternates_and_starts_with_user():
    context = ChatContext(turns=[
        ChatTurn(role="assistant", text="온보딩 인사"),
        ChatTurn(role="user", text="로판"),
        ChatTurn(role="user", text="완결로"),
        ChatTurn(role="assistant", text="이거 어때요"),
        ChatTurn(role="user", text="마지막 질문은 따로 붙는다"),
    ])

    assert history_messages(context) == [
        {"role": "user", "content": "로판\n완결로"},
        {"role": "assistant", "content": "이거 어때요"},
    ]


def test_parse_picks():
    assert [p.work_id for p in parse_picks(message(tool_input=VALID))] == [3]
    assert parse_picks(message(tool_input={"works": [{"workId": "셋"}]})) == []
    assert parse_picks(message(stop_reason="max_tokens", tool_input=VALID)) == []
    assert parse_picks(message(stop_reason="refusal", tool_input=VALID)) == []
    assert parse_picks(message(stop_reason="end_turn")) == []


class FakeStream:
    def __init__(self, events, final):
        self.events, self.final = events, final

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for event in self.events:
            yield event

    async def get_final_message(self):
        return self.final


class FakeClient:
    def __init__(self, stream):
        self.kwargs = None
        outer = self

        class Messages:
            def stream(self, **kwargs):
                outer.kwargs = kwargs
                return stream

        self.beta = SimpleNamespace(messages=Messages())


def test_stream_yields_text_then_done_and_sends_expected_request():
    events = [SimpleNamespace(type="text", text="골라 "), SimpleNamespace(type="input_json", partial_json="{"),
              SimpleNamespace(type="text", text="봤어요.")]
    client = FakeClient(FakeStream(events, message(tool_input=VALID)))
    answerer = ClaudeAnswerer(client, Settings(internal_token="t"))

    async def collect():
        return [item async for item in answerer.stream(
            "계약결혼 로판", [Candidate(work_id=3, title="작품", works_type="WEBTOON")],
            ChatContext(), SearchPolicy(adult_allowed=False))]

    items = asyncio.run(collect())

    assert items[:2] == [TextDelta("골라 "), TextDelta("봤어요.")]
    done = items[-1]
    assert isinstance(done, AnswerDone) and not done.refused
    assert [p.work_id for p in done.picks] == [3]
    assert done.usage[0].cache_read_tokens == 900

    kwargs = client.kwargs
    assert kwargs["model"] == "claude-sonnet-5-5"
    assert kwargs["fallbacks"] == "default" and kwargs["betas"] == [FALLBACK_BETA]
    assert kwargs["tool_choice"] == {"type": "auto"}
    assert kwargs["output_config"] == {"effort": "low"}
    assert kwargs["tools"][0]["eager_input_streaming"] is True
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kwargs["messages"][-1]["role"] == "user"
    assert "workId=3" in kwargs["messages"][-1]["content"]
    assert "19세 이상" in kwargs["messages"][-1]["content"]
