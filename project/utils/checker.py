"""ระบบ Judge สำหรับรันโค้ดผ่าน Piston พร้อมตรรกะตรวจภายใน"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any

import aiohttp

PISTON_URL = "https://emkc.org/api/v2/piston/execute"
RUNTIME_MAP = {
    "python": {"language": "python", "version": "3.10.0"},
    "c": {"language": "c", "version": "10.2.0"},
}


@dataclass(slots=True)
class TestcaseResult:
    """ผลลัพธ์ของแต่ละ testcase"""

    index: int
    passed: bool
    expected: str
    got: str


@dataclass(slots=True)
class JudgeResult:
    """ผลลัพธ์รวมของการตรวจโค้ด"""

    verdict: str
    passed: bool
    output: str
    error: str
    testcase_results: list[TestcaseResult]
    style_score: int
    warning: str = ""


def _normalize_text(text: str, ignore_case: bool = True, ignore_space: bool = True) -> str:
    """ช่วย normalize ข้อความก่อนเทียบคำตอบ"""

    value = text.strip()
    if ignore_space:
        value = "\n".join(line.strip() for line in value.splitlines())
    if ignore_case:
        value = value.lower()
    return value


def _match_output(actual: str, accepted_outputs: list[str], regex_compare: bool, ignore_case: bool, ignore_space: bool) -> bool:
    """รองรับ accepted output หลายค่า + regex"""

    normalized_actual = _normalize_text(actual, ignore_case=ignore_case, ignore_space=ignore_space)
    for target in accepted_outputs:
        if regex_compare:
            flags = re.IGNORECASE if ignore_case else 0
            if re.fullmatch(target, actual.strip(), flags=flags):
                return True
            continue
        if normalized_actual == _normalize_text(target, ignore_case=ignore_case, ignore_space=ignore_space):
            return True
    return False


def _style_score(code: str) -> int:
    """คำนวณ style score แบบเบา ๆ"""

    lines = [line for line in code.splitlines() if line.strip()]
    if not lines:
        return 0
    long_lines = sum(1 for line in lines if len(line) > 120)
    has_comment = any("#" in line or "//" in line for line in lines)
    score = 100 - min(40, long_lines * 5)
    if has_comment:
        score += 5
    return max(0, min(100, score))


def precheck_keywords(code: str, task: dict[str, Any]) -> tuple[bool, str]:
    """ตรวจ required/forbidden keyword ก่อนยิง API"""

    required_any = task.get("required_keywords_any", [])
    forbidden = task.get("forbidden_keywords", [])

    if required_any and not any(keyword in code for keyword in required_any):
        return False, f"⚠️ คุณลืมใช้หนึ่งในคีย์เวิร์ด: {', '.join(required_any)}"

    found_forbidden = [keyword for keyword in forbidden if keyword in code]
    if found_forbidden:
        return False, f"⚠️ ห้ามใช้คีย์เวิร์ด: {', '.join(found_forbidden)}"

    if "while True" in code or "for(;;)" in code:
        return False, "⚠️ ตรวจพบรูปแบบเสี่ยง Infinite Loop กรุณาใส่เงื่อนไขหยุด"

    return True, ""


async def _run_code(language: str, code: str, stdin: str, timeout_sec: int) -> dict[str, Any]:
    """เรียก Piston API ต่อ 1 testcase"""

    payload = {
        "language": RUNTIME_MAP[language]["language"],
        "version": RUNTIME_MAP[language]["version"],
        "files": [{"name": "main", "content": code}],
        "stdin": stdin,
    }
    timeout = aiohttp.ClientTimeout(total=max(5, timeout_sec + 3))

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(PISTON_URL, json=payload) as response:
            return await response.json()


async def check_code(language: str, code: str, task: dict[str, Any]) -> JudgeResult:
    """ตรวจโค้ดแบบครบขั้นตอน: precheck -> run many testcase -> verdict"""

    if language not in RUNTIME_MAP:
        return JudgeResult("System Error", False, "", f"ยังไม่รองรับภาษา {language}", [], 0)

    testcases = task.get("testcases") or [{"input": "", "accepted_outputs": task.get("accepted_outputs", [])}]
    regex_compare = bool(task.get("regex_compare", False))
    ignore_case = bool(task.get("ignore_case", True))
    ignore_space = bool(task.get("ignore_space", True))
    timeout_sec = int(task.get("time_limit_sec", 2))
    style_score = _style_score(code)

    all_results: list[TestcaseResult] = []
    final_output = ""

    for index, testcase in enumerate(testcases, start=1):
        accepted_outputs = testcase.get("accepted_outputs", task.get("accepted_outputs", []))
        if not accepted_outputs:
            accepted_outputs = [""]

        try:
            data = await asyncio.wait_for(
                _run_code(language=language, code=code, stdin=str(testcase.get("input", "")), timeout_sec=timeout_sec),
                timeout=timeout_sec + 4,
            )
        except TimeoutError:
            return JudgeResult("Time Limit Exceeded", False, final_output, "รันโค้ดเกินเวลาที่กำหนด", all_results, style_score)
        except Exception as exc:  # noqa: BLE001
            return JudgeResult("System Error", False, final_output, f"เชื่อมต่อ Judge ไม่สำเร็จ: {exc}", all_results, style_score)

        run = data.get("run", {})
        compile_data = data.get("compile", {})
        stdout = str(run.get("stdout", "") or "")
        stderr = str(run.get("stderr", "") or "")
        compile_stderr = str(compile_data.get("stderr", "") or "")
        final_output = stdout

        if compile_stderr:
            return JudgeResult("Compile Error", False, stdout, compile_stderr, all_results, style_score)
        if stderr:
            return JudgeResult("Runtime Error", False, stdout, stderr, all_results, style_score)

        passed = _match_output(
            actual=stdout,
            accepted_outputs=list(accepted_outputs),
            regex_compare=regex_compare,
            ignore_case=ignore_case,
            ignore_space=ignore_space,
        )

        expected_preview = " | ".join(accepted_outputs)
        all_results.append(TestcaseResult(index=index, passed=passed, expected=expected_preview, got=stdout.strip()))

        if not passed:
            return JudgeResult("Wrong Answer", False, stdout, "ผลลัพธ์ไม่ตรงที่กำหนด", all_results, style_score)

    return JudgeResult("Accepted", True, final_output, "", all_results, style_score)
