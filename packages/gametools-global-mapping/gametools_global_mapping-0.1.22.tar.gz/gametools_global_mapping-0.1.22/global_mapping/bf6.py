PLATFORM = {
    0: "unknown",
    1: "pc",
    2: "ps4",
    3: "xboxone",
    4: "ps5",
    5: "xboxseries",
    6: "common",
    7: "steam",
}
STATS_PLATFORM = {
    1: "pc",
    3: "xboxone",
    2: "ps4",
    5: "xboxseries",
    4: "ps5",
    6: "common",
    7: "steam",
}
PLATFORM_REVERSE = {
    "unknown": 0,
    "pc": 1,
    "ps4": 2,
    "xboxone": 3,
    "ps5": 4,
    "xboxseries": 5,
    "common": 6,
    "steam": 7,
}
PLATFORM_FESL = {
    0: "pc",
    1: "pc",
    2: "ps4",
    3: "xboxone",
    4: "ps4",
    5: "xboxone",
    6: "pc",
    7: "pc",
}
STATS_PLATFORM_REVERSE = {
    "pc": 1,
    "xboxone": 3,
    "ps4": 2,
    "xboxseries": 5,
    "ps5": 4,
    "xbox": 5,
    "psn": 4,
    "steam": 7,
}
REGIONS = {
    "aws-bah": "Asia",
    "aws-bom": "Asia",
    "aws-brz": "South America",
    "aws-cdg": "Europe",
    "aws-cmh": "South America",
    "aws-cpt": "Africa",
    "aws-dub": "Europe",
    "aws-fra": "Europe",
    "aws-hkg": "Asia",
    "aws-iad": "North America",
    "aws-icn": "South America",
    "aws-lhr": "Europe",
    "aws-nrt": "Asia",
    "aws-pdx": "North America",
    "aws-sin": "Asia",
    "aws-sjc": "North America",
    "aws-syd": "Oceania",
}
REGIONSLIST = {
    "asia": ["aws-bah", "aws-bom", "aws-hkg", "aws-nrt", "aws-sin"],
    "nam": ["aws-iad", "aws-pdx", "aws-sjc"],
    "sam": ["aws-brz", "aws-cmh", "aws-icn"],
    "eu": ["aws-cdg", "aws-dub", "aws-fra", "aws-lhr"],
    "afr": ["aws-cpt"],
    "oc": ["aws-syd"],
    "all": [
        "aws-bah",
        "aws-bom",
        "aws-hkg",
        "aws-nrt",
        "aws-sin",
        "aws-iad",
        "aws-pdx",
        "aws-sjc",
        "aws-brz",
        "aws-cmh",
        "aws-icn",
        "aws-cdg",
        "aws-dub",
        "aws-fra",
        "aws-lhr",
        "aws-cpt",
        "aws-syd",
    ],
}
SHORT_REGIONS = {
    "aws-bah": "asia",
    "aws-bom": "asia",
    "aws-brz": "sam",
    "aws-cdg": "eu",
    "aws-cmh": "sam",
    "aws-cpt": "afr",
    "aws-dub": "eu",
    "aws-fra": "eu",
    "aws-hkg": "asia",
    "aws-iad": "nam",
    "aws-icn": "sam",
    "aws-lhr": "eu",
    "aws-nrt": "asia",
    "aws-pdx": "nam",
    "aws-sin": "asia",
    "aws-sjc": "nam",
    "aws-syd": "oc",
}
MAPS = {
    "MP_Abbasid": "Siege of Cairo",
    "MP_Aftermath": "Empire State",
    "MP_Battery": "Iberian Offensive",
    "MP_Capstone": "Liberation Peak",
    "MP_Dumbo": "Manhattan Bridge",
    "MP_FireStorm": "Operation Firestorm",
    "MP_Limestone": "Saints Quarter",
    "MP_Outskirts": "New Sobek City",
    "MP_Tungsten": "Mirak Valley",
}
TO_GAME_MAPS = {
    "siege of cairo": "MP_Abbasid",
    "empire state": "MP_Aftermath",
    "iberian offensive": "MP_Battery",
    "liberation peak": "MP_Capstone",
    "manhattan bridge": "MP_Dumbo",
    "operation firestorm": "MP_FireStorm",
    "saints quarter": "MP_Limestone",
    "new sobek city": "MP_Outskirts",
    "mirak valley": "MP_Tungsten",
}
MAP_TRANSLATION_IDS = {
    "MP_Abbasid": "ID_MP_LVL_ABBASID_NAME",
    "MP_Aftermath": "ID_MP_LVL_AFTERMATH_NAME",
    "MP_Battery": "ID_MP_LVL_BATTERY_NAME",
    "MP_Capstone": "ID_ARRIVAL_MAP_CAPSTONE",
    "MP_Dumbo": "ID_MP_LVL_DUMBO_NAME",
    "MP_FireStorm": "ID_MP_LVL_FIRESTORM_NAME",
    "MP_Limestone": "ID_MP_LVL_LIMESTONE_NAME",
    "MP_Outskirts": "ID_MP_LVL_OUTSKIRTS_NAME",
    "MP_Tungsten": "ID_MP_LVL_TUNGSTEN_NAME",
}
MAP_PICTURES = {
    "MP_Abbasid": "https://cdn.gametools.network/maps/bf6/T_UI_Abbasid_Large_OPT-49a3761a.webp",
    "MP_Aftermath": "https://cdn.gametools.network/maps/bf6/T_UI_Aftermath_Large_OPT-bf883df1.webp",
    "MP_Battery": "https://cdn.gametools.network/maps/bf6/T_UI_Battery_Large_OPT-034d4636.webp",
    "MP_Capstone": "https://cdn.gametools.network/maps/bf6/T_UI_Capstone_Large_OPT-2ccae694.webp",
    "MP_Dumbo": "https://cdn.gametools.network/maps/bf6/T_UI_Dumbo_Large_OPT-20de031f.webp",
    "MP_FireStorm": "https://cdn.gametools.network/maps/bf6/T_UI_Firestorm_Large_OPT-45d582ad.webp",
    "MP_Limestone": "https://cdn.gametools.network/maps/bf6/T_UI_Limestone_Large_OPT-c9160897.webp",
    "MP_Outskirts": "https://cdn.gametools.network/maps/bf6/T_UI_Outskirts_Large_OPT-bf08f756.webp",
    "MP_Tungsten": "https://cdn.gametools.network/maps/bf6/T_UI_Tungsten_Large_OPT-935da06b.webp",
}
SMALLMODES = {
    "Breakthrough0": "BT",
    "BreakthroughSmall0": "BS",
    "ConquestSmall0": "CQ",
    "ModBuilderCustom0": "CM",
    "Rush0": "RS",
    "Conquest0": "CL",
}
MODES = {
    "Breakthrough0": "Breakthrough Large",
    "BreakthroughSmall0": "Breakthrough",
    "ConquestSmall0": "Conquest",
    "ModBuilderCustom0": "Custom",
    "Rush0": "Rush",
    "Conquest0": "Conquest large",
}
TO_GAME_MODES = {
    "breakthrough large": "Breakthrough0",
    "breakthrough": "BreakthroughSmall0",
    "conquest": "ConquestSmall0",
    "custom": "ModBuilderCustom0",
    "rush": "Rush0",
    "conquest large": "Conquest0",
}
STAT_MAPS = {
    "mpabbasid": {
        "mapName": "Siege of Cairo",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Abbasid_Large_OPT-49a3761a.webp",
    },
    "mpaftermath": {
        "mapName": "Empire State",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Aftermath_Large_OPT-bf883df1.webp",
    },
    "mpbattery": {
        "mapName": "Iberian Offensive",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Battery_Large_OPT-034d4636.webp",
    },
    "mpcapstone": {
        "mapName": "Liberation Peak",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Capstone_Large_OPT-2ccae694.webp",
    },
    "mpdumbo": {
        "mapName": "Manhattan Bridge",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Dumbo_Large_OPT-20de031f.webp",
    },
    "mpfirestorm": {
        "mapName": "Operation Firestorm",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Firestorm_Large_OPT-45d582ad.webp",
    },
    "mplimestone": {
        "mapName": "Saints Quarter",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Limestone_Large_OPT-c9160897.webp",
    },
    "mpoutskirts": {
        "mapName": "New Sobek City",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Outskirts_Large_OPT-bf08f756.webp",
    },
    "mptungsten": {
        "mapName": "Mirak Valley",
        "image": "https://cdn.gametools.network/maps/bf6/T_UI_Tungsten_Large_OPT-935da06b.webp",
    },
}
STAT_GAMEMODE = {
    "MP_Escalation0": {"gamemodeName": "Escalation", "image": ""},
    "MP_TeamDM0": {"gamemodeName": "Team deathmatch", "image": ""},
    "Conquest0": {"gamemodeName": "Conquest", "image": ""},
    "MP_KOTH0": {"gamemodeName": "King of the hill", "image": ""},
    "MP_SquadDM0": {"gamemodeName": "Squad deathmatch", "image": ""},
    "Breakthrough0": {"gamemodeName": "Breakthrough", "image": ""},
    "Rush0": {"gamemodeName": "Rush", "image": ""},
}
VEHICLES = {
    "air_panthera": {
        "type": "Air Combat",
        "vehicleName": "Panthera KHT",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_Eurocopter_VSD0001-8003028d.webp",
    },
    "air_m77efalchio": {
        "type": "Air Combat",
        "vehicleName": "M77E Falchion",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_AH64E_VSD0001-dd0a7df6.webp",
    },
    "sur_leoa4": {
        "type": "Ground Combat",
        "vehicleName": "Leo A4",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_Leopard_VSD0001-f8da51ee.webp",
    },
    "sur_strf09a4": {
        "type": "Ground Combat",
        "vehicleName": "Strf 09 A4",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_CV90_VSD0001-acd942b6.webp",
    },
    "sur_m1a2sepv3": {
        "type": "Ground Combat",
        "vehicleName": "M1A2 SEPv3",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_Abrams_VSD0001-5412a78d.webp",
    },
    "sur_cheetah1a2": {
        "type": "Ground Combat",
        "vehicleName": "Cheetah 1A2",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_Gepard_VSD0001-d796732f.webp",
    },
    "sur_glider96": {
        "type": "Ground Combat",
        "vehicleName": "Glider 96",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_MDV_Flyer60_VSD0005-1569869f.webp",
    },
    "sur_bradley": {
        "type": "Ground Combat",
        "vehicleName": "M3A3 Bradley",
        "image": "https://cdn.gametools.network/vehicles/bf6/T_UI_OB_VEH_Tank_Bradley_VSD0001_Dressing-66f252ca.webp",
    },
}
