"""Smart Judge แบบ static ไม่เรียก API ภายนอก"""

from __future__ import annotations

import asyncio
import difflib
import math
import re
from dataclasses import dataclass
from typing import Any


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


def _normalize_text(text: str, ignore_case: bool = True, strip_all_whitespace: bool = False) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if strip_all_whitespace:
        cleaned = "\n".join(" ".join(line.split()) for line in cleaned.split("\n"))
    else:
        cleaned = "\n".join(line.strip() for line in cleaned.split("\n"))
    return cleaned.lower() if ignore_case else cleaned


def _is_match(actual: str, accepted_outputs: list[str], compare_mode: str = "normalized", tolerance: float = 1e-6) -> bool:
    if compare_mode == "float_tolerance":
        for expected in accepted_outputs:
            try:
                if math.isclose(float(actual.strip()), float(str(expected).strip()), rel_tol=tolerance, abs_tol=tolerance):
                    return True
            except ValueError:
                continue
        return False
    if compare_mode == "exact":
        return actual in accepted_outputs
    if compare_mode == "regex":
        return any(re.fullmatch(pattern, actual.strip(), flags=re.IGNORECASE) for pattern in accepted_outputs)
    return any(_normalize_text(actual, True, True) == _normalize_text(item, True, True) for item in accepted_outputs)


def normalize_code(code: str) -> str:
    text = _normalize_text(code, ignore_case=True, strip_all_whitespace=True)
    text = text.replace(";", "").replace('"', "'")
    return text


def auto_fix_user_code(code: str, lang: str) -> str:
    fixed = (code or "").strip()
    if lang == "c":
        fixed = re.sub(r"#include\s*<[^>]+>", "", fixed)
        fixed = re.sub(r"int\s+main\s*\([^)]*\)\s*\{", "", fixed)
        fixed = fixed.replace("return 0;", "")
        fixed = fixed.replace("}", "")
    return fixed.strip()


def assemble_code(user_code: str, lang: str) -> str:
    if lang == "c":
        return "#include <stdio.h>\n#include <stdlib.h>\nint main(){\n" + user_code + "\nreturn 0;\n}\n"
    return user_code


def check_forbidden(code: str, task: dict[str, Any], lang: str = "") -> tuple[bool, list[str]]:
    base_c = ["system(", "exec(", "fork(", "popen(", "execlp("]
    base_py = ["os.system", "subprocess", "__import__", "exec(", "eval(", "open(", "socket", "requests", "urllib"]
    extra = task.get("forbidden_keywords", []) or []
    pool = (base_c if lang == "c" else base_py) + list(extra)
    found = [k for k in pool if k and k in code]
    return (len(found) > 0), found


def check_keywords(code: str, task: dict[str, Any]) -> tuple[int, list[str]]:
    required = task.get("required_keywords", []) or []
    if not required:
        return 20, []
    missing = [k for k in required if k not in code]
    score = int(((len(required) - len(missing)) / max(1, len(required))) * 20)
    return score, missing


def check_similarity(code: str, task: dict[str, Any]) -> tuple[int, str, float]:
    accepted = task.get("accepted_answers") or task.get("accepted_outputs") or []
    if not accepted:
        return 0, "", 0.0
    src = normalize_code(code)
    best_ratio = 0.0
    best_answer = str(accepted[0])
    for answer in accepted:
        ratio = difflib.SequenceMatcher(a=src, b=normalize_code(str(answer))).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_answer = str(answer)
    return round(best_ratio * 60), best_answer, best_ratio


def check_structure(code: str, lang: str) -> tuple[int, list[str]]:
    issues: list[str] = []
    score = 20
    if lang == "c":
        if code.count("{") != code.count("}"):
            score -= 10
            issues.append("วงเล็บปีกกาไม่สมดุล")
        for line in [ln.strip() for ln in code.splitlines() if ln.strip()]:
            if any(line.startswith(k) for k in ["if", "for", "while", "#include", "int main"]) or line.endswith(("{", "}")):
                continue
            if not line.endswith(";"):
                score -= 2
                issues.append(f"บรรทัดควรลงท้าย ; : {line[:30]}")
    else:
        for line in [ln.strip() for ln in code.splitlines() if ln.strip()]:
            if any(line.startswith(k) for k in ["if ", "for ", "while ", "def "]) and not line.endswith(":"):
                score -= 5
                issues.append(f"บรรทัดควรลงท้าย : {line[:30]}")
    return max(0, score), issues


def judge(user_code: str, lang: str, task: dict[str, Any]) -> dict[str, Any]:
    fixed = auto_fix_user_code(user_code, lang)
    full_code = assemble_code(fixed, lang)
    is_forbidden, forbidden = check_forbidden(full_code, task, lang)
    if is_forbidden:
        return {"status": "forbidden", "score": 0, "keyword_score": 0, "similarity_score": 0, "structure_score": 0, "matched_answer": "", "missing_keywords": [], "forbidden_found": forbidden, "structure_issues": [], "message": "🚫 ตรวจพบโค้ดที่ไม่อนุญาต", "full_code": full_code, "fixed_user_code": fixed}

    keyword_score, missing = check_keywords(full_code, task)
    similarity_score, matched, _ = check_similarity(fixed, task)
    structure_score, structure_issues = check_structure(full_code, lang)
    score = keyword_score + similarity_score + structure_score
    pass_score = int(task.get("pass_score", 70))
    status = "pass" if score >= pass_score else "fail"
    message = "✅ ถูกต้อง! ยอดเยี่ยมมาก" if status == "pass" else "❌ ยังไม่ถูกต้อง"
    return {"status": status, "score": score, "keyword_score": keyword_score, "similarity_score": similarity_score, "structure_score": structure_score, "matched_answer": matched, "missing_keywords": missing, "forbidden_found": forbidden, "structure_issues": structure_issues, "message": message, "full_code": full_code, "fixed_user_code": fixed}


def precheck_keywords(code: str, task: dict[str, Any]) -> tuple[bool, str]:
    required = task.get("required_keywords", []) or []
    if required and not any(k in code for k in required):
        return False, f"⚠️ คุณลืมใช้ {required[0]}"
    forbidden = task.get("forbidden_keywords", []) or []
    found = [k for k in forbidden if k and k in code]
    if found:
        return False, f"⚠️ ห้ามใช้คีย์เวิร์ด: {', '.join(found)}"
    return True, ""


async def _execute_with_retry(**_: Any) -> dict[str, Any]:
    raise RuntimeError("Static judge mode does not support code execution API")


async def check_code(language: str, code: str, task: dict[str, Any]) -> JudgeResult:
    try:
        await _execute_with_retry(language=language, code=code, stdin="", timeout_sec=int(task.get("time_limit", 2)))
    except PermissionError as exc:
        return JudgeResult("System Error", False, "-", "-", str(exc), [])
    except RuntimeError:
        pass
    except Exception:
        pass
    out = judge(code, language, task)
    passed = out["status"] == "pass"
    verdict = "Accepted" if passed else ("Forbidden" if out["status"] == "forbidden" else "Wrong Answer")
    return JudgeResult(verdict=verdict, passed=passed, expected_output=out.get("matched_answer", "-"), your_output=out.get("fixed_user_code", "-"), error_message=out.get("message", "-"), testcase_results=[])


class JudgeQueueWorker:
    def __init__(self, worker_count: int = 2) -> None:
        self.worker_count = worker_count
        self.queue: asyncio.Queue[JudgeJob] = asyncio.Queue(maxsize=200)
        self._workers: list[asyncio.Task[Any]] = []

    async def start(self) -> None:
        if self._workers:
            return
        self._workers = [asyncio.create_task(self._worker_loop()) for _ in range(self.worker_count)]

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
                result = await check_code(job.language, job.code, job.task)
                if not job.future.done():
                    job.future.set_result(result)
            except Exception as exc:  # noqa: BLE001
                if not job.future.done():
                    job.future.set_result(JudgeResult("System Error", False, "-", "-", str(exc), []))
            finally:
                self.queue.task_done()
