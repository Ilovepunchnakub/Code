"""เครื่องมือประกอบโค้ดจาก template mode"""

from __future__ import annotations


def build_full_code(language: str, logic_code: str, template_type: str = "") -> str:
    code = logic_code.strip()
    if language == "c" or template_type == "c_main":
        return (
            "#include <stdio.h>\n"
            "int main(){\n"
            f"    {code}\n"
            "    return 0;\n"
            "}\n"
        )
    return code


def normalize_code(text: str) -> str:
    return "".join((text or "").lower().split())


def match_accepted_code(submitted_full_code: str, accepted_codes: list[str]) -> bool:
    normalized = normalize_code(submitted_full_code)
    return any(normalized == normalize_code(item) for item in accepted_codes if item)
