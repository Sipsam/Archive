import argparse
import json
import os
import re
import shutil
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import pandas as pd
import requests
from dotenv import load_dotenv
from qagent_core.data_pipeline.normalize_match import (
    compute_kda, extract_patch_version, extract_raw_patch_version, get_primary_perk,
    get_sub_style, map_game_version_to_patch_version, normalize_item_id,
    parse_riot_id, patch_version_mapping_rule, queue_to_battle_mode,
    safe_filename, timestamp_to_iso_kst, truthy_win,
)


# =========================================================
# 1. 기본 설정
# =========================================================

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

REGIONAL_ROUTING = "asia"
PLATFORM_ROUTING = "kr"
MATCH_COUNT_PER_PLAYER = 15
# Riot MATCH-V5 match id 목록은 여러 페이지로 나눠 가져올 수 있도록 100개 단위로 요청한다.
MATCH_ID_PAGE_SIZE = 100

# 개인 API Key 제한
LIMIT_1_SECOND = 20
WINDOW_1_SECOND = 1

LIMIT_2_MINUTES = 100
WINDOW_2_MINUTES = 120

# 실수 방지용 안전 여유
SAFE_LIMIT_2_MINUTES = 95


# =========================================================
# 1-1. 내장 아이템 ID → 이름 매핑
# =========================================================

# 외부 item_id_map.csv가 없어도 앱용 battle_logs.csv에 item0_name~item6_name을 붙이기 위한 내장 매핑입니다.
# 외부 CSV를 명시하거나 자동 탐색에서 찾으면 CSV 값이 우선 적용됩니다.
EMBEDDED_ITEM_ID_NAME_MAP: dict[int, str] = {1001: 'Boots',
 1004: 'Faerie Charm',
 1006: 'Rejuvenation Bead',
 1011: "Giant's Belt",
 1018: 'Cloak of Agility',
 1026: 'Blasting Wand',
 1027: 'Sapphire Crystal',
 1028: 'Ruby Crystal',
 1029: 'Cloth Armor',
 1031: 'Chain Vest',
 1033: 'Null-Magic Mantle',
 1036: 'Long Sword',
 1037: 'Pickaxe',
 1038: 'B. F. Sword',
 1042: 'Dagger',
 1043: 'Recurve Bow',
 1052: 'Amplifying Tome',
 1053: 'Vampiric Scepter',
 1054: "Doran's Shield",
 1055: "Doran's Blade",
 1056: "Doran's Ring",
 1057: 'Negatron Cloak',
 1058: 'Needlessly Large Rod',
 1082: 'Dark Seal',
 1083: 'Cull',
 1086: "Doran's Bow",
 1101: 'Scorchclaw Pup',
 1102: 'Gustwalker Hatchling',
 1103: 'Mosstomper Seedling',
 1111: "Jarvan I's",
 1120: "Doran's Helm",
 1500: 'Ohmwrecker (Turret Item)',
 1502: 'Reinforced Armor (Turret Item)',
 1503: "Warden's Eye",
 1506: 'Base Turret Reinforced Armor (Turret Item)',
 1507: 'Overcharged',
 1508: 'Anti-Tower Socks',
 1509: 'Gusto',
 1510: 'Phreakish Gusto',
 1511: 'Super Mech Armor',
 1512: 'Super Mech Power Field',
 1515: 'Turret Plating',
 1524: 'Crystalline Overgrowth',
 2003: 'Health Potion',
 2010: 'Total Biscuit of Everlasting Will',
 2019: 'Steel Sigil',
 2020: 'The Brutalizer',
 2021: 'Tunneler',
 2022: 'Glowing Mote',
 2031: 'Refillable Potion',
 2049: "Guardian's Amulet",
 2050: "Guardian's Shroud",
 2051: "Guardian's Horn",
 2052: 'Poro-Snax',
 2055: 'Control Ward',
 2065: "Shurelya's Battlesong",
 2138: 'Elixir of Iron',
 2139: 'Elixir of Sorcery',
 2140: 'Elixir of Wrath',
 2141: 'Cappa Juice',
 2142: 'Juice of Power',
 2143: 'Juice of Vitality',
 2144: 'Juice of Haste',
 2145: 'Lucky Dice',
 2146: 'Enhanced Lucky Dice',
 2150: 'Elixir of Skill',
 2151: 'Elixir of Avarice',
 2152: 'Elixir of Force',
 2420: "Seeker's Armguard",
 2421: 'Shattered Armguard',
 2422: 'Slightly Magical Boots',
 2501: "Overlord's Bloodmail",
 2502: 'Unending Despair',
 2503: 'Blackfire Torch',
 2504: 'Kaenic Rookern',
 2508: 'Fated Ashes',
 2510: 'Dusk and Dawn',
 2512: 'Fiendhunter Bolts',
 2517: 'Endless Hunger',
 2520: 'Bastionbreaker',
 2522: 'Actualizer',
 2523: 'Hexoptics C44',
 2524: 'Bandlepipes',
 2525: 'Protoplasm Harness',
 2526: 'Whispering Circlet',
 2530: 'Diadem of Songs',
 3003: "Archangel's Staff",
 3004: 'Manamune',
 3006: "Berserker's Greaves",
 3008: 'Gluttonous Greaves',
 3009: 'Boots of Swiftness',
 3020: "Sorcerer's Shoes",
 3024: 'Glacial Buckler',
 3026: 'Guardian Angel',
 3031: 'Infinity Edge',
 3032: 'Yun Tal Wildarrows',
 3033: 'Mortal Reminder',
 3035: 'Last Whisper',
 3036: "Lord Dominik's Regards",
 3040: "Seraph's Embrace",
 3041: "Mejai's Soulstealer",
 3042: 'Muramana',
 3044: 'Phage',
 3046: 'Phantom Dancer',
 3047: 'Plated Steelcaps',
 3050: "Zeke's Convergence",
 3051: 'Hearthbound Axe',
 3053: "Sterak's Gage",
 3057: 'Sheen',
 3065: 'Spirit Visage',
 3066: 'Winged Moonplate',
 3067: 'Kindlegem',
 3068: 'Sunfire Aegis',
 3070: 'Tear of the Goddess',
 3071: 'Black Cleaver',
 3072: 'Bloodthirster',
 3073: 'Experimental Hexplate',
 3074: 'Ravenous Hydra',
 3075: 'Thornmail',
 3076: 'Bramble Vest',
 3077: 'Tiamat',
 3078: 'Trinity Force',
 3082: "Warden's Mail",
 3083: "Warmog's Armor",
 3084: 'Heartsteel',
 3085: "Runaan's Hurricane",
 3086: 'Zeal',
 3087: 'Statikk Shiv',
 3089: "Rabadon's Deathcap",
 3091: "Wit's End",
 3094: 'Rapid Firecannon',
 3097: 'Stormrazor',
 3100: 'Lich Bane',
 3102: "Banshee's Veil",
 3107: 'Redemption',
 3108: 'Fiendish Codex',
 3109: "Knight's Vow",
 3110: 'Frozen Heart',
 3111: "Mercury's Treads",
 3112: "Guardian's Orb",
 3113: 'Aether Wisp',
 3114: 'Forbidden Idol',
 3115: "Nashor's Tooth",
 3116: "Rylai's Crystal Scepter",
 3118: 'Malignance',
 3119: "Winter's Approach",
 3121: 'Fimbulwinter',
 3123: "Executioner's Calling",
 3124: "Guinsoo's Rageblade",
 3133: "Caulfield's Warhammer",
 3134: 'Serrated Dirk',
 3135: 'Void Staff',
 3137: 'Cryptbloom',
 3139: 'Mercurial Scimitar',
 3140: 'Quicksilver Sash',
 3142: "Youmuu's Ghostblade",
 3143: "Randuin's Omen",
 3144: "Scout's Slingshot",
 3145: 'Hextech Alternator',
 3146: 'Hextech Gunblade',
 3147: 'Haunting Guise',
 3152: 'Hextech Rocketbelt',
 3153: 'Blade of the Ruined King',
 3155: 'Hexdrinker',
 3156: 'Maw of Malmortius',
 3157: "Zhonya's Hourglass",
 3158: 'Ionian Boots of Lucidity',
 3161: 'Spear of Shojin',
 3165: 'Morellonomicon',
 3168: 'Immortal Path',
 3170: 'Swiftmarch',
 3171: 'Crimson Lucidity',
 3172: 'Zephyr',
 3173: 'Chainlaced Crushers',
 3174: 'Armored Advance',
 3175: "Spellslinger's Shoes",
 3177: "Guardian's Blade",
 3179: 'Umbral Glaive',
 3181: 'Hullbreaker',
 3184: "Guardian's Hammer",
 3190: 'Locket of the Iron Solari',
 3211: "Spectre's Cowl",
 3222: "Mikael's Blessing",
 3302: 'Terminus',
 3330: 'Scarecrow Effigy',
 3340: 'Stealth Ward',
 3348: 'Arcane Sweeper (Trinket)',
 3363: 'Farsight Alteration',
 3364: 'Oracle Lens',
 3400: 'Your Cut',
 3430: 'Rite of Ruin',
 3504: 'Ardent Censer',
 3508: 'Essence Reaver',
 3513: 'Eye of the Herald',
 3599: 'Black Spear',
 3742: "Dead Man's Plate",
 3748: 'Titanic Hydra',
 3801: 'Crystalline Bracer',
 3802: 'Lost Chapter',
 3803: 'Catalyst of Aeons',
 3814: 'Edge of Night',
 3865: 'World Atlas',
 3866: 'Runic Compass',
 3867: 'Bounty of Worlds',
 3869: 'Celestial Opposition',
 3870: 'Dream Maker',
 3871: "Zaz'Zak's Realmspike",
 3876: 'Solstice Sleigh',
 3877: 'Bloodsong',
 3901: 'Fire at Will',
 3902: "Death's Daughter",
 3903: 'Raise Morale',
 3916: 'Oblivion Orb',
 4003: 'Lifeline',
 4005: 'Imperial Mandate',
 4011: 'Sword of Blossoming Dawn',
 4015: 'Perplexity',
 4016: 'Wordless Promise',
 4017: 'Hellfire Hatchet',
 4401: 'Force of Nature',
 4628: 'Horizon Focus',
 4629: 'Cosmic Drive',
 4630: 'Blighting Jewel',
 4632: 'Verdant Barrier',
 4633: 'Riftmaker',
 4642: 'Bandleglass Mirror',
 4645: 'Shadowflame',
 4646: 'Stormsurge',
 6333: "Death's Dance",
 6609: 'Chempunk Chainsword',
 6610: 'Sundered Sky',
 6616: 'Staff of Flowing Water',
 6617: 'Moonstone Renewer',
 6620: 'Echoes of Helia',
 6621: 'Dawncore',
 6631: 'Stridebreaker',
 6653: "Liandry's Torment",
 6655: "Luden's Echo",
 6657: 'Rod of Ages',
 6660: "Bami's Cinder",
 6662: 'Iceborn Gauntlet',
 6664: 'Hollow Radiance',
 6665: "Jak'Sho, The Protean",
 6670: 'Noonquiver',
 6672: 'Kraken Slayer',
 6673: 'Immortal Shieldbow',
 6675: 'Navori Flickerblade',
 6676: 'The Collector',
 6690: 'Rectrix',
 6692: 'Eclipse',
 6694: "Serylda's Grudge",
 6695: "Serpent's Fang",
 6696: 'Axiom Arc',
 6697: 'Hubris',
 6698: 'Profane Hydra',
 6699: 'Voltaic Cyclosword',
 8010: "Bloodletter's Curse",
 8020: 'Abyssal Mask',
 9999: 'Scouting Ahead',
 220000: 'Stat Bonus (ARAM: Mayhem)',
 220001: 'Legendary Fighter Item',
 220002: 'Legendary Marksman Item',
 220003: 'Legendary Assassin Item',
 220004: 'Legendary Mage Item',
 220005: 'Legendary Tank Item',
 220006: 'Legendary Support Item',
 220007: 'Prismatic Item',
 223005: 'Ghostcrawlers',
 223039: "Atma's Reckoning",
 223069: 'Void Immolation',
 223185: "Guardian's Dirk",
 224004: 'Spectral Cutlass',
 224403: 'The Golden Spatula',
 226630: 'Goredrinker',
 228001: "Anathema's Chains",
 228002: "Wooglet's Witchcap",
 228009: 'Multitool',
 443054: 'Darksteel Talons',
 443055: 'Fulmination',
 443056: "Demon King's Crown",
 443058: 'Shield of Molten Stone',
 443059: 'Cloak of Starry Night',
 443060: 'Sword of the Divine',
 443061: 'Force of Entropy',
 443062: 'Sanguine Gift',
 443063: "Eleisa's Miracle",
 443064: 'Talisman of Ascension',
 443069: 'Hamstringer',
 443079: 'Turbo Chemtank',
 443080: 'Twin Mask',
 443081: 'Hexbolt Companion',
 443090: "Reaper's Toll",
 443193: 'Gargoyle Stoneplate',
 444636: 'Night Harvester',
 444637: 'Demonic Embrace',
 444644: 'Crown of the Shattered Queen',
 446632: 'Divine Sunderer',
 446656: 'Everfrost',
 446667: 'Radiant Virtue',
 446671: 'Galeforce',
 446691: 'Duskblade of Draktharr',
 446693: "Prowler's Claw",
 447100: 'Mirage Blade',
 447101: "Gambler's Blade",
 447102: 'Reality Fracture',
 447103: "Hemomancer's Helm",
 447104: 'Innervating Locket',
 447105: 'Empyrean Promise',
 447106: 'Dragonheart',
 447107: 'Decapitator',
 447108: 'Runecarver',
 447109: 'Cruelty',
 447110: 'Moonflair Spellblade',
 447112: 'Flesheater',
 447113: 'Detonation Orb',
 447114: 'Reverberation',
 447115: 'Regicide',
 447116: 'Kinkou Jitte',
 447118: "Pyromancer's Cloak",
 447119: 'Lightning Rod',
 447120: 'Diamond-Tipped Spear',
 447121: "Twilight's Edge",
 447122: 'Black Hole Gauntlet',
 447123: 'Puppeteer',
 999999: "Veigar's Talisman of Ascension"}


# =========================================================
# 2. 수집 대상 유저 목록
# =========================================================

PLAYERS = [
    # CHALLENGER
    {"tier": "CHALLENGER", "riot_id": "DNS 또이브#KR13"},
    {"tier": "CHALLENGER", "riot_id": "Calix#해 린"},
    {"tier": "CHALLENGER", "riot_id": "TOPKING#asd"},

    # GRANDMASTER
    {"tier": "GRANDMASTER", "riot_id": "jkjkjkjkk#1173"},
    {"tier": "GRANDMASTER", "riot_id": "LittlePira#1128"},
    {"tier": "GRANDMASTER", "riot_id": "Celina#샐러드"},

    # MASTER
    {"tier": "MASTER", "riot_id": "Holder#KR3"},
    {"tier": "MASTER", "riot_id": "水原铃瑞#宋岱霖の"},
    {"tier": "MASTER", "riot_id": "Faker#0409"},

    # DIAMOND
    {"tier": "DIAMOND", "riot_id": "남 이#0815"},
    {"tier": "DIAMOND", "riot_id": "백석아찌#0222"},
    {"tier": "DIAMOND", "riot_id": "100동진#KR100"},

    # EMERALD
    {"tier": "EMERALD", "riot_id": "해도토리#KR1"},
    {"tier": "EMERALD", "riot_id": "심도동#도심동"},
    {"tier": "EMERALD", "riot_id": "사 구#삼 구"},

    # PLATINUM
    {"tier": "PLATINUM", "riot_id": "역대급천재탑유망주#09년생"},
    {"tier": "PLATINUM", "riot_id": "bulgariss#KR1"},
    {"tier": "PLATINUM", "riot_id": "넌 보란듯이 예쁜 꽃 되니까#0000"},

    # GOLD
    {"tier": "GOLD", "riot_id": "아니이자식아#KR2"},
    {"tier": "GOLD", "riot_id": "조선제일검#0421"},
    {"tier": "GOLD", "riot_id": "대구여신 김민주#KR1"},
]


# =========================================================
# 3. 유틸 함수
# =========================================================





def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


















# 기존 이름 호환


# =========================================================
# 4. Rate Limiter
# =========================================================

class RiotRateLimiter:
    """
    1초 20회, 2분 100회 제한을 지키기 위한 rate limiter.
    2분 제한이 더 빡빡하므로 실제로는 2분 제한이 주로 작동한다.
    """

    def __init__(
        self,
        limit_1s: int = LIMIT_1_SECOND,
        window_1s: int = WINDOW_1_SECOND,
        limit_2m: int = SAFE_LIMIT_2_MINUTES,
        window_2m: int = WINDOW_2_MINUTES,
    ):
        self.limit_1s = limit_1s
        self.window_1s = window_1s
        self.limit_2m = limit_2m
        self.window_2m = window_2m

        self.calls_1s = deque()
        self.calls_2m = deque()

    def wait(self) -> None:
        while True:
            now = time.time()

            while self.calls_1s and now - self.calls_1s[0] >= self.window_1s:
                self.calls_1s.popleft()

            while self.calls_2m and now - self.calls_2m[0] >= self.window_2m:
                self.calls_2m.popleft()

            wait_times = []

            if len(self.calls_1s) >= self.limit_1s:
                wait_times.append(self.window_1s - (now - self.calls_1s[0]))

            if len(self.calls_2m) >= self.limit_2m:
                wait_times.append(self.window_2m - (now - self.calls_2m[0]))

            if not wait_times:
                self.calls_1s.append(now)
                self.calls_2m.append(now)
                return

            sleep_for = max(0.1, max(wait_times))
            print(f"[RATE] 제한 보호 대기: {sleep_for:.1f}초")
            time.sleep(sleep_for)


# =========================================================
# 5. Riot API Client
# =========================================================

class RiotApiClient:
    def __init__(
        self,
        api_key: Optional[str],
        regional_routing: str = REGIONAL_ROUTING,
        platform_routing: str = PLATFORM_ROUTING,
    ):
        if not api_key:
            raise RuntimeError(
                "RIOT_API_KEY가 없습니다. 프로젝트 루트에 .env 파일을 만들고 "
                "RIOT_API_KEY=RGAPI-... 형태로 저장하세요."
            )

        self.api_key = api_key
        self.regional_routing = regional_routing
        self.platform_routing = platform_routing
        self.session = requests.Session()
        self.limiter = RiotRateLimiter()

    def headers(self) -> dict[str, str]:
        return {
            "X-Riot-Token": self.api_key,
            "Accept": "application/json",
        }

    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Any:
        last_error = None

        for attempt in range(1, max_retries + 1):
            self.limiter.wait()

            response = self.session.get(
                url,
                headers=self.headers(),
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after is not None:
                    wait_time = int(retry_after) + 1
                else:
                    wait_time = 10 * attempt

                print(f"[429] Rate limit. {wait_time}초 대기 후 재시도")
                time.sleep(wait_time)
                continue

            if response.status_code in {500, 502, 503, 504}:
                wait_time = 5 * attempt
                print(f"[WARN] 서버 오류 {response.status_code}. {wait_time}초 대기 후 재시도")
                time.sleep(wait_time)
                continue

            try:
                body = response.json()
            except Exception:
                body = response.text

            last_error = {
                "status_code": response.status_code,
                "url": response.url,
                "body": body,
            }

            raise RuntimeError(json.dumps(last_error, ensure_ascii=False, indent=2))

        raise RuntimeError(f"요청 실패: {last_error}")

    # -----------------------------------------------------
    # ACCOUNT-V1
    # -----------------------------------------------------

    def get_account_by_riot_id(self, riot_id: str) -> dict[str, Any]:
        game_name, tag_line = parse_riot_id(riot_id)

        encoded_game_name = quote(game_name, safe="")
        encoded_tag_line = quote(tag_line, safe="")

        url = (
            f"https://{self.regional_routing}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
        )

        return self.get(url)

    def get_account_by_puuid(self, puuid: str) -> dict[str, Any]:
        url = (
            f"https://{self.regional_routing}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-puuid/{puuid}"
        )
        return self.get(url)

    # -----------------------------------------------------
    # SUMMONER-V4
    # -----------------------------------------------------

    def get_summoner_by_id(self, encrypted_summoner_id: str) -> dict[str, Any]:
        url = (
            f"https://{self.platform_routing}.api.riotgames.com"
            f"/lol/summoner/v4/summoners/{encrypted_summoner_id}"
        )
        return self.get(url)

    # -----------------------------------------------------
    # LEAGUE-V4
    # -----------------------------------------------------

    def get_league_entries(
        self,
        queue: str,
        tier: str,
        division: str,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """
        LEAGUE-V4:
        /lol/league/v4/entries/{queue}/{tier}/{division}?page={page}
        """
        url = (
            f"https://{self.platform_routing}.api.riotgames.com"
            f"/lol/league/v4/entries/{queue}/{tier}/{division}"
        )
        return self.get(url, params={"page": page})

    def get_apex_league(self, queue: str, tier: str) -> dict[str, Any]:
        """
        CHALLENGER / GRANDMASTER / MASTER는 전용 league endpoint를 우선 사용한다.
        """
        normalized = str(tier).upper().strip()

        if normalized == "CHALLENGER":
            path = "challengerleagues"
        elif normalized == "GRANDMASTER":
            path = "grandmasterleagues"
        elif normalized == "MASTER":
            path = "masterleagues"
        else:
            raise ValueError(f"apex tier가 아닙니다: {tier}")

        url = (
            f"https://{self.platform_routing}.api.riotgames.com"
            f"/lol/league/v4/{path}/by-queue/{queue}"
        )
        return self.get(url)

    # -----------------------------------------------------
    # MATCH-V5
    # -----------------------------------------------------

    def get_match_ids_page_by_puuid(
        self,
        puuid: str,
        start: int = 0,
        count: int = MATCH_ID_PAGE_SIZE,
        queue: Optional[int] = None,
        match_type: Optional[str] = None,
    ) -> list[str]:
        """
        MATCH-V5 match id 목록을 한 페이지만 가져온다.
        """
        url = (
            f"https://{self.regional_routing}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )

        params: dict[str, Any] = {
            "start": start,
            "count": count,
        }

        if queue is not None:
            params["queue"] = queue

        if match_type is not None:
            params["type"] = match_type

        return self.get(url, params=params)

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        count: int = MATCH_COUNT_PER_PLAYER,
        queue: Optional[int] = None,
        match_type: Optional[str] = None,
        page_size: int = MATCH_ID_PAGE_SIZE,
    ) -> list[str]:
        """
        요청한 count만큼 match_id를 가져온다.
        count가 100개를 초과하면 start offset으로 여러 페이지를 조회한다.
        """
        target_count = max(int(count), 0)
        page_size = max(1, min(int(page_size), MATCH_ID_PAGE_SIZE))

        all_match_ids: list[str] = []
        seen: set[str] = set()
        start = 0

        while len(all_match_ids) < target_count:
            request_count = min(page_size, target_count - len(all_match_ids))

            print(
                f"[REQ] Match IDs page puuid={puuid[:8]}... "
                f"start={start}, count={request_count}, queue={queue}, type={match_type}"
            )

            page = self.get_match_ids_page_by_puuid(
                puuid=puuid,
                start=start,
                count=request_count,
                queue=queue,
                match_type=match_type,
            )

            if not page:
                break

            for match_id in page:
                if match_id not in seen:
                    seen.add(match_id)
                    all_match_ids.append(match_id)

            if len(page) < request_count:
                break

            start += len(page)

        return all_match_ids[:target_count]

    def get_new_match_ids_by_puuid(
        self,
        puuid: str,
        target_new_count: int,
        existing_match_ids: set[str],
        selected_this_run: set[str],
        queue: Optional[int] = None,
        match_type: Optional[str] = None,
        page_size: int = MATCH_ID_PAGE_SIZE,
        max_scan_pages: int = 30,
    ) -> dict[str, Any]:
        """
        최근 경기 목록을 훑으면서 이미 수집된 match_id는 count에 포함하지 않고,
        아직 수집하지 않은 match_id만 target_new_count개까지 반환한다.

        - existing_match_ids: 이전 실행에서 이미 detail까지 가져온 전투 기록
        - selected_this_run: 이번 실행에서 이미 다른 유저 때문에 선택된 match_id
        """
        target_new_count = max(int(target_new_count), 0)
        page_size = max(1, min(int(page_size), MATCH_ID_PAGE_SIZE))
        max_scan_pages = max(1, int(max_scan_pages))

        new_match_ids: list[str] = []
        duplicate_in_current_run: list[str] = []
        seen_candidate: set[str] = set()

        skipped_existing = 0
        skipped_current_duplicate = 0
        scanned_candidates = 0

        start = 0
        pages_scanned = 0

        while len(new_match_ids) < target_new_count and pages_scanned < max_scan_pages:
            print(
                f"[REQ] New-only Match IDs page puuid={puuid[:8]}... "
                f"start={start}, count={page_size}, queue={queue}, type={match_type}"
            )

            page = self.get_match_ids_page_by_puuid(
                puuid=puuid,
                start=start,
                count=page_size,
                queue=queue,
                match_type=match_type,
            )

            pages_scanned += 1

            if not page:
                break

            scanned_candidates += len(page)

            for match_id in page:
                if match_id in seen_candidate:
                    continue

                seen_candidate.add(match_id)

                if match_id in existing_match_ids:
                    skipped_existing += 1
                    continue

                if match_id in selected_this_run:
                    skipped_current_duplicate += 1
                    duplicate_in_current_run.append(match_id)
                    continue

                new_match_ids.append(match_id)

                if len(new_match_ids) >= target_new_count:
                    break

            if len(page) < page_size:
                break

            start += len(page)

        return {
            "match_ids": new_match_ids[:target_new_count],
            "duplicate_in_current_run": duplicate_in_current_run,
            "stats": {
                "target_new_count": target_new_count,
                "selected_new_count": len(new_match_ids[:target_new_count]),
                "skipped_existing": skipped_existing,
                "skipped_current_duplicate": skipped_current_duplicate,
                "scanned_candidates": scanned_candidates,
                "pages_scanned": pages_scanned,
                "max_scan_pages": max_scan_pages,
            },
        }

    def get_match_detail(self, match_id: str) -> dict[str, Any]:
        url = (
            f"https://{self.regional_routing}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )

        return self.get(url)



# =========================================================
# 6. Match Detail → raw battle_logs row 변환
# =========================================================





def build_battle_log_rows(
    match_detail: dict[str, Any],
    match_sources: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """
    match_detail 하나에서 참가자 10명 row 생성.
    이 단계의 row는 Riot API 중심 raw 구조이며, 이후 app-ready 변환을 다시 수행한다.
    """
    metadata = match_detail.get("metadata", {})
    info = match_detail.get("info", {})

    match_id = metadata.get("matchId")
    game_version = info.get("gameVersion")

    source_tiers = sorted({s["tier"] for s in match_sources})
    source_riot_ids = sorted({s["riot_id"] for s in match_sources})
    source_puuids = sorted({s["puuid"] for s in match_sources})

    game_start_timestamp = info.get("gameStartTimestamp")
    game_end_timestamp = info.get("gameEndTimestamp")

    rows = []

    for p in info.get("participants", []):
        kills = p.get("kills", 0)
        deaths = p.get("deaths", 0)
        assists = p.get("assists", 0)

        total_cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)

        raw_patch_version = extract_raw_patch_version(game_version)
        mapped_patch_version = map_game_version_to_patch_version(game_version)

        row = {
            # 수집 기준 정보
            "source_tiers": "|".join(source_tiers),
            "source_riot_ids": "|".join(source_riot_ids),
            "source_puuids": "|".join(source_puuids),

            # 매치 정보
            "match_id": match_id,
            "game_id": info.get("gameId"),
            "game_version": game_version,
            "original_patch_version": raw_patch_version,
            "patch_version": mapped_patch_version,
            "patch_version_mapping_rule": patch_version_mapping_rule(game_version),
            "queue_id": info.get("queueId"),
            "map_id": info.get("mapId"),
            "game_mode": info.get("gameMode"),
            "game_type": info.get("gameType"),
            "game_duration": info.get("gameDuration"),
            "game_start_timestamp": game_start_timestamp,
            "game_end_timestamp": game_end_timestamp,
            "game_start_kst": timestamp_to_iso_kst(game_start_timestamp),
            "game_end_kst": timestamp_to_iso_kst(game_end_timestamp),
            "end_of_game_result": info.get("endOfGameResult"),

            # 참가자 식별
            "participant_id": p.get("participantId"),
            "puuid": p.get("puuid"),
            "riot_id_game_name": p.get("riotIdGameName"),
            "riot_id_tagline": p.get("riotIdTagline"),
            "summoner_id": p.get("summonerId"),
            "summoner_level": p.get("summonerLevel"),

            # 팀/포지션
            "team_id": p.get("teamId"),
            "team_position": p.get("teamPosition"),
            "individual_position": p.get("individualPosition"),
            "lane": p.get("lane"),
            "role": p.get("role"),
            "win": p.get("win"),

            # 챔피언
            "champion_id": p.get("championId"),
            "champion_name": p.get("championName"),
            "champ_level": p.get("champLevel"),
            "champ_experience": p.get("champExperience"),

            # 전투 결과
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "kda": compute_kda(kills, deaths, assists),
            "double_kills": p.get("doubleKills"),
            "triple_kills": p.get("tripleKills"),
            "quadra_kills": p.get("quadraKills"),
            "penta_kills": p.get("pentaKills"),
            "first_blood_kill": p.get("firstBloodKill"),
            "first_blood_assist": p.get("firstBloodAssist"),

            # 골드/CS
            "gold_earned": p.get("goldEarned"),
            "gold_spent": p.get("goldSpent"),
            "total_minions_killed": p.get("totalMinionsKilled"),
            "neutral_minions_killed": p.get("neutralMinionsKilled"),
            "total_cs": total_cs,

            # 데미지
            "total_damage_dealt": p.get("totalDamageDealt"),
            "total_damage_dealt_to_champions": p.get("totalDamageDealtToChampions"),
            "physical_damage_dealt_to_champions": p.get("physicalDamageDealtToChampions"),
            "magic_damage_dealt_to_champions": p.get("magicDamageDealtToChampions"),
            "true_damage_dealt_to_champions": p.get("trueDamageDealtToChampions"),
            "total_damage_taken": p.get("totalDamageTaken"),
            "physical_damage_taken": p.get("physicalDamageTaken"),
            "magic_damage_taken": p.get("magicDamageTaken"),
            "true_damage_taken": p.get("trueDamageTaken"),
            "damage_self_mitigated": p.get("damageSelfMitigated"),

            # 오브젝트
            "turret_kills": p.get("turretKills"),
            "turret_takedowns": p.get("turretTakedowns"),
            "inhibitor_kills": p.get("inhibitorKills"),
            "inhibitor_takedowns": p.get("inhibitorTakedowns"),
            "dragon_kills": p.get("dragonKills"),
            "baron_kills": p.get("baronKills"),
            "objectives_stolen": p.get("objectivesStolen"),

            # 시야
            "vision_score": p.get("visionScore"),
            "wards_placed": p.get("wardsPlaced"),
            "wards_killed": p.get("wardsKilled"),
            "detector_wards_placed": p.get("detectorWardsPlaced"),
            "vision_wards_bought_in_game": p.get("visionWardsBoughtInGame"),

            # 스펠
            "summoner1_id": p.get("summoner1Id"),
            "summoner2_id": p.get("summoner2Id"),

            # 아이템
            "item0": p.get("item0"),
            "item1": p.get("item1"),
            "item2": p.get("item2"),
            "item3": p.get("item3"),
            "item4": p.get("item4"),
            "item5": p.get("item5"),
            "item6": p.get("item6"),
            "items_purchased": p.get("itemsPurchased"),

            # 룬
            "primary_perk": get_primary_perk(p),
            "sub_style": get_sub_style(p),

            # Challenges 일부
            "kill_participation": p.get("challenges", {}).get("killParticipation"),
            "damage_per_minute": p.get("challenges", {}).get("damagePerMinute"),
            "gold_per_minute": p.get("challenges", {}).get("goldPerMinute"),
            "vision_score_per_minute": p.get("challenges", {}).get("visionScorePerMinute"),
            "team_damage_percentage": p.get("challenges", {}).get("teamDamagePercentage"),
        }

        rows.append(row)

    return rows


# =========================================================
# 7. App-ready 변환 함수
# =========================================================

def find_existing_path(candidates: list[Path]) -> Optional[Path]:
    for path in candidates:
        if path and path.exists():
            return path
    return None


def load_item_name_map(item_map_path: Optional[str] = None) -> dict[int, str]:
    """
    item_id -> item_name 매핑을 로드한다.

    우선순위:
    1. --item-map으로 직접 지정한 CSV
    2. 자동 탐색된 item_id_map.csv
    3. 스크립트 내부 EMBEDDED_ITEM_ID_NAME_MAP

    따라서 외부 item_id_map.csv가 없어도 아이템 이름 변환이 가능하다.
    """
    embedded_mapping = dict(EMBEDDED_ITEM_ID_NAME_MAP)

    candidates = []

    if item_map_path:
        candidates.append(Path(item_map_path))

    candidates.extend([
        Path("data/lol_assignment_dataset/extras/item_id_map.csv"),
        Path("data/lol_assignment_dataset/item_id_map.csv"),
        Path("data/item_id_map.csv"),
        Path("item_id_map.csv"),
    ])

    path = find_existing_path(candidates)

    if path is None:
        print(f"[INFO] item_id_map.csv를 찾지 못했습니다. 내장 아이템 매핑 {len(embedded_mapping)}개를 사용합니다.")
        return embedded_mapping

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] item map 로드 실패: {path} / {e}")
        print(f"[INFO] 내장 아이템 매핑 {len(embedded_mapping)}개를 사용합니다.")
        return embedded_mapping

    if "item_id" not in df.columns:
        print(f"[WARN] item map에 item_id 컬럼이 없습니다: {path}")
        print(f"[INFO] 내장 아이템 매핑 {len(embedded_mapping)}개를 사용합니다.")
        return embedded_mapping

    name_col = None
    for candidate in ["item_name", "name", "item", "아이템명"]:
        if candidate in df.columns:
            name_col = candidate
            break

    if name_col is None:
        print(f"[WARN] item map에 item_name/name 컬럼이 없습니다: {path}")
        print(f"[INFO] 내장 아이템 매핑 {len(embedded_mapping)}개를 사용합니다.")
        return embedded_mapping

    csv_mapping = {}

    for _, row in df.iterrows():
        item_id = normalize_item_id(row.get("item_id"))
        if item_id is None:
            continue

        name = str(row.get(name_col, "")).strip()

        if not name or name.lower() == "nan":
            continue

        csv_mapping[item_id] = name

    # CSV가 있으면 CSV 값을 우선 적용하되, CSV에 없는 값은 내장 매핑을 유지한다.
    merged_mapping = dict(embedded_mapping)
    merged_mapping.update(csv_mapping)

    print(
        f"[INFO] item map 로드 완료: {path} / CSV {len(csv_mapping)}개 + "
        f"내장 fallback {len(embedded_mapping)}개 = 최종 {len(merged_mapping)}개"
    )
    return merged_mapping



def item_display_name(item_id: Any, item_name_map: dict[int, str]) -> str:
    normalized = normalize_item_id(item_id)

    if normalized is None:
        return ""

    return item_name_map.get(normalized, str(normalized))


def add_item_name_columns(df: pd.DataFrame, item_name_map: dict[int, str]) -> pd.DataFrame:
    df = df.copy()

    for i in range(7):
        item_col = f"item{i}"
        name_col = f"item{i}_name"

        if item_col not in df.columns:
            df[item_col] = 0

        df[name_col] = df[item_col].apply(lambda x: item_display_name(x, item_name_map))

    item_name_cols = [f"item{i}_name" for i in range(7)]

    def build_item_build(row: pd.Series) -> str:
        names = []
        for col in item_name_cols:
            value = str(row.get(col, "")).strip()
            if value and value.lower() != "nan":
                names.append(value)
        return " / ".join(names)

    def representative_item(row: pd.Series) -> str:
        # 장신구 item6보다 실제 빌드 아이템 item0~item5를 우선 대표 아이템으로 선택
        for i in range(6):
            value = str(row.get(f"item{i}_name", "")).strip()
            if value and value.lower() != "nan":
                return value
        value = str(row.get("item6_name", "")).strip()
        return value if value.lower() != "nan" else ""

    df["item_build"] = df.apply(build_item_build, axis=1)
    df["equipment_set"] = df.apply(representative_item, axis=1)

    return df


def add_enemy_team_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "match_id" not in df.columns or "team_id" not in df.columns or "champion_name" not in df.columns:
        df["enemy_team"] = ""
        return df

    team_champions = (
        df.groupby(["match_id", "team_id"])["champion_name"]
        .apply(lambda s: " / ".join(sorted([str(x) for x in s.dropna().unique() if str(x).strip()])))
        .reset_index()
    )

    opponent_map = {}

    for match_id, group in team_champions.groupby("match_id"):
        if len(group) < 2:
            continue

        rows = group.to_dict("records")

        for row in rows:
            opponent_rows = [r for r in rows if str(r["team_id"]) != str(row["team_id"])]
            if opponent_rows:
                opponent_map[(match_id, row["team_id"])] = opponent_rows[0]["champion_name"]

    df["enemy_team"] = df.apply(
        lambda r: opponent_map.get((r.get("match_id"), r.get("team_id")), ""),
        axis=1,
    )

    return df


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def convert_raw_battle_logs_to_app_ready(
    raw_df: pd.DataFrame,
    item_map_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Riot API 수집 결과 raw battle_logs를 app.py v2.4 호환 구조로 변환한다.

    핵심 추가 컬럼:
    - battle_id
    - result
    - duration_sec
    - player_team
    - enemy_team
    - main_dealer
    - total_damage
    - skill_used_most
    - equipment_set
    - user_segment
    - battle_mode
    - original_patch_version
    - patch_version_mapping_rule
    - item0_name ~ item6_name
    - item_build
    """
    df = raw_df.copy()
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

    # 필수 원본 컬럼 방어
    for col in ["match_id", "participant_id", "game_version", "champion_name", "team_id", "win"]:
        if col not in df.columns:
            df[col] = ""

    # 패치 버전 매핑 재계산
    df["original_patch_version"] = df["game_version"].apply(extract_raw_patch_version)
    df["patch_version"] = df["game_version"].apply(map_game_version_to_patch_version)
    df["patch_version_mapping_rule"] = df["game_version"].apply(patch_version_mapping_rule)

    # 앱 필수 컬럼
    df["battle_id"] = df["match_id"].astype(str) + "_" + df["participant_id"].astype(str)
    df["result"] = df["win"].apply(lambda x: "win" if truthy_win(x) else "loss")
    df["duration_sec"] = pd.to_numeric(df.get("game_duration", 0), errors="coerce").fillna(0).astype(int)
    df["player_team"] = df["champion_name"].astype(str)
    df["main_dealer"] = df["champion_name"].astype(str)
    df["total_damage"] = pd.to_numeric(
        df.get("total_damage_dealt_to_champions", 0),
        errors="coerce",
    ).fillna(0)
    df["skill_used_most"] = df.get("team_position", "").astype(str)
    df["user_segment"] = df.get("source_tiers", "").astype(str)
    df["source_player_riot_id"] = df.get("source_riot_ids", "").astype(str)
    df["battle_mode"] = df.get("queue_id", "").apply(queue_to_battle_mode)

    # 아이템명/대표 아이템/아이템 빌드
    item_name_map = load_item_name_map(item_map_path)
    df = add_item_name_columns(df, item_name_map)

    # 상대팀 조합
    df = add_enemy_team_column(df)

    # 중복 제거
    df = df.drop_duplicates(subset=["battle_id"], keep="first").reset_index(drop=True)

    return df


def build_item_usage_long(app_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in app_df.iterrows():
        for slot in range(7):
            item_col = f"item{slot}"
            item_name_col = f"item{slot}_name"

            item_id = normalize_item_id(row.get(item_col))
            item_name = str(row.get(item_name_col, "")).strip()

            if item_id is None and not item_name:
                continue

            rows.append({
                "match_id": row.get("match_id"),
                "battle_id": row.get("battle_id"),
                "participant_id": row.get("participant_id"),
                "patch_version": row.get("patch_version"),
                "original_patch_version": row.get("original_patch_version"),
                "game_version": row.get("game_version"),
                "source_tiers": row.get("source_tiers"),
                "source_riot_ids": row.get("source_riot_ids"),
                "champion_name": row.get("champion_name"),
                "team_position": row.get("team_position"),
                "result": row.get("result"),
                "win": row.get("win"),
                "item_slot": slot,
                "item_id": item_id,
                "item_name": item_name or str(item_id),
                "total_damage": row.get("total_damage"),
                "kills": row.get("kills"),
                "deaths": row.get("deaths"),
                "assists": row.get("assists"),
                "kda": row.get("kda"),
                "gold_earned": row.get("gold_earned"),
                "total_cs": row.get("total_cs"),
                "vision_score": row.get("vision_score"),
            })

    return pd.DataFrame(rows)


def win_rate_from_result(series: pd.Series) -> float:
    return float((series.astype(str).str.lower() == "win").mean())


def save_app_ready_outputs(
    app_df: pd.DataFrame,
    processed_dir: Path,
    app_dataset_dir: Optional[Path] = None,
    raw_df: Optional[pd.DataFrame] = None,
) -> dict[str, Any]:
    """
    processed 폴더와 app_dataset 폴더에 앱용 battle_logs와 extras 집계 파일을 저장한다.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    # raw 보존
    if raw_df is not None:
        raw_path = processed_dir / "battle_logs_raw.csv"
        raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    # processed/battle_logs.csv는 앱용 구조로 저장
    battle_logs_path = processed_dir / "battle_logs.csv"
    app_df.to_csv(battle_logs_path, index=False, encoding="utf-8-sig")

    # app_dataset_dir에도 저장
    if app_dataset_dir is not None:
        app_dataset_dir.mkdir(parents=True, exist_ok=True)
        app_df.to_csv(app_dataset_dir / "battle_logs.csv", index=False, encoding="utf-8-sig")
        extras_dir = app_dataset_dir / "extras"
    else:
        extras_dir = processed_dir / "extras"

    extras_dir.mkdir(parents=True, exist_ok=True)

    # item_usage_long
    item_usage_long = build_item_usage_long(app_df)
    item_usage_long.to_csv(extras_dir / "item_usage_long.csv", index=False, encoding="utf-8-sig")

    # champion_performance_by_patch
    champion_group_cols = ["patch_version", "champion_name", "team_position"]
    champion_perf = (
        app_df.groupby(champion_group_cols, dropna=False)
        .agg(
            rows=("battle_id", "count"),
            matches=("match_id", "nunique"),
            wins=("result", lambda x: int((x.astype(str).str.lower() == "win").sum())),
            win_rate=("result", win_rate_from_result),
            avg_kills=("kills", "mean"),
            avg_deaths=("deaths", "mean"),
            avg_assists=("assists", "mean"),
            avg_kda=("kda", "mean"),
            avg_damage=("total_damage", "mean"),
            avg_gold=("gold_earned", "mean"),
            avg_cs=("total_cs", "mean"),
            avg_vision=("vision_score", "mean"),
        )
        .reset_index()
    )
    champion_perf.to_csv(
        extras_dir / "champion_performance_by_patch.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # item_performance_by_patch
    if not item_usage_long.empty:
        item_perf = (
            item_usage_long.groupby(["patch_version", "item_id", "item_name"], dropna=False)
            .agg(
                rows=("battle_id", "count"),
                matches=("match_id", "nunique"),
                wins=("result", lambda x: int((x.astype(str).str.lower() == "win").sum())),
                win_rate=("result", win_rate_from_result),
                avg_damage=("total_damage", "mean"),
                avg_kills=("kills", "mean"),
                avg_deaths=("deaths", "mean"),
                avg_assists=("assists", "mean"),
                avg_kda=("kda", "mean"),
            )
            .reset_index()
        )
    else:
        item_perf = pd.DataFrame()
    item_perf.to_csv(
        extras_dir / "item_performance_by_patch.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # tier_patch_performance
    tier_patch_perf = (
        app_df.groupby(["patch_version", "source_tiers"], dropna=False)
        .agg(
            rows=("battle_id", "count"),
            matches=("match_id", "nunique"),
            wins=("result", lambda x: int((x.astype(str).str.lower() == "win").sum())),
            win_rate=("result", win_rate_from_result),
            avg_damage=("total_damage", "mean"),
            avg_kda=("kda", "mean"),
            avg_gold=("gold_earned", "mean"),
            avg_cs=("total_cs", "mean"),
        )
        .reset_index()
    )
    tier_patch_perf.to_csv(
        extras_dir / "tier_patch_performance.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # 변환 요약
    summary = {
        "app_ready_rows": int(len(app_df)),
        "app_ready_columns": int(len(app_df.columns)),
        "unique_matches": int(app_df["match_id"].nunique()) if "match_id" in app_df.columns else 0,
        "unique_battle_ids": int(app_df["battle_id"].nunique()) if "battle_id" in app_df.columns else 0,
        "item_usage_long_rows": int(len(item_usage_long)),
        "patch_versions": sorted([str(x) for x in app_df["patch_version"].dropna().unique().tolist()])
        if "patch_version" in app_df.columns else [],
        "battle_logs_path": str(battle_logs_path),
        "app_dataset_dir": str(app_dataset_dir) if app_dataset_dir else "",
        "extras_dir": str(extras_dir),
    }

    save_json(summary, processed_dir / "app_conversion_summary.json")

    if app_dataset_dir is not None:
        save_json(summary, app_dataset_dir / "app_conversion_summary.json")

    return summary


def convert_existing_battle_logs_file(
    input_csv: Path,
    output_csv: Optional[Path],
    item_map_path: Optional[str],
    app_dataset_dir: Optional[Path],
) -> dict[str, Any]:
    """
    이미 수집된 battle_logs.csv를 앱용 구조로 변환하는 단독 모드.
    API Key 없이 사용 가능.
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"입력 CSV를 찾을 수 없습니다: {input_csv}")

    raw_df = pd.read_csv(input_csv)
    app_df = convert_raw_battle_logs_to_app_ready(raw_df, item_map_path=item_map_path)

    if output_csv is not None:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        app_df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    processed_dir = output_csv.parent if output_csv is not None else input_csv.parent
    summary = save_app_ready_outputs(
        app_df=app_df,
        processed_dir=processed_dir,
        app_dataset_dir=app_dataset_dir,
        raw_df=raw_df,
    )

    return summary



def make_match_ids_cache_path(
    raw_match_ids_dir: Path,
    tier: str,
    riot_id: str,
    count_per_player: int,
    queue: Optional[int],
    match_type: Optional[str],
) -> Path:
    """
    count/queue/type이 달라졌는데도 예전 match_ids 캐시를 재사용하는 문제를 막기 위한 캐시 파일명 생성.

    예:
    CHALLENGER_DNS_또이브_KR13_count300_queue420_typeranked.json
    """
    queue_part = f"queue{queue}" if queue is not None else "queueall"
    type_part = f"type{match_type}" if match_type else "typeall"
    filename = (
        f"{tier}_{safe_filename(riot_id)}"
        f"_count{int(count_per_player)}_{queue_part}_{type_part}.json"
    )
    return raw_match_ids_dir / filename


def load_usable_match_ids_cache(
    path: Path,
    requested_count: int,
) -> Optional[list[str]]:
    """
    캐시가 있어도 요청한 개수보다 적으면 사용하지 않는다.
    예전 count=15 캐시가 있을 때 --count 300을 주면 이 함수가 None을 반환해서 재수집한다.
    """
    if not path.exists():
        return None

    try:
        match_ids = load_json(path)
    except Exception:
        return None

    if not isinstance(match_ids, list):
        return None

    if len(match_ids) < requested_count:
        print(
            f"[CACHE-SKIP] {path.name}: 캐시 {len(match_ids)}개 < 요청 {requested_count}개, 다시 수집"
        )
        return None

    return match_ids[:requested_count]



def split_csv_values(text_value: Optional[str], default: Optional[list[str]] = None) -> list[str]:
    if text_value is None or str(text_value).strip() == "":
        return list(default or [])

    return [x.strip().upper() for x in str(text_value).split(",") if x.strip()]


def normalize_tier(tier: str) -> str:
    return str(tier).strip().upper().replace(" ", "")


def normalize_division(division: str) -> str:
    return str(division).strip().upper()


def load_match_ids_from_csv(path: Path) -> set[str]:
    if not path.exists():
        return set()

    try:
        df = pd.read_csv(path, usecols=lambda c: str(c).replace("\ufeff", "").strip() == "match_id")
    except Exception:
        try:
            df = pd.read_csv(path)
        except Exception:
            return set()

    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

    if "match_id" not in df.columns:
        return set()

    return {
        str(x).strip()
        for x in df["match_id"].dropna().tolist()
        if str(x).strip()
    }


def load_existing_match_ids(out_path: Path, app_dataset_dir: Optional[str] = None) -> set[str]:
    """
    이미 수집한 match_id를 모은다.

    기준:
    - raw/match_details/*.json 파일명
    - processed/battle_logs_raw.csv
    - processed/battle_logs.csv
    - app_dataset_dir/battle_logs.csv
    """
    existing: set[str] = set()

    raw_match_details_dir = out_path / "raw" / "match_details"
    if raw_match_details_dir.exists():
        for path in raw_match_details_dir.glob("*.json"):
            match_id = path.stem.strip()
            if match_id:
                existing.add(match_id)

    candidate_csvs = [
        out_path / "processed" / "battle_logs_raw.csv",
        out_path / "processed" / "battle_logs.csv",
    ]

    if app_dataset_dir:
        candidate_csvs.append(Path(app_dataset_dir) / "battle_logs.csv")

    for csv_path in candidate_csvs:
        existing.update(load_match_ids_from_csv(csv_path))

    return existing


def load_existing_raw_battle_logs(processed_dir: Path) -> pd.DataFrame:
    """
    이전에 저장한 raw 전투 로그를 읽어서 새 로그와 병합할 때 사용한다.
    """
    for candidate in [
        processed_dir / "battle_logs_raw.csv",
        processed_dir / "battle_logs.csv",
    ]:
        if candidate.exists():
            try:
                df = pd.read_csv(candidate)
                df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
                if "match_id" in df.columns and "participant_id" in df.columns:
                    return df
            except Exception:
                pass

    return pd.DataFrame()


def merge_raw_battle_logs(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    frames = []

    if existing_df is not None and not existing_df.empty:
        frames.append(existing_df)

    if new_df is not None and not new_df.empty:
        frames.append(new_df)

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True, sort=False)

    if "match_id" in merged.columns and "participant_id" in merged.columns:
        merged = merged.drop_duplicates(
            subset=["match_id", "participant_id"],
            keep="last",
        ).reset_index(drop=True)

    return merged


def build_riot_id_from_account(account: dict[str, Any], fallback: str = "") -> str:
    game_name = str(account.get("gameName", "") or "").strip()
    tag_line = str(account.get("tagLine", "") or "").strip()

    if game_name and tag_line:
        return f"{game_name}#{tag_line}"

    return fallback


def league_entry_sort_key(entry: dict[str, Any]) -> tuple[int, int]:
    """
    리그 엔트리를 LP, 승수 기준으로 정렬하기 위한 key.
    """
    lp = int(entry.get("leaguePoints", 0) or 0)
    wins = int(entry.get("wins", 0) or 0)
    return (lp, wins)


def resolve_league_entry_to_player(
    client: RiotApiClient,
    tier: str,
    entry: dict[str, Any],
    source: str,
) -> Optional[dict[str, Any]]:
    """
    LEAGUE-V4 entry를 수집 대상 player row로 변환한다.

    최신 LeagueEntryDTO 계열 응답은 환경/시점에 따라 puuid가 직접 들어오거나,
    summonerId만 들어올 수 있다. 따라서 다음 순서로 처리한다.

    1. entry["puuid"]가 있으면 Summoner-V4를 건너뛰고 바로 사용
    2. puuid가 없고 summonerId가 있으면 Summoner-V4로 puuid 조회
    3. puuid 확보 후 Account-V1로 Riot ID 복원

    이 처리를 하지 않으면 entry에 summonerId가 없고 puuid만 있는 경우
    플레이어가 1명도 수집되지 않아 page를 계속 넘기는 문제가 생길 수 있다.
    """
    encrypted_summoner_id = str(entry.get("summonerId", "") or "").strip()
    puuid = str(entry.get("puuid", "") or entry.get("encryptedPUUID", "") or "").strip()

    # LeagueEntry에 puuid가 없는 구형/일부 응답이면 summonerId -> puuid 변환
    if not puuid and encrypted_summoner_id:
        summoner = client.get_summoner_by_id(encrypted_summoner_id)
        puuid = str(summoner.get("puuid", "") or "").strip()

    if not puuid:
        return None

    account = {}
    try:
        account = client.get_account_by_puuid(puuid)
    except Exception as e:
        print(f"[WARN] Account by PUUID 실패: {puuid[:8]}... / {e}")

    fallback_riot_id = encrypted_summoner_id or puuid[:12]

    return {
        "tier": normalize_tier(tier),
        "riot_id": build_riot_id_from_account(account, fallback=fallback_riot_id),
        "game_name": account.get("gameName", ""),
        "tag_line": account.get("tagLine", ""),
        "puuid": puuid,
        "summoner_id": encrypted_summoner_id,
        "league_points": entry.get("leaguePoints", 0),
        "rank": entry.get("rank", ""),
        "wins": entry.get("wins", 0),
        "losses": entry.get("losses", 0),
        "veteran": entry.get("veteran", False),
        "inactive": entry.get("inactive", False),
        "fresh_blood": entry.get("freshBlood", False),
        "hot_streak": entry.get("hotStreak", False),
        "source": source,
        "status": "success",
        "message": "",
    }


def collect_players_from_league_v4(
    client: RiotApiClient,
    tiers: list[str],
    players_per_tier: int,
    league_queue: str,
    divisions: list[str],
    processed_dir: Path,
    resume: bool = True,
    league_max_pages_per_division: int = 3,
) -> list[dict[str, Any]]:
    """
    LEAGUE-V4로 티어별 플레이어 목록을 자동 수집한다.

    - CHALLENGER / GRANDMASTER / MASTER: apex league endpoint 사용
    - DIAMOND 이하 또는 일반 티어: entries/{queue}/{tier}/{division}?page=N 사용
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    league_max_pages_per_division = max(1, int(league_max_pages_per_division))

    cache_path = processed_dir / (
        f"auto_players_{league_queue}_"
        f"{'-'.join(tiers)}_n{players_per_tier}_div{'-'.join(divisions)}_maxp{league_max_pages_per_division}.csv"
    )

    if resume and cache_path.exists():
        try:
            cached = pd.read_csv(cache_path)
            cached.columns = [str(c).replace("\ufeff", "").strip() for c in cached.columns]
            if len(cached) >= len(tiers) * players_per_tier and "puuid" in cached.columns:
                print(f"[CACHE] 자동 플레이어 목록 사용: {cache_path}")
                return cached.to_dict(orient="records")
        except Exception:
            pass

    all_players: list[dict[str, Any]] = []
    seen_puuids: set[str] = set()
    logs: list[dict[str, Any]] = []

    for tier in tiers:
        tier = normalize_tier(tier)
        collected_for_tier = 0

        print(f"\n========== LEAGUE-V4 자동 플레이어 수집: {tier} ==========")

        try:
            if tier in {"CHALLENGER", "GRANDMASTER", "MASTER"}:
                league = client.get_apex_league(queue=league_queue, tier=tier)
                entries = league.get("entries", [])
                entries = sorted(entries, key=league_entry_sort_key, reverse=True)

                for entry in entries:
                    if collected_for_tier >= players_per_tier:
                        break

                    try:
                        player = resolve_league_entry_to_player(
                            client=client,
                            tier=tier,
                            entry=entry,
                            source=f"league-v4:{tier}:{league_queue}",
                        )
                        if not player:
                            continue

                        if player["puuid"] in seen_puuids:
                            continue

                        seen_puuids.add(player["puuid"])
                        all_players.append(player)
                        collected_for_tier += 1
                        print(f"[PLAYER] {tier} {collected_for_tier}/{players_per_tier} {player['riot_id']}")

                    except Exception as e:
                        logs.append({
                            "tier": tier,
                            "step": "resolve_apex_player",
                            "status": "failed",
                            "message": str(e),
                        })
                        print(f"[WARN] {tier} 플레이어 변환 실패: {e}")

            else:
                for division in divisions:
                    if collected_for_tier >= players_per_tier:
                        break

                    division = normalize_division(division)
                    page = 1

                    while collected_for_tier < players_per_tier and page <= league_max_pages_per_division:
                        print(
                            f"[REQ] League entries tier={tier}, division={division}, page={page} "
                            f"/ max_page={league_max_pages_per_division}"
                        )
                        entries = client.get_league_entries(
                            queue=league_queue,
                            tier=tier,
                            division=division,
                            page=page,
                        )

                        if not entries:
                            break

                        entries = sorted(entries, key=league_entry_sort_key, reverse=True)

                        for entry in entries:
                            if collected_for_tier >= players_per_tier:
                                break

                            try:
                                player = resolve_league_entry_to_player(
                                    client=client,
                                    tier=tier,
                                    entry=entry,
                                    source=f"league-v4:{tier}:{division}:page{page}:{league_queue}",
                                )
                                if not player:
                                    logs.append({
                                        "tier": tier,
                                        "division": division,
                                        "page": page,
                                        "step": "resolve_entry_player",
                                        "status": "skipped",
                                        "message": "League entry에 puuid/summonerId가 없어 플레이어로 변환하지 못했습니다.",
                                    })
                                    continue

                                if player["puuid"] in seen_puuids:
                                    continue

                                seen_puuids.add(player["puuid"])
                                all_players.append(player)
                                collected_for_tier += 1
                                print(f"[PLAYER] {tier} {collected_for_tier}/{players_per_tier} {player['riot_id']}")

                            except Exception as e:
                                logs.append({
                                    "tier": tier,
                                    "division": division,
                                    "page": page,
                                    "step": "resolve_entry_player",
                                    "status": "failed",
                                    "message": str(e),
                                })
                                print(f"[WARN] {tier} {division} 플레이어 변환 실패: {e}")

                        page += 1

                    if collected_for_tier < players_per_tier and page > league_max_pages_per_division:
                        print(
                            f"[STOP] {tier} {division}: max_page={league_max_pages_per_division}까지 확인했지만 "
                            f"{collected_for_tier}/{players_per_tier}명만 확보했습니다. 다음 division으로 넘어갑니다."
                        )

        except Exception as e:
            logs.append({
                "tier": tier,
                "step": "collect_tier_players",
                "status": "failed",
                "message": str(e),
            })
            print(f"[FAIL] {tier} 플레이어 목록 수집 실패: {e}")

    players_df = pd.DataFrame(all_players)
    players_df.to_csv(cache_path, index=False, encoding="utf-8-sig")
    players_df.to_csv(processed_dir / "auto_players.csv", index=False, encoding="utf-8-sig")

    if logs:
        pd.DataFrame(logs).to_csv(processed_dir / "auto_players_logs.csv", index=False, encoding="utf-8-sig")

    print(f"[INFO] 자동 수집 플레이어 수: {len(all_players)}")
    print(f"[INFO] 자동 플레이어 목록 저장: {cache_path}")

    return all_players


# =========================================================
# 8. 수집 실행
# =========================================================

def collect_dataset(
    out_dir: str,
    count_per_player: int,
    queue: Optional[int],
    match_type: Optional[str],
    resume: bool,
    item_map_path: Optional[str],
    app_dataset_dir: Optional[str],
    skip_app_convert: bool,
    auto_players: bool = False,
    tiers: Optional[list[str]] = None,
    players_per_tier: int = 3,
    divisions: Optional[list[str]] = None,
    league_queue: str = "RANKED_SOLO_5x5",
    platform_routing: str = PLATFORM_ROUTING,
    exclude_existing_from_count: bool = True,
    merge_existing: bool = True,
    max_match_scan_pages: int = 30,
    league_max_pages_per_division: int = 3,
) -> None:
    out_path = Path(out_dir)

    raw_accounts_dir = out_path / "raw" / "accounts"
    raw_match_ids_dir = out_path / "raw" / "match_ids"
    raw_match_details_dir = out_path / "raw" / "match_details"

    processed_dir = out_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    client = RiotApiClient(
        api_key=RIOT_API_KEY,
        regional_routing=REGIONAL_ROUTING,
        platform_routing=platform_routing,
    )

    accounts = []
    player_match_id_rows = []
    match_sources: dict[str, list[dict[str, str]]] = {}
    logs = []

    # -----------------------------------------------------
    # 0) 수집 대상 플레이어 결정
    # -----------------------------------------------------

    if auto_players:
        selected_tiers = tiers or ["CHALLENGER", "GRANDMASTER", "MASTER", "DIAMOND", "EMERALD", "PLATINUM", "GOLD"]
        selected_divisions = divisions or ["I", "II", "III", "IV"]

        print("\n========== STEP 0. LEAGUE-V4로 티어별 플레이어 자동 수집 ==========")
        accounts = collect_players_from_league_v4(
            client=client,
            tiers=selected_tiers,
            players_per_tier=players_per_tier,
            league_queue=league_queue,
            divisions=selected_divisions,
            processed_dir=processed_dir,
            resume=resume,
            league_max_pages_per_division=league_max_pages_per_division,
        )
    else:
        # -----------------------------------------------------
        # 1) Riot ID -> PUUID
        # -----------------------------------------------------

        print("\n========== STEP 1. Riot ID -> PUUID ==========")

        for idx, player in enumerate(PLAYERS, start=1):
            tier = player["tier"]
            riot_id = player["riot_id"]

            account_path = raw_accounts_dir / f"{tier}_{safe_filename(riot_id)}.json"

            try:
                if resume and account_path.exists():
                    account = load_json(account_path)
                    print(f"[CACHE] Account {idx}/{len(PLAYERS)} {tier} {riot_id}")
                else:
                    print(f"[REQ] Account {idx}/{len(PLAYERS)} {tier} {riot_id}")
                    account = client.get_account_by_riot_id(riot_id)
                    save_json(account, account_path)

                puuid = account.get("puuid")

                if not puuid:
                    raise RuntimeError("PUUID가 응답에 없습니다.")

                account_row = {
                    "tier": tier,
                    "riot_id": riot_id,
                    "game_name": account.get("gameName"),
                    "tag_line": account.get("tagLine"),
                    "puuid": puuid,
                    "status": "success",
                    "message": "",
                }

                accounts.append(account_row)

            except Exception as e:
                print(f"[FAIL] Account {tier} {riot_id}: {e}")

                logs.append({
                    "step": "account",
                    "tier": tier,
                    "riot_id": riot_id,
                    "match_id": "",
                    "status": "failed",
                    "message": str(e),
                })

                accounts.append({
                    "tier": tier,
                    "riot_id": riot_id,
                    "game_name": "",
                    "tag_line": "",
                    "puuid": "",
                    "status": "failed",
                    "message": str(e),
                })

    accounts_df = pd.DataFrame(accounts)
    accounts_df.to_csv(
        processed_dir / "accounts.csv",
        index=False,
        encoding="utf-8-sig",
    )

    valid_accounts = [a for a in accounts if a.get("status") == "success" and str(a.get("puuid", "")).strip()]

    print(f"[INFO] 유효 계정 수: {len(valid_accounts)} / {len(accounts)}")

    # -----------------------------------------------------
    # 2) PUUID -> 최근 match_id
    # -----------------------------------------------------

    print("\n========== STEP 2. PUUID -> Match IDs ==========")

    existing_match_ids = load_existing_match_ids(out_path, app_dataset_dir=app_dataset_dir) if exclude_existing_from_count else set()
    selected_this_run: set[str] = set()
    existing_raw_df = load_existing_raw_battle_logs(processed_dir) if merge_existing else pd.DataFrame()

    print(f"[INFO] 기존 수집 match_id 수: {len(existing_match_ids)}")
    if merge_existing and not existing_raw_df.empty:
        print(f"[INFO] 기존 raw battle log rows 병합 예정: {len(existing_raw_df)}")

    for idx, account in enumerate(valid_accounts, start=1):
        tier = str(account["tier"])
        riot_id = str(account["riot_id"])
        puuid = str(account["puuid"])

        match_ids_path = make_match_ids_cache_path(
            raw_match_ids_dir=raw_match_ids_dir,
            tier=tier,
            riot_id=riot_id,
            count_per_player=count_per_player,
            queue=queue,
            match_type=match_type,
        )

        try:
            if exclude_existing_from_count:
                print(
                    f"[REQ] New-only Match IDs {idx}/{len(valid_accounts)} {tier} {riot_id} "
                    f"/ 새 경기 목표={count_per_player}, queue={queue}, type={match_type}"
                )
                result = client.get_new_match_ids_by_puuid(
                    puuid=puuid,
                    target_new_count=count_per_player,
                    existing_match_ids=existing_match_ids,
                    selected_this_run=selected_this_run,
                    queue=queue,
                    match_type=match_type,
                    page_size=MATCH_ID_PAGE_SIZE,
                    max_scan_pages=max_match_scan_pages,
                )
                match_ids = result["match_ids"]
                duplicate_in_current_run = result.get("duplicate_in_current_run", [])
                match_id_stats = result.get("stats", {})

                save_json(
                    {
                        "tier": tier,
                        "riot_id": riot_id,
                        "puuid": puuid,
                        "selected_new_match_ids": match_ids,
                        "duplicate_in_current_run": duplicate_in_current_run,
                        "stats": match_id_stats,
                    },
                    match_ids_path,
                )

                print(
                    f"[INFO] {tier} {riot_id}: 새 match_id {len(match_ids)}개 선택 "
                    f"/ 기존 제외 {match_id_stats.get('skipped_existing', 0)}개 "
                    f"/ 이번 실행 중복 제외 {match_id_stats.get('skipped_current_duplicate', 0)}개 "
                    f"/ 후보 스캔 {match_id_stats.get('scanned_candidates', 0)}개"
                )

                # 이번 실행에서 이미 다른 유저가 선택한 match_id는 source만 추가하고 fetch count에는 포함하지 않는다.
                for duplicate_match_id in duplicate_in_current_run:
                    source = {"tier": tier, "riot_id": riot_id, "puuid": puuid}
                    if duplicate_match_id in match_sources:
                        match_sources.setdefault(duplicate_match_id, []).append(source)

                    player_match_id_rows.append({
                        "tier": tier,
                        "riot_id": riot_id,
                        "puuid": puuid,
                        "match_rank": "",
                        "match_id": duplicate_match_id,
                        "selection_status": "duplicate_in_current_run_not_counted",
                    })

            else:
                cached_match_ids = None
                if resume:
                    cached_match_ids = load_usable_match_ids_cache(
                        path=match_ids_path,
                        requested_count=count_per_player,
                    )

                if cached_match_ids is not None:
                    match_ids = cached_match_ids
                    print(
                        f"[CACHE] Match IDs {idx}/{len(valid_accounts)} "
                        f"{tier} {riot_id} / {len(match_ids)}개"
                    )
                else:
                    print(
                        f"[REQ] Match IDs {idx}/{len(valid_accounts)} {tier} {riot_id} "
                        f"/ requested={count_per_player}, queue={queue}, type={match_type}"
                    )
                    match_ids = client.get_match_ids_by_puuid(
                        puuid=puuid,
                        count=count_per_player,
                        queue=queue,
                        match_type=match_type,
                    )
                    save_json(match_ids, match_ids_path)

            for rank, match_id in enumerate(match_ids, start=1):
                source = {
                    "tier": tier,
                    "riot_id": riot_id,
                    "puuid": puuid,
                }

                selected_this_run.add(match_id)
                match_sources.setdefault(match_id, []).append(source)

                player_match_id_rows.append({
                    "tier": tier,
                    "riot_id": riot_id,
                    "puuid": puuid,
                    "match_rank": rank,
                    "match_id": match_id,
                    "selection_status": "selected_new" if exclude_existing_from_count else "selected",
                })

        except Exception as e:
            print(f"[FAIL] Match IDs {tier} {riot_id}: {e}")

            logs.append({
                "step": "match_ids",
                "tier": tier,
                "riot_id": riot_id,
                "match_id": "",
                "status": "failed",
                "message": str(e),
            })

    player_match_ids_df = pd.DataFrame(player_match_id_rows)
    player_match_ids_df.to_csv(
        processed_dir / "player_match_ids.csv",
        index=False,
        encoding="utf-8-sig",
    )

    unique_match_ids = sorted(match_sources.keys())

    print(f"[INFO] 유저별 선택 match_id row 수: {len(player_match_id_rows)}")
    print(f"[INFO] 이번 실행에서 새로 가져올 unique match_id 수: {len(unique_match_ids)}")

    # -----------------------------------------------------
    # 3) match_id -> match detail
    # -----------------------------------------------------

    print("\n========== STEP 3. Match Detail 수집 ==========")

    new_battle_rows = []

    for idx, match_id in enumerate(unique_match_ids, start=1):
        detail_path = raw_match_details_dir / f"{match_id}.json"

        try:
            # exclude_existing_from_count=True일 때 unique_match_ids 자체가 새 match만 들어오므로,
            # detail_path 캐시는 보통 없지만, 재시작 안정성을 위해 있으면 재사용한다.
            if resume and detail_path.exists():
                match_detail = load_json(detail_path)
                print(f"[CACHE] Detail {idx}/{len(unique_match_ids)} {match_id}")
            else:
                print(f"[REQ] Detail {idx}/{len(unique_match_ids)} {match_id}")
                match_detail = client.get_match_detail(match_id)
                save_json(match_detail, detail_path)

            rows = build_battle_log_rows(
                match_detail=match_detail,
                match_sources=match_sources.get(match_id, []),
            )

            new_battle_rows.extend(rows)

        except Exception as e:
            print(f"[FAIL] Detail {match_id}: {e}")

            logs.append({
                "step": "match_detail",
                "tier": "",
                "riot_id": "",
                "match_id": match_id,
                "status": "failed",
                "message": str(e),
            })

    # -----------------------------------------------------
    # 4) 저장 + 앱용 자동 변환
    # -----------------------------------------------------

    print("\n========== STEP 4. 최종 데이터셋 저장 ==========")

    new_raw_battle_logs_df = pd.DataFrame(new_battle_rows)

    if not new_raw_battle_logs_df.empty:
        new_raw_battle_logs_df = new_raw_battle_logs_df.drop_duplicates(
            subset=["match_id", "participant_id"],
            keep="first",
        ).reset_index(drop=True)

    if merge_existing:
        raw_battle_logs_df = merge_raw_battle_logs(existing_raw_df, new_raw_battle_logs_df)
    else:
        raw_battle_logs_df = new_raw_battle_logs_df

    raw_battle_logs_path = processed_dir / "battle_logs_raw.csv"
    raw_battle_logs_df.to_csv(
        raw_battle_logs_path,
        index=False,
        encoding="utf-8-sig",
    )

    # 이번 실행에서 새로 수집한 row도 별도 저장
    new_raw_battle_logs_df.to_csv(
        processed_dir / "battle_logs_new_only.csv",
        index=False,
        encoding="utf-8-sig",
    )

    if skip_app_convert:
        battle_logs_df = raw_battle_logs_df
        battle_logs_path = processed_dir / "battle_logs.csv"
        battle_logs_df.to_csv(battle_logs_path, index=False, encoding="utf-8-sig")
        app_summary = {}
    else:
        print("\n========== STEP 5. App v2.4용 battle_logs 자동 변환 ==========")
        battle_logs_df = convert_raw_battle_logs_to_app_ready(
            raw_battle_logs_df,
            item_map_path=item_map_path,
        )

        app_dataset_path = Path(app_dataset_dir) if app_dataset_dir else None
        app_summary = save_app_ready_outputs(
            app_df=battle_logs_df,
            processed_dir=processed_dir,
            app_dataset_dir=app_dataset_path,
            raw_df=raw_battle_logs_df,
        )

        battle_logs_path = processed_dir / "battle_logs.csv"

    logs_df = pd.DataFrame(logs)
    logs_df.to_csv(
        processed_dir / "collect_logs.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "auto_players": auto_players,
        "input_players": len(accounts),
        "valid_accounts": len(valid_accounts),
        "requested_new_match_count_per_player": count_per_player if exclude_existing_from_count else None,
        "requested_match_count_per_player": count_per_player,
        "exclude_existing_from_count": exclude_existing_from_count,
        "merge_existing": merge_existing,
        "existing_match_ids_before_run": len(existing_match_ids),
        "player_match_id_rows": len(player_match_id_rows),
        "new_unique_match_ids_this_run": len(unique_match_ids),
        "new_raw_battle_log_rows_this_run": len(new_raw_battle_logs_df),
        "merged_raw_battle_log_rows": len(raw_battle_logs_df),
        "app_ready_battle_log_rows": len(battle_logs_df),
        "failed_logs": len(logs),
        "queue": queue,
        "match_type": match_type,
        "league_queue": league_queue,
        "platform_routing": platform_routing,
        "league_max_pages_per_division": league_max_pages_per_division,
        "skip_app_convert": skip_app_convert,
        "app_conversion": app_summary,
    }

    save_json(summary, processed_dir / "summary.json")

    print("\n========== 완료 ==========")
    print(f"accounts.csv: {processed_dir / 'accounts.csv'}")
    print(f"player_match_ids.csv: {processed_dir / 'player_match_ids.csv'}")
    print(f"battle_logs_new_only.csv: {processed_dir / 'battle_logs_new_only.csv'}")
    print(f"battle_logs_raw.csv: {raw_battle_logs_path}")
    print(f"battle_logs.csv: {battle_logs_path}")
    print(f"collect_logs.csv: {processed_dir / 'collect_logs.csv'}")
    print(f"summary.json: {processed_dir / 'summary.json'}")
    if app_dataset_dir and not skip_app_convert:
        print(f"app dataset battle_logs.csv: {Path(app_dataset_dir) / 'battle_logs.csv'}")
    print()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


# =========================================================
# 9. CLI
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Riot API로 랭크 플레이어와 최근 매치 정보를 수집하고, "
            "app.py v2.4/v2.5용 battle_logs.csv로 자동 변환"
        )
    )

    parser.add_argument(
        "--out-dir",
        default="data/riot_dataset",
        help="수집 결과 저장 폴더",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=MATCH_COUNT_PER_PLAYER,
        help=(
            "유저당 새로 가져올 경기 수. 기본적으로 이미 수집된 match_id는 count에 포함하지 않고 "
            "더 오래된 경기까지 탐색해서 새 match_id를 찾는다."
        ),
    )

    parser.add_argument(
        "--queue",
        type=int,
        default=420,
        help="MATCH-V5 큐 ID. 기본값 420=솔로랭크. 440=자유랭크, 450=칼바람",
    )

    parser.add_argument(
        "--type",
        dest="match_type",
        default="ranked",
        help="MATCH-V5 매치 타입. 기본값 ranked",
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="기존 API 응답 캐시를 무시하고 다시 요청",
    )

    parser.add_argument(
        "--item-map",
        default=None,
        help="item_id_map.csv 경로. 없으면 자동 탐색 후 내장 아이템 매핑 사용",
    )

    parser.add_argument(
        "--app-dataset-dir",
        default="data/lol_assignment_dataset",
        help="app.py가 읽는 LoL 데이터셋 폴더. 여기에 battle_logs.csv와 extras를 자동 저장",
    )

    parser.add_argument(
        "--skip-app-convert",
        action="store_true",
        help="앱용 변환을 건너뛰고 Riot API raw battle_logs.csv만 저장",
    )

    parser.add_argument(
        "--convert-existing",
        default=None,
        help="이미 수집된 battle_logs.csv를 앱용 구조로 변환만 수행. API Key 불필요",
    )

    parser.add_argument(
        "--output-csv",
        default=None,
        help="--convert-existing 사용 시 변환 결과 CSV 저장 경로",
    )

    parser.add_argument(
        "--include-existing-in-count",
        action="store_true",
        help=(
            "기존 방식처럼 이미 가져온 match_id도 count에 포함한다. "
            "기본값은 기존 match_id를 제외하고 새 match_id만 count한다."
        ),
    )

    parser.add_argument(
        "--no-merge-existing",
        action="store_true",
        help=(
            "기존 battle_logs_raw.csv와 병합하지 않고 이번 실행에서 새로 가져온 전투 기록만 저장한다. "
            "기본값은 기존 데이터와 새 데이터를 병합한다."
        ),
    )

    parser.add_argument(
        "--max-match-scan-pages",
        type=int,
        default=30,
        help=(
            "이미 수집된 경기를 건너뛰면서 새 match_id를 찾기 위해 유저당 최대 몇 페이지까지 볼지 설정. "
            "페이지당 최대 100개 후보를 확인한다."
        ),
    )

    # -----------------------------------------------------
    # LEAGUE-V4 자동 플레이어 수집 옵션
    # -----------------------------------------------------

    parser.add_argument(
        "--auto-players",
        action="store_true",
        help=(
            "하드코딩된 PLAYERS 대신 LEAGUE-V4로 티어별 플레이어 목록을 자동 수집한다. "
            "수집한 플레이어는 processed/auto_players.csv에 저장된다."
        ),
    )

    parser.add_argument(
        "--tiers",
        default="CHALLENGER,GRANDMASTER,MASTER,DIAMOND,EMERALD,PLATINUM,GOLD",
        help="--auto-players 사용 시 수집할 티어 목록. 예: DIAMOND,EMERALD,GOLD",
    )

    parser.add_argument(
        "--players-per-tier",
        type=int,
        default=3,
        help="--auto-players 사용 시 티어별 자동 수집할 플레이어 수",
    )

    parser.add_argument(
        "--divisions",
        default="I,II,III,IV",
        help="DIAMOND 이하 티어에서 조회할 division 목록. 예: I 또는 I,II,III,IV",
    )

    parser.add_argument(
        "--league-max-pages-per-division",
        type=int,
        default=3,
        help=(
            "LEAGUE-V4 entries 조회 시 DIAMOND 이하 각 division에서 최대 몇 page까지만 볼지 설정. "
            "기본값은 3이며, players-per-tier가 작을 때 수백 page를 조회하는 일을 방지한다."
        ),
    )

    parser.add_argument(
        "--league-queue",
        default="RANKED_SOLO_5x5",
        help="LEAGUE-V4 큐 이름. 기본값 RANKED_SOLO_5X5가 아니라 Riot 표기인 RANKED_SOLO_5x5를 사용",
    )

    parser.add_argument(
        "--platform-routing",
        default=PLATFORM_ROUTING,
        help="LEAGUE-V4 / SUMMONER-V4 platform routing. 한국 서버는 kr",
    )

    args = parser.parse_args()

    if args.convert_existing:
        input_csv = Path(args.convert_existing)
        output_csv = Path(args.output_csv) if args.output_csv else input_csv.parent / "battle_logs_app_ready.csv"
        app_dataset_dir = Path(args.app_dataset_dir) if args.app_dataset_dir else None

        summary = convert_existing_battle_logs_file(
            input_csv=input_csv,
            output_csv=output_csv,
            item_map_path=args.item_map,
            app_dataset_dir=app_dataset_dir,
        )

        print("\n========== 기존 battle_logs 변환 완료 ==========")
        print(f"input_csv: {input_csv}")
        print(f"output_csv: {output_csv}")
        if app_dataset_dir:
            print(f"app_dataset_dir: {app_dataset_dir}")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    tiers = split_csv_values(args.tiers)
    divisions = split_csv_values(args.divisions)

    collect_dataset(
        out_dir=args.out_dir,
        count_per_player=args.count,
        queue=args.queue,
        match_type=args.match_type,
        resume=not args.no_resume,
        item_map_path=args.item_map,
        app_dataset_dir=args.app_dataset_dir,
        skip_app_convert=args.skip_app_convert,
        auto_players=args.auto_players,
        tiers=tiers,
        players_per_tier=args.players_per_tier,
        divisions=divisions,
        league_queue=args.league_queue,
        platform_routing=args.platform_routing,
        exclude_existing_from_count=not args.include_existing_in_count,
        merge_existing=not args.no_merge_existing,
        max_match_scan_pages=args.max_match_scan_pages,
        league_max_pages_per_division=args.league_max_pages_per_division,
    )


if __name__ == "__main__":
    main()
