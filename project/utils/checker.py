"""ระบบ Judge สำหรับรันโค้ดผ่าน Piston API พร้อม queue worker และ retry"""

from __future__ import annotations

import asyncio
import math
import re
from dataclasses import dataclass
from typing import Any

import aiohttp

DEFAULT_PISTON_URLS = ["https://emkc.org/api/v2/piston/execute", "https://piston.rs/api/v2/execute"]
MAX_OUTPUT_LEN = 1500

RUNTIME_CONFIG = {
    "python": {"language": "python", "version": "3.10.0", "filename": "main.py"},
    "c": {"language": "c", "version": "10.2.0", "filename": "main.c"},
}


@dataclass(slots=True)
class TestcaseResult:
    index: int
    passed: bool
    expected: str
    got: str


@dataclass(slots=True)
class JudgeResult:
    verdict: str
    passed: bool
    expected_output: str
    your_output: str
    error_message: str
    testcase_results: list[TestcaseResult]


@dataclass(slots=True)
class JudgeJob:
    language: str
    code: str
    task: dict[str, Any]
    future: asyncio.Future[JudgeResult]


def _truncate_output(text: str) -> str:
    clean = text or ""
    return clean if len(clean) <= MAX_OUTPUT_LEN else f"{clean[:MAX_OUTPUT_LEN]}... (ตัดข้อความ)"


def _normalize_text(text: str, ignore_case: bool = True, strip_all_whitespace: bool = False) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if strip_all_whitespace:
        cleaned = "\n".join(" ".join(line.split()) for line in cleaned.split("\n"))
    else:
        cleaned = "\n".join(line.strip() for line in cleaned.split("\n"))
    return cleaned.lower() if ignore_case else cleaned


def _split_csv_text(value: str) -> list[str]:
    return [chunk.strip() for chunk in (value or "").split(",") if chunk.strip()]




def _piston_urls() -> list[str]:
    # ใช้ public endpoint เป็นค่าเริ่มต้น (ไม่ต้อง token)
    return list(DEFAULT_PISTON_URLS)


def _piston_headers() -> dict[str, str]:
    # ไม่ส่ง Authorization header เพื่อเลี่ยง 401 จากค่า ENV ผิด
    return {}


def _float_lines_match(actual: str, expected: str, tolerance: float) -> bool:
    actual_lines = _normalize_text(actual, ignore_case=False).split("\n")
    expected_lines = _normalize_text(expected, ignore_case=False).split("\n")
    if len(actual_lines) != len(expected_lines):
        return False
    for a_line, e_line in zip(actual_lines, expected_lines, strict=False):
        try:
            if not math.isclose(float(a_line), float(e_line), rel_tol=tolerance, abs_tol=tolerance):
                return False
        except ValueError:
            return False
    return True


def _is_match(actual: str, accepted_outputs: list[str], compare_mode: str = "normalized", tolerance: float = 1e-6) -> bool:
    compare_mode = (compare_mode or "normalized").lower()
    for output in accepted_outputs:
        if compare_mode == "exact":
            if actual == output:
                return True
        elif compare_mode == "regex":
            if re.fullmatch(output, actual.strip(), flags=re.IGNORECASE):
                return True
        elif compare_mode == "float_tolerance":
            if _float_lines_match(actual, output, tolerance=tolerance):
                return True
        else:
            if _normalize_text(actual, ignore_case=True, strip_all_whitespace=True) == _normalize_text(
                output, ignore_case=True, strip_all_whitespace=True
            ):
                return True
    return False


def _build_keyword_warning(code: str, task: dict[str, Any]) -> str | None:
    required = task.get("required_keywords") or []
    forbidden = task.get("forbidden_keywords") or []
    if isinstance(required, str):
        required = _split_csv_text(required)
    if isinstance(forbidden, str):
        forbidden = _split_csv_text(forbidden)

    if required and not any(keyword in code for keyword in required):
        return f"⚠️ คุณลืมใช้ {required[0]}"

    found_forbidden = [keyword for keyword in forbidden if keyword in code]
    if found_forbidden:
        return f"⚠️ ห้ามใช้คีย์เวิร์ด: {', '.join(found_forbidden)}"

    if "while True" in code or "for(;;)" in code:
        return "⚠️ ตรวจพบรูปแบบเสี่ยง Infinite Loop กรุณาเพิ่มเงื่อนไขหยุด"

    if "int main" not in code and task.get("language_hint") == "c":
        return "⚠️ คำเตือน: โค้ดภาษา C ควรมีฟังก์ชัน int main()"

    return None


def precheck_keywords(code: str, task: dict[str, Any]) -> tuple[bool, str]:
    warning = _build_keyword_warning(code, task)
    return (warning is None), (warning or "")


async def _execute(language: str, code: str, stdin: str, timeout_sec: int) -> dict[str, Any]:
    runtime = RUNTIME_CONFIG[language]
    payload = {
        "language": runtime["language"],
        "version": runtime["version"],
        "files": [{"name": runtime["filename"], "content": code}],
        "stdin": stdin,
    }

    timeout = aiohttp.ClientTimeout(total=max(8, timeout_sec + 6))
    headers = _piston_headers()
    last_error: Exception | None = None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for url in _piston_urls():
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 401:
                        raise PermissionError(
                            "Piston API Unauthorized (401): ตรวจสอบ PISTON_URL/PISTON_API_TOKEN หรือ PISTON_AUTH_HEADER"
                        )
                    response.raise_for_status()
                    return await response.json()
            except PermissionError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

    raise RuntimeError(f"ไม่สามารถเชื่อมต่อ Piston ได้ทุก endpoint: {last_error}")



async def _execute_with_retry(language: str, code: str, stdin: str, timeout_sec: int, retries: int = 2) -> dict[str, Any]:
    attempt = 0
    while True:
        try:
            return await _execute(language=language, code=code, stdin=stdin, timeout_sec=timeout_sec)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt >= retries:
                raise
            await asyncio.sleep(0.4 * (2**attempt))
            attempt += 1


async def check_code(language: str, code: str, task: dict[str, Any]) -> JudgeResult:
    if language not in RUNTIME_CONFIG:
        return JudgeResult("System Error", False, "-", "-", f"ยังไม่รองรับภาษา {language}", [])

    task = dict(task)
    if language == "c":
        task["language_hint"] = "c"

    keyword_warning = _build_keyword_warning(code, task)
    if keyword_warning and not keyword_warning.startswith("⚠️ คำเตือน"):
        return JudgeResult("Keyword Check", False, "-", "-", keyword_warning, [])

    accepted_outputs = task.get("accepted_outputs") or [""]
    testcases = task.get("testcases") or [{"input": "", "accepted_outputs": accepted_outputs}]
    timeout_sec = int(task.get("time_limit") or 2)
    memory_limit = int(task.get("memory_limit") or 128)
    compare_mode = str(task.get("compare_mode") or "normalized")
    tolerance = float(task.get("float_tolerance") or 1e-6)

    testcase_results: list[TestcaseResult] = []
    latest_stdout = ""

    for index, testcase in enumerate(testcases, start=1):
        tc_input = str(testcase.get("input", ""))
        tc_expected = testcase.get("accepted_outputs") or accepted_outputs
        if isinstance(tc_expected, str):
            tc_expected = _split_csv_text(tc_expected)

        try:
            response_data = await asyncio.wait_for(
                _execute_with_retry(language=language, code=code, stdin=tc_input, timeout_sec=timeout_sec),
                timeout=timeout_sec + 6,
            )
        except asyncio.TimeoutError:
            return JudgeResult(
                "Time Limit Exceeded",
                False,
                " | ".join(tc_expected),
                _truncate_output(latest_stdout.strip() or "-"),
                "รันโค้ดเกินเวลาที่กำหนด (Execution Timeout)",
                testcase_results,
            )
        except PermissionError as exc:
            return JudgeResult(
                "System Error",
                False,
                " | ".join(tc_expected),
                _truncate_output(latest_stdout.strip() or "-"),
                str(exc),
                testcase_results,
            )
        except Exception as exc:  # noqa: BLE001
            return JudgeResult(
                "System Error",
                False,
                " | ".join(tc_expected),
                _truncate_output(latest_stdout.strip() or "-"),
                f"เชื่อมต่อ Piston ไม่สำเร็จ (API Timeout/Network): {exc}",
                testcase_results,
            )

        run_data = response_data.get("run", {})
        compile_data = response_data.get("compile", {})

        stdout = str(run_data.get("stdout", "") or "")
        stderr = str(run_data.get("stderr", "") or "")
        compile_stderr = str(compile_data.get("stderr", "") or "")
        signal = str(run_data.get("signal", "") or "")
        code_exit = int(run_data.get("code", 0) or 0)
        latest_stdout = stdout

        if compile_stderr:
            return JudgeResult("Compile Error", False, " | ".join(tc_expected), _truncate_output(stdout.strip() or "-"), _truncate_output(compile_stderr), testcase_results)

        if "killed" in signal.lower() or code_exit == 137 or "memory" in stderr.lower():
            return JudgeResult(
                "Memory Error",
                False,
                " | ".join(tc_expected),
                _truncate_output(stdout.strip() or "-"),
                f"หน่วยความจำเกิน {memory_limit} MB หรือเกิด Memory Error",
                testcase_results,
            )

        if stderr:
            return JudgeResult("Runtime Error", False, " | ".join(tc_expected), _truncate_output(stdout.strip() or "-"), _truncate_output(stderr), testcase_results)

        passed = _is_match(stdout, list(tc_expected), compare_mode=compare_mode, tolerance=tolerance)
        testcase_results.append(TestcaseResult(index=index, passed=passed, expected=" | ".join(tc_expected), got=_truncate_output(stdout.strip())))

        if not passed:
            return JudgeResult(
                "Wrong Answer",
                False,
                " | ".join(tc_expected),
                _truncate_output(stdout.strip() or "-"),
                "ผลลัพธ์ไม่ตรงกับที่กำหนด",
                testcase_results,
            )

    return JudgeResult("Accepted", True, " | ".join(accepted_outputs), _truncate_output(latest_stdout.strip() or "-"), "-", testcase_results)


class JudgeQueueWorker:
    """queue worker กัน burst traffic และ timeout cascade"""

    def __init__(self, worker_count: int = 2) -> None:
        self.worker_count = worker_count
        self.queue: asyncio.Queue[JudgeJob] = asyncio.Queue(maxsize=200)
        self._workers: list[asyncio.Task[Any]] = []

    async def start(self) -> None:
        if self._workers:
            return
        self._workers = [asyncio.create_task(self._worker_loop(), name=f"judge-worker-{i}") for i in range(self.worker_count)]

    async def stop(self) -> None:
        for task in self._workers:
            task.cancel()
        self._workers.clear()

    async def submit(self, language: str, code: str, task: dict[str, Any]) -> JudgeResult:
        if not self._workers:
            await self.start()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[JudgeResult] = loop.create_future()
        await self.queue.put(JudgeJob(language=language, code=code, task=task, future=future))
        return await future

    async def _worker_loop(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                result = await check_code(language=job.language, code=job.code, task=job.task)
                if not job.future.done():
                    job.future.set_result(result)
            except Exception as exc:  # noqa: BLE001
                if not job.future.done():
                    job.future.set_result(JudgeResult("System Error", False, "-", "-", str(exc), []))
            finally:
                self.queue.task_done()

# ===== Smart Judge (local, no external API) =====

def normalize_code(code: str) -> str:
    return "".join((code or "").strip().lower().replace(";", "").split())


def check_forbidden(code: str, task: dict[str, Any]) -> bool:
    forbidden = task.get("forbidden_keywords", []) or []
    return any(k in code for k in forbidden)


def check_keywords(code: str, task: dict[str, Any]) -> int:
    required = task.get("required_keywords", []) or []
    if not required:
        return 20
    matched = sum(1 for k in required if k in code)
    return int((matched / max(1, len(required))) * 20)


def check_similarity(code: str, task: dict[str, Any]) -> int:
    accepted = task.get("accepted_answers") or task.get("accepted_outputs") or []
    if not accepted:
        return 0
    c = normalize_code(code)
    best = 0.0
    for ans in accepted:
        a = normalize_code(str(ans))
        if not a:
            continue
        same = sum(1 for i, ch in enumerate(c[: len(a)]) if i < len(a) and ch == a[i])
        ratio = same / max(len(c), len(a), 1)
        best = max(best, ratio)
    return int(best * 60)


def check_structure(code: str, lang: str) -> int:
    score = 20
    if lang == "c":
        if code.count("{") != code.count("}"):
            score -= 10
        lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
        for line in lines:
            if any(line.startswith(k) for k in ["if", "for", "while", "int main", "#include"]):
                continue
            if not line.endswith((";", "}", "{")):
                score -= 2
    else:
        lines = [ln.rstrip() for ln in code.splitlines() if ln.strip()]
        for ln in lines:
            if any(ln.strip().startswith(k) for k in ["if ", "for ", "while ", "def "]) and not ln.strip().endswith(":"):
                score -= 5
    return max(0, score)


def judge(user_code: str, lang: str, task: dict[str, Any]) -> dict[str, Any]:
    if check_forbidden(user_code, task):
        return {"status": "forbidden", "score": 0, "keyword_score": 0, "similarity_score": 0, "structure_score": 0, "matched_answer": "", "message": "🚫 ตรวจพบโค้ดที่ไม่อนุญาต", "full_code": user_code}
    keyword_score = check_keywords(user_code, task)
    similarity_score = check_similarity(user_code, task)
    structure_score = check_structure(user_code, lang)
    score = keyword_score + similarity_score + structure_score
    pass_score = int(task.get("pass_score", 70))
    status = "pass" if score >= pass_score else "fail"
    return {
        "status": status,
        "score": score,
        "keyword_score": keyword_score,
        "similarity_score": similarity_score,
        "structure_score": structure_score,
        "matched_answer": (task.get("accepted_answers") or [""])[0],
        "message": "✅ ถูกต้อง!" if status == "pass" else "❌ ยังไม่ถูกต้อง",
        "full_code": user_code,
    }
