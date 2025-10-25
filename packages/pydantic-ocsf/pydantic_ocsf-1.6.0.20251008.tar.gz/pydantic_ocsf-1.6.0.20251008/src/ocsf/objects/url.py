import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Self

from annotated_types import Ge, Lt
from pydantic import AnyUrl, computed_field, model_validator

from ocsf.objects.object import Object


class CategoryIds(IntEnum):
    UNKNOWN = 0
    ADULT_MATURE_CONTENT = 1
    PORNOGRAPHY = 3
    SEX_EDUCATION = 4
    INTIMATE_APPAREL_SWIMSUIT = 5
    NUDITY = 6
    EXTREME = 7
    SCAM_QUESTIONABLE_ILLEGAL = 9
    GAMBLING = 11
    VIOLENCE_HATE_RACISM = 14
    WEAPONS = 15
    ABORTION = 16
    HACKING = 17
    PHISHING = 18
    ENTERTAINMENT = 20
    BUSINESS_ECONOMY = 21
    ALTERNATIVE_SPIRITUALITY_BELIEF = 22
    ALCOHOL = 23
    TOBACCO = 24
    CONTROLLED_SUBSTANCES = 25
    CHILD_PORNOGRAPHY = 26
    EDUCATION = 27
    CHARITABLE_ORGANIZATIONS = 29
    ART_CULTURE = 30
    FINANCIAL_SERVICES = 31
    BROKERAGE_TRADING = 32
    GAMES = 33
    GOVERNMENT_LEGAL = 34
    MILITARY = 35
    POLITICAL_SOCIAL_ADVOCACY = 36
    HEALTH = 37
    TECHNOLOGY_INTERNET = 38
    SEARCH_ENGINES_PORTALS = 40
    MALICIOUS_SOURCES_MALNETS = 43
    MALICIOUS_OUTBOUND_DATA_BOTNETS = 44
    JOB_SEARCH_CAREERS = 45
    NEWS_MEDIA = 46
    PERSONALS_DATING = 47
    REFERENCE = 49
    MIXED_CONTENT_POTENTIALLY_ADULT = 50
    CHAT__IM__SMS = 51
    EMAIL = 52
    NEWSGROUPS_FORUMS = 53
    RELIGION = 54
    SOCIAL_NETWORKING = 55
    FILE_STORAGE_SHARING = 56
    REMOTE_ACCESS_TOOLS = 57
    SHOPPING = 58
    AUCTIONS = 59
    REAL_ESTATE = 60
    SOCIETY_DAILY_LIVING = 61
    PERSONAL_SITES = 63
    RESTAURANTS_DINING_FOOD = 64
    SPORTS_RECREATION = 65
    TRAVEL = 66
    VEHICLES = 67
    HUMOR_JOKES = 68
    SOFTWARE_DOWNLOADS = 71
    PEER_TO_PEER__P2P_ = 83
    AUDIO_VIDEO_CLIPS = 84
    OFFICE_BUSINESS_APPLICATIONS = 85
    PROXY_AVOIDANCE = 86
    FOR_KIDS = 87
    WEB_ADS_ANALYTICS = 88
    WEB_HOSTING = 89
    UNCATEGORIZED = 90
    SUSPICIOUS = 92
    SEXUAL_EXPRESSION = 93
    TRANSLATION = 95
    NON_VIEWABLE_INFRASTRUCTURE = 96
    CONTENT_SERVERS = 97
    PLACEHOLDERS = 98
    OTHER = 99
    SPAM = 101
    POTENTIALLY_UNWANTED_SOFTWARE = 102
    DYNAMIC_DNS_HOST = 103
    E_CARD_INVITATIONS = 106
    INFORMATIONAL = 107
    COMPUTER_INFORMATION_SECURITY = 108
    INTERNET_CONNECTED_DEVICES = 109
    INTERNET_TELEPHONY = 110
    ONLINE_MEETINGS = 111
    MEDIA_SHARING = 112
    RADIO_AUDIO_STREAMS = 113
    TV_VIDEO_STREAMS = 114
    PIRACY_COPYRIGHT_CONCERNS = 118
    MARIJUANA = 121

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return CategoryIds[obj]
        else:
            return CategoryIds(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ADULT_MATURE_CONTENT": "Adult/Mature Content",
            "PORNOGRAPHY": "Pornography",
            "SEX_EDUCATION": "Sex Education",
            "INTIMATE_APPAREL_SWIMSUIT": "Intimate Apparel/Swimsuit",
            "NUDITY": "Nudity",
            "EXTREME": "Extreme",
            "SCAM_QUESTIONABLE_ILLEGAL": "Scam/Questionable/Illegal",
            "GAMBLING": "Gambling",
            "VIOLENCE_HATE_RACISM": "Violence/Hate/Racism",
            "WEAPONS": "Weapons",
            "ABORTION": "Abortion",
            "HACKING": "Hacking",
            "PHISHING": "Phishing",
            "ENTERTAINMENT": "Entertainment",
            "BUSINESS_ECONOMY": "Business/Economy",
            "ALTERNATIVE_SPIRITUALITY_BELIEF": "Alternative Spirituality/Belief",
            "ALCOHOL": "Alcohol",
            "TOBACCO": "Tobacco",
            "CONTROLLED_SUBSTANCES": "Controlled Substances",
            "CHILD_PORNOGRAPHY": "Child Pornography",
            "EDUCATION": "Education",
            "CHARITABLE_ORGANIZATIONS": "Charitable Organizations",
            "ART_CULTURE": "Art/Culture",
            "FINANCIAL_SERVICES": "Financial Services",
            "BROKERAGE_TRADING": "Brokerage/Trading",
            "GAMES": "Games",
            "GOVERNMENT_LEGAL": "Government/Legal",
            "MILITARY": "Military",
            "POLITICAL_SOCIAL_ADVOCACY": "Political/Social Advocacy",
            "HEALTH": "Health",
            "TECHNOLOGY_INTERNET": "Technology/Internet",
            "SEARCH_ENGINES_PORTALS": "Search Engines/Portals",
            "MALICIOUS_SOURCES_MALNETS": "Malicious Sources/Malnets",
            "MALICIOUS_OUTBOUND_DATA_BOTNETS": "Malicious Outbound Data/Botnets",
            "JOB_SEARCH_CAREERS": "Job Search/Careers",
            "NEWS_MEDIA": "News/Media",
            "PERSONALS_DATING": "Personals/Dating",
            "REFERENCE": "Reference",
            "MIXED_CONTENT_POTENTIALLY_ADULT": "Mixed Content/Potentially Adult",
            "CHAT__IM__SMS": "Chat (IM)/SMS",
            "EMAIL": "Email",
            "NEWSGROUPS_FORUMS": "Newsgroups/Forums",
            "RELIGION": "Religion",
            "SOCIAL_NETWORKING": "Social Networking",
            "FILE_STORAGE_SHARING": "File Storage/Sharing",
            "REMOTE_ACCESS_TOOLS": "Remote Access Tools",
            "SHOPPING": "Shopping",
            "AUCTIONS": "Auctions",
            "REAL_ESTATE": "Real Estate",
            "SOCIETY_DAILY_LIVING": "Society/Daily Living",
            "PERSONAL_SITES": "Personal Sites",
            "RESTAURANTS_DINING_FOOD": "Restaurants/Dining/Food",
            "SPORTS_RECREATION": "Sports/Recreation",
            "TRAVEL": "Travel",
            "VEHICLES": "Vehicles",
            "HUMOR_JOKES": "Humor/Jokes",
            "SOFTWARE_DOWNLOADS": "Software Downloads",
            "PEER_TO_PEER__P2P_": "Peer-to-Peer (P2P)",
            "AUDIO_VIDEO_CLIPS": "Audio/Video Clips",
            "OFFICE_BUSINESS_APPLICATIONS": "Office/Business Applications",
            "PROXY_AVOIDANCE": "Proxy Avoidance",
            "FOR_KIDS": "For Kids",
            "WEB_ADS_ANALYTICS": "Web Ads/Analytics",
            "WEB_HOSTING": "Web Hosting",
            "UNCATEGORIZED": "Uncategorized",
            "SUSPICIOUS": "Suspicious",
            "SEXUAL_EXPRESSION": "Sexual Expression",
            "TRANSLATION": "Translation",
            "NON_VIEWABLE_INFRASTRUCTURE": "Non-Viewable/Infrastructure",
            "CONTENT_SERVERS": "Content Servers",
            "PLACEHOLDERS": "Placeholders",
            "OTHER": "Other",
            "SPAM": "Spam",
            "POTENTIALLY_UNWANTED_SOFTWARE": "Potentially Unwanted Software",
            "DYNAMIC_DNS_HOST": "Dynamic DNS Host",
            "E_CARD_INVITATIONS": "E-Card/Invitations",
            "INFORMATIONAL": "Informational",
            "COMPUTER_INFORMATION_SECURITY": "Computer/Information Security",
            "INTERNET_CONNECTED_DEVICES": "Internet Connected Devices",
            "INTERNET_TELEPHONY": "Internet Telephony",
            "ONLINE_MEETINGS": "Online Meetings",
            "MEDIA_SHARING": "Media Sharing",
            "RADIO_AUDIO_STREAMS": "Radio/Audio Streams",
            "TV_VIDEO_STREAMS": "TV/Video Streams",
            "PIRACY_COPYRIGHT_CONCERNS": "Piracy/Copyright Concerns",
            "MARIJUANA": "Marijuana",
        }
        return name_map[super().name]


class Url(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "url"

    # Recommended
    category_ids: list[CategoryIds] | None = None
    hostname: str | None = None
    path: str | None = None
    port: Annotated[int, Ge(0), Lt(65536)] | None = None
    query_string: str | None = None
    scheme: str | None = None
    url_string: AnyUrl | None = None

    # Optional
    domain: str | None = None
    resource_type: str | None = None
    subdomain: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def categories(self) -> list[str] | None:
        if self.category_ids is None:
            return None
        return [value.name for value in self.category_ids]

    @categories.setter
    def categories(self, value: list[str] | None) -> None:
        if value is None:
            self.category_ids = None
        else:
            self.category_ids = [CategoryIds[x] for x in value]

    @model_validator(mode="before")
    @classmethod
    def validate_categories_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "categories" in data and "category_ids" not in data:
            categories = re.sub(r"\W", "_", data.pop("categories").upper())
            data["category_ids"] = CategoryIds[categories]
        return data

    @model_validator(mode="after")
    def validate_categories_after(self) -> Self:
        if self.__pydantic_extra__ and "categories" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("categories")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["url_string", "path"]):
            raise ValueError("At least one of `url_string`, `path` must be provided")
        return self
