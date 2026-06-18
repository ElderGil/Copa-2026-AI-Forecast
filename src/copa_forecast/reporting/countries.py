from __future__ import annotations


TEAM_DISPLAY_NAMES_PT_BR = {
    "Algeria": "Argélia",
    "Argentina": "Argentina",
    "Australia": "Austrália",
    "Austria": "Áustria",
    "Belgium": "Bélgica",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    "Brazil": "Brasil",
    "Cabo Verde": "Cabo Verde",
    "Canada": "Canadá",
    "Colombia": "Colômbia",
    "Congo DR": "RD Congo",
    "Croatia": "Croácia",
    "Curaçao": "Curaçao",
    "Czechia": "Tchéquia",
    "Côte d'Ivoire": "Costa do Marfim",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Ghana": "Gana",
    "Haiti": "Haiti",
    "IR Iran": "Irã",
    "Iraq": "Iraque",
    "Japan": "Japão",
    "Jordan": "Jordânia",
    "Korea Republic": "Coreia do Sul",
    "Mexico": "México",
    "Morocco": "Marrocos",
    "Netherlands": "Países Baixos",
    "New Zealand": "Nova Zelândia",
    "Norway": "Noruega",
    "Panama": "Panamá",
    "Paraguay": "Paraguai",
    "Portugal": "Portugal",
    "Qatar": "Catar",
    "Saudi Arabia": "Arábia Saudita",
    "Scotland": "Escócia",
    "Senegal": "Senegal",
    "South Africa": "África do Sul",
    "Spain": "Espanha",
    "Sweden": "Suécia",
    "Switzerland": "Suíça",
    "Tunisia": "Tunísia",
    "Türkiye": "Turquia",
    "USA": "Estados Unidos",
    "Uruguay": "Uruguai",
    "Uzbekistan": "Uzbequistão",
}


FIFA_ALPHA3_TO_ALPHA2 = {
    "ALG": "DZ",
    "ARG": "AR",
    "AUS": "AU",
    "AUT": "AT",
    "BEL": "BE",
    "BIH": "BA",
    "BRA": "BR",
    "CAN": "CA",
    "CIV": "CI",
    "CMR": "CM",
    "COD": "CD",
    "COL": "CO",
    "CPV": "CV",
    "CRO": "HR",
    "CUW": "CW",
    "CZE": "CZ",
    "ECU": "EC",
    "EGY": "EG",
    "ESP": "ES",
    "FRA": "FR",
    "GER": "DE",
    "GHA": "GH",
    "ENG": "GB-ENG",
    "HAI": "HT",
    "IRN": "IR",
    "IRQ": "IQ",
    "JOR": "JO",
    "JPN": "JP",
    "KOR": "KR",
    "KSA": "SA",
    "MAR": "MA",
    "MEX": "MX",
    "NED": "NL",
    "NOR": "NO",
    "NZL": "NZ",
    "PAN": "PA",
    "PAR": "PY",
    "POR": "PT",
    "QAT": "QA",
    "RSA": "ZA",
    "SCO": "GB-SCT",
    "SEN": "SN",
    "SUI": "CH",
    "SWE": "SE",
    "TUN": "TN",
    "TUR": "TR",
    "URU": "UY",
    "USA": "US",
    "UZB": "UZ",
}


SUBDIVISION_FLAGS = {
    "GB-ENG": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
    "GB-SCT": "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",
}


def display_team_name(team_name: str) -> str:
    return TEAM_DISPLAY_NAMES_PT_BR.get(team_name, team_name)


def flag_emoji(flag_code: str | None) -> str:
    if not flag_code:
        return ""
    code = flag_code.upper()
    alpha2 = FIFA_ALPHA3_TO_ALPHA2.get(code, code)
    if alpha2 in SUBDIVISION_FLAGS:
        return SUBDIVISION_FLAGS[alpha2]
    if len(alpha2) != 2 or not alpha2.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in alpha2)
