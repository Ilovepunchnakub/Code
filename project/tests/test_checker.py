from __future__ import annotations

import asyncio

from utils import checker


def test_normalize_text_handles_case_and_space() -> None:
    assert checker._normalize_text("  Hello\r\nWorld  ") == "hello\nworld"


def test_match_modes() -> None:
    assert checker._is_match("Hello", ["hello"], compare_mode="normalized")
    assert checker._is_match("42", [r"\d+"], compare_mode="regex")
    assert checker._is_match("1.000001", ["1.000002"], compare_mode="float_tolerance", tolerance=1e-5)


def test_precheck_keywords_required_and_forbidden() -> None:
    ok, warning = checker.precheck_keywords("print('x')", {"required_keywords": ["print"]})
    assert ok and warning == ""

    ok2, warning2 = checker.precheck_keywords("int main(){goto x;}", {"forbidden_keywords": ["goto"]})
    assert not ok2
    assert "ห้ามใช้คีย์เวิร์ด" in warning2


def test_check_code_verdict_mapping(monkeypatch) -> None:
    async def fake_execute(**_: object) -> dict[str, object]:
        return {"run": {"stdout": "hello\n", "stderr": "", "code": 0, "signal": ""}, "compile": {"stderr": ""}}

    monkeypatch.setattr(checker, "_execute_with_retry", fake_execute)
    result = asyncio.run(checker.check_code("python", "print('hello')", {"accepted_outputs": ["Hello"], "testcases": [{"input": "", "accepted_outputs": ["hello"]}]}))
    assert result.passed is True
    assert result.verdict == "Accepted"


def test_judge_queue_worker(monkeypatch) -> None:
    async def fake_check_code(language: str, code: str, task: dict[str, object]) -> checker.JudgeResult:
        return checker.JudgeResult("Accepted", True, "x", "x", "-", [])

    monkeypatch.setattr(checker, "check_code", fake_check_code)
    worker = checker.JudgeQueueWorker(worker_count=1)
    res = asyncio.run(worker.submit("python", "print(1)", {}))
    assert res.passed is True
    asyncio.run(worker.stop())
