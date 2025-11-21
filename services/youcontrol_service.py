import httpx
import asyncio
from typing import List
from core.config import settings  # Імпортуємо налаштування
from schemas.youcontrol_schema import CheckResult

# Ключ беремо з конфігу, а не хардкодимо
API_KEY = settings.YOUCONTROL_API_KEY
BASE_URL = "https://api.youscore.com.ua/v1"
HEADERS = {
    "apiKey": API_KEY,
    "Accept": "application/json"
}

ENDPOINTS = {
    "/individualsSsuWantedAndTraitorPersons": "🔴 СБУ: Зрадники та Розшук",
    "/ruswarcriminals": "🔴 Реєстр воєнних злочинців РФ",
    "/generalprosecutor24febsuspect": "Підозрювані магістральної справи '24 лютого'",
    "/myrotvorets": "🔴 Центр 'Миротворець'",
    "/corruptedPersons": "🟠 Реєстр корупціонерів",
    "/individualsRnboSanctions": "🟠 Санкції РНБО",
    "/individualsGlobalSanctionsLists" : "Перевірка Міжнародних санкцій",
    "/lustratedPersons": "🟠 Люстровані особи",
    "/individualsRelatedPersons" : "Пов’язані з фізичною особою компанії та ФОП",
    "/wantedOrDisappearedPersons": "🟠 Розшук МВС",
    "/individualsCourtCasesToBeHeard": "Судові справи, призначені до розгляду",
}


async def _fetch(client: httpx.AsyncClient, endpoint: str, params: dict, source_name: str) -> CheckResult:
    try:
        response = await client.get(f"{BASE_URL}{endpoint}", params=params, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            is_match = False
            count = 0

            if isinstance(data, list) and len(data) > 0:
                is_match = True
                count = len(data)
            elif isinstance(data, dict) and data:
                # Додаткова перевірка для специфічних відповідей
                if len(data) > 0:
                    is_match = True
                    count = 1

            return CheckResult(source_name=source_name, match_found=is_match, details_count=count,
                               raw_data=data if is_match else [])
        return CheckResult(source_name=source_name, match_found=False, details_count=0, raw_data=[])
    except Exception as e:
        # Тут краще додати логування
        print(f"Error checking {source_name}: {e}")
        return CheckResult(source_name=source_name, match_found=False, details_count=0, raw_data=[])


async def check_candidate(surname: str, name: str, patronymic: str) -> dict:
    params = {"surname": surname, "firstname": name, "patronymic": patronymic}

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [
            _fetch(client, endpoint, params, name)
            for endpoint, name in ENDPOINTS.items()
        ]
        results = await asyncio.gather(*tasks)

    return _format_report(surname, name, patronymic, results)


def _format_report(s, n, p, results: List[CheckResult]) -> dict:
    # логіка формування JSON звіту
    report = {
        "candidate": f"{s} {n} {p}",
        "risk_summary": "CLEAN",
        "hits": []
    }

    found_critical = False
    found_warning = False

    for res in results:
        if res.match_found:
            if "🔴" in res.source_name: found_critical = True
            if "🟠" in res.source_name: found_warning = True

            report['hits'].append({
                "list": res.source_name,
                "records_found": res.details_count,
                "sample": res.raw_data[:2]
            })

    if found_critical:
        report['risk_summary'] = "CRITICAL 🔴"
    elif found_warning:
        report['risk_summary'] = "WARNING 🟠"

    return report
