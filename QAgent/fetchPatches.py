import argparse
import csv
import html
import re
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup, NavigableString, Tag


def read_versions(version_file: str) -> list[str]:
    """
    patch_version.txt에서 패치 버전 목록을 읽고,
    공백 제거 + 중복 제거를 수행한다.
    순서는 유지한다.
    """
    path = Path(version_file)

    if not path.exists():
        raise FileNotFoundError(f"버전 파일을 찾을 수 없습니다: {version_file}")

    raw_versions = [
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]

    seen = set()
    versions = []

    for version in raw_versions:
        if version in seen:
            continue
        seen.add(version)
        versions.append(version)

    print(f"[INFO] 입력 버전 수: {len(raw_versions)}")
    print(f"[INFO] 중복 제거 후 버전 수: {len(versions)}")

    return versions


def normalize_page_name(version: str) -> str:
    """
    26.13 -> V26.13
    V26.13 -> V26.13
    """
    version = version.strip()

    if version.upper().startswith("V"):
        return version

    return f"V{version}"


def fetch_patch_html(
    session: requests.Session,
    version: str,
    delay: float = 0.7,
    max_retries: int = 3,
) -> tuple[str, Optional[str]]:
    """
    MediaWiki API로 패치 HTML을 가져온다.

    return:
        ("success", html_text)
        ("missing", None)
        ("failed", error_message)
    """
    page_name = normalize_page_name(version)
    api_url = "https://wiki.leagueoflegends.com/en-us/api.php"

    params = {
        "action": "parse",
        "page": page_name,
        "prop": "text",
        "format": "json",
        "formatversion": "2",
        "disablelimitreport": "1",
    }

    headers = {
        "User-Agent": "LoLPatchParser/1.0 school-project",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    }

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(delay)

            response = session.get(
                api_url,
                params=params,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 404:
                return "missing", None

            response.raise_for_status()

            data = response.json()

            if "error" in data:
                code = data["error"].get("code", "")
                info = data["error"].get("info", "")

                if code in {"missingtitle", "invalidtitle"}:
                    return "missing", info

                return "failed", f"{code}: {info}"

            html_text = data.get("parse", {}).get("text")

            if not html_text:
                return "failed", "API 응답에 parse.text가 없습니다."

            return "success", html_text

        except requests.exceptions.HTTPError as e:
            last_error = f"HTTPError: {e}"

            # 429, 500, 502, 503 같은 경우 재시도
            status_code = getattr(e.response, "status_code", None)

            if status_code in {429, 500, 502, 503, 504}:
                time.sleep(delay * attempt * 3)
                continue

            return "failed", last_error

        except Exception as e:
            last_error = str(e)
            time.sleep(delay * attempt * 2)

    return "failed", last_error


def clean_text(node: Tag | str) -> str:
    """Extract normalized plain text from a BeautifulSoup node or string."""
    if isinstance(node, str):
        raw = node
    else:
        raw = node.get_text(" ", strip=True)

    raw = html.unescape(raw)
    raw = raw.replace("\xa0", " ")
    raw = raw.replace("\u200b", "")
    raw = raw.replace("⇒", "=>")

    # 18.<small>5</small> -> 18.5 보정
    raw = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", raw)

    # 여러 공백 정리
    raw = re.sub(r"\s+", " ", raw)

    return raw.strip()


def direct_text_without_nested_ul(li: Tag) -> str:
    """
    li 내부에서 하위 ul 텍스트는 제외하고 현재 li의 직접 텍스트만 추출.
    """
    parts = []

    for child in li.contents:
        if isinstance(child, NavigableString):
            parts.append(str(child))

        elif isinstance(child, Tag):
            if child.name == "ul":
                continue

            parts.append(child.get_text(" ", strip=True))

    return clean_text(" ".join(parts))


def cleanup_target_name(target: Optional[str]) -> Optional[str]:
    """Normalize a patch target name and strip boilerplate suffixes."""
    if not target:
        return target

    target = clean_text(target)

    # Locke - New Champion -> Locke
    target = re.sub(
        r"\s*-\s*New Champion\s*$",
        "",
        target,
        flags=re.IGNORECASE,
    )

    return target.strip()


def find_main_content(soup: BeautifulSoup) -> Tag:
    """Return the main MediaWiki parser output node when available."""
    selectors = [
        "#mw-content-text .mw-parser-output",
        ".mw-parser-output",
    ]

    for selector in selectors:
        content = soup.select_one(selector)

        if content:
            return content

    return soup


def get_heading_wrapper(heading: Tag) -> Tag:
    """
    MediaWiki는 보통 이런 구조다.

    <div class="mw-heading mw-heading3">
        <h3 id="Champions">Champions</h3>
    </div>

    따라서 h3의 다음 sibling이 아니라,
    h3를 감싼 div의 다음 sibling부터 봐야 한다.
    """
    parent = heading.parent

    if parent and isinstance(parent, Tag) and "mw-heading" in parent.get("class", []):
        return parent

    return heading


def iter_section_nodes(start_heading: Tag, stop_heading_levels: set[str]):
    """Yield sibling nodes in a section until a stopping heading level."""
    start_node = get_heading_wrapper(start_heading)

    for node in start_node.next_siblings:
        if isinstance(node, NavigableString):
            continue

        if not isinstance(node, Tag):
            continue

        heading = node.find(["h2", "h3"], recursive=False)

        if heading and heading.name in stop_heading_levels:
            break

        yield node


def canonical_section_name(text: str) -> Optional[str]:
    """
    챔피언/아이템 섹션만 통과시킨다.

    오래된 문서에서 Champion, Champions, Item, Items처럼
    약간 다르게 나올 가능성을 고려한다.
    """
    normalized = clean_text(text).lower()

    if normalized in {"champion", "champions"}:
        return "Champions"

    if normalized in {"item", "items"}:
        return "Items"

    return None


def is_probable_change_text(text: str) -> bool:
    """Heuristically decide whether text looks like a balance change."""
    lower = text.lower()

    keywords = [
        "increased",
        "reduced",
        "changed",
        "adjusted",
        "fixed",
        "disabled",
        "removed",
        "added",
        "now ",
        "new:",
        "tier:",
        "cooldown",
        "damage",
        "health",
        "mana",
        "armor",
        "magic resistance",
        "attack damage",
        "ability power",
        "ratio",
        "duration",
        "cost",
        "range",
        "speed",
        "threshold",
        "grants",
    ]

    return len(text) >= 5 and any(keyword in lower for keyword in keywords)


def classify_change_type(text: str) -> str:
    """Classify a patch-note sentence as buff, nerf, new, disabled, or bugfix."""
    lower = text.lower()

    if "bug fix" in lower or "fixed a bug" in lower:
        return "bugfix"

    if "disabled" in lower:
        return "disabled"

    if "new:" in lower or "new champion" in lower:
        return "new"

    # 쿨타임/마나/코스트 감소는 보통 버프
    if "cooldown reduced" in lower or "reduced cooldown" in lower:
        return "buff"

    if "cost reduced" in lower or "mana cost reduced" in lower:
        return "buff"

    if "increased" in lower:
        # 코스트/쿨타임 증가는 보통 너프
        if "cooldown" in lower or "cost" in lower or "mana cost" in lower:
            return "nerf"

        return "buff"

    if "reduced" in lower:
        return "nerf"

    if "changed" in lower or "adjusted" in lower:
        return "adjustment"

    if "added" in lower or "removed" in lower or "now" in lower:
        return "adjustment"

    if "=>" in text:
        return "numeric_change"

    return "other"


def extract_old_new_values(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    old_value, new_value 추출.

    예:
    - increased to 15% from 10%
    - Armor reduced to 8 from 10.
    - Tier: Gold => Prismatic
    """
    text = clean_text(text)

    pattern_to_from = re.search(
        r"\b(?:increased|reduced|changed|adjusted)\s+to\s+(.+?)\s+from\s+(.+?)(?:\.|$)",
        text,
        flags=re.IGNORECASE,
    )

    if pattern_to_from:
        new_value = pattern_to_from.group(1).strip()
        old_value = pattern_to_from.group(2).strip()

        return old_value, new_value

    pattern_arrow_with_label = re.search(
        r"^[^:]+:\s*(.+?)\s*=>\s*(.+?)(?:\.|$)",
        text,
        flags=re.IGNORECASE,
    )

    if pattern_arrow_with_label:
        old_value = pattern_arrow_with_label.group(1).strip()
        new_value = pattern_arrow_with_label.group(2).strip()

        return old_value, new_value

    pattern_arrow = re.search(
        r"(.+?)\s*=>\s*(.+?)(?:\.|$)",
        text,
        flags=re.IGNORECASE,
    )

    if pattern_arrow:
        old_value = pattern_arrow.group(1).strip()
        new_value = pattern_arrow.group(2).strip()

        return old_value, new_value

    return None, None


def flatten_li(li: Tag, prefix: Optional[str] = None) -> list[dict]:
    """
    중첩된 ul/li 구조를 분석용 row로 펼친다.

    예:
    Aphelios
      Calibrum
        Bonus AD ratio increased...

    결과:
    target = Aphelios
    subtarget = Calibrum
    change_text = Bonus AD ratio increased...
    """
    rows = []

    current_text = direct_text_without_nested_ul(li)
    child_uls = li.find_all("ul", recursive=False)

    if not child_uls:
        if current_text:
            rows.append(
                {
                    "subtarget": prefix,
                    "change_text": current_text,
                }
            )

        return rows

    # 하위 목록이 있어도 현재 문장 자체가 변경사항이면 저장
    if current_text and is_probable_change_text(current_text):
        rows.append(
            {
                "subtarget": prefix,
                "change_text": current_text,
            }
        )

    if current_text:
        next_prefix = current_text if not prefix else f"{prefix} > {current_text}"
    else:
        next_prefix = prefix

    for ul in child_uls:
        for child_li in ul.find_all("li", recursive=False):
            rows.extend(flatten_li(child_li, next_prefix))

    return rows


def parse_patch_html(html_text: str, version: str) -> list[dict]:
    """Parse one LoL wiki patch page into normalized change rows."""
    soup = BeautifulSoup(html_text, "lxml")
    content = find_main_content(soup)

    rows = []

    for heading in content.find_all(["h2", "h3"]):
        section = canonical_section_name(clean_text(heading))

        if section is None:
            continue

        current_target = None

        # h3 Champions/Items는 다음 h2/h3 전까지
        # h2 Champions/Items는 다음 h2 전까지
        if heading.name == "h3":
            stop_levels = {"h2", "h3"}
        else:
            stop_levels = {"h2"}

        for node in iter_section_nodes(heading, stop_levels):
            if not isinstance(node, Tag):
                continue

            # <dl><dt>Aphelios</dt></dl>
            if node.name == "dl":
                dt = node.find("dt")

                if dt:
                    current_target = cleanup_target_name(clean_text(dt))

                continue

            # <ul><li>...</li></ul>
            if node.name == "ul":
                for li in node.find_all("li", recursive=False):
                    flattened_items = flatten_li(li)

                    for item in flattened_items:
                        change_text = item["change_text"]

                        if not change_text:
                            continue

                        old_value, new_value = extract_old_new_values(change_text)

                        rows.append(
                            {
                                "patch_version": version,
                                "page_name": normalize_page_name(version),
                                "section": section,
                                "target": current_target,
                                "subtarget": item["subtarget"],
                                "change_text": change_text,
                                "change_type": classify_change_type(change_text),
                                "old_value": old_value,
                                "new_value": new_value,
                            }
                        )

    # 완전 중복 제거
    unique_rows = []
    seen = set()

    for row in rows:
        key = tuple(row.items())

        if key in seen:
            continue

        seen.add(key)
        unique_rows.append(row)

    return unique_rows


def save_rows_csv(rows: list[dict], output_path: Path) -> None:
    """Save parsed patch rows to a UTF-8-SIG CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        pd.DataFrame(
            columns=[
                "patch_version",
                "page_name",
                "section",
                "target",
                "subtarget",
                "change_text",
                "change_type",
                "old_value",
                "new_value",
            ]
        ).to_csv(output_path, index=False, encoding="utf-8-sig")
        return

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def save_logs_csv(logs: list[dict], output_path: Path) -> None:
    """Save patch fetch status logs to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(logs)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def save_jsonl(rows: list[dict], output_path: Path) -> None:
    """Save parsed patch rows as newline-delimited JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_json(
        output_path,
        orient="records",
        lines=True,
        force_ascii=False,
    )


def run_batch(
    version_file: str,
    out_dir: str,
    delay: float,
    max_retries: int,
    checkpoint_every: int,
    limit: Optional[int] = None,
) -> None:
    """Fetch, parse, and persist patch notes for a version list."""
    versions = read_versions(version_file)

    if limit is not None:
        versions = versions[:limit]
        print(f"[INFO] 테스트 제한 적용: {limit}개만 처리")

    out_path = Path(out_dir)
    output_csv = out_path / "lol_patch_champions_items.csv"
    output_jsonl = out_path / "lol_patch_champions_items.jsonl"
    log_csv = out_path / "lol_patch_fetch_log.csv"

    all_rows = []
    logs = []

    session = requests.Session()

    total = len(versions)

    for index, version in enumerate(versions, start=1):
        print(f"\n[{index}/{total}] {version} 처리 중...")

        status, result = fetch_patch_html(
            session=session,
            version=version,
            delay=delay,
            max_retries=max_retries,
        )

        if status == "missing":
            logs.append(
                {
                    "patch_version": version,
                    "page_name": normalize_page_name(version),
                    "status": "missing",
                    "parsed_rows": 0,
                    "message": result or "page not found",
                }
            )
            print(f"[MISS] {version}: 페이지 없음")
            continue

        if status == "failed":
            logs.append(
                {
                    "patch_version": version,
                    "page_name": normalize_page_name(version),
                    "status": "failed",
                    "parsed_rows": 0,
                    "message": result,
                }
            )
            print(f"[FAIL] {version}: {result}")
            continue

        html_text = result
        rows = parse_patch_html(html_text, version)

        all_rows.extend(rows)

        row_count = len(rows)

        if row_count == 0:
            parse_status = "success_no_rows"
            message = "Champions/Items 섹션이 없거나 구조가 예상과 다름"
        else:
            parse_status = "success"
            message = ""

        logs.append(
            {
                "patch_version": version,
                "page_name": normalize_page_name(version),
                "status": parse_status,
                "parsed_rows": row_count,
                "message": message,
            }
        )

        print(f"[OK] {version}: {row_count}개 변경사항 추출")

        # 중간 저장
        if checkpoint_every > 0 and index % checkpoint_every == 0:
            print("[INFO] 체크포인트 저장 중...")
            save_rows_csv(all_rows, output_csv)
            save_jsonl(all_rows, output_jsonl)
            save_logs_csv(logs, log_csv)

    print("\n[INFO] 최종 저장 중...")

    save_rows_csv(all_rows, output_csv)
    save_jsonl(all_rows, output_jsonl)
    save_logs_csv(logs, log_csv)

    success_count = sum(1 for log in logs if log["status"] == "success")
    no_rows_count = sum(1 for log in logs if log["status"] == "success_no_rows")
    missing_count = sum(1 for log in logs if log["status"] == "missing")
    failed_count = sum(1 for log in logs if log["status"] == "failed")

    print("\n========== 결과 ==========")
    print(f"총 요청 버전 수: {len(versions)}")
    print(f"성공: {success_count}")
    print(f"성공했지만 row 없음: {no_rows_count}")
    print(f"없는 페이지: {missing_count}")
    print(f"실패: {failed_count}")
    print(f"총 추출 row 수: {len(all_rows)}")
    print(f"CSV: {output_csv}")
    print(f"JSONL: {output_jsonl}")
    print(f"LOG: {log_csv}")


def main():
    """CLI entry point for LoL wiki patch-note collection."""
    parser = argparse.ArgumentParser(
        description="LoL Wiki 패치노트에서 Champions/Items 변경사항만 일괄 수집합니다."
    )

    parser.add_argument(
        "--versions",
        default="patch_version.txt",
        help="패치 버전 목록 txt 파일 경로",
    )

    parser.add_argument(
        "--out-dir",
        default="data/processed",
        help="결과 저장 폴더",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.7,
        help="요청 간 대기 시간. 서버 부담을 줄이기 위해 너무 낮게 잡지 않는 것을 권장",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="요청 실패 시 재시도 횟수",
    )

    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="몇 개 버전마다 중간 저장할지 설정",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="테스트용 처리 개수 제한. 예: --limit 5",
    )

    args = parser.parse_args()

    run_batch(
        version_file=args.versions,
        out_dir=args.out_dir,
        delay=args.delay,
        max_retries=args.max_retries,
        checkpoint_every=args.checkpoint_every,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
