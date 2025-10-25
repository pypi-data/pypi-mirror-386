from enum import IntEnum, IntFlag

class MetatileBehavior(IntEnum):
    """Complete metatile behaviors from Pokemon Emerald decompilation"""
    NORMAL = 0
    SECRET_BASE_WALL = 1
    TALL_GRASS = 2
    LONG_GRASS = 3
    UNUSED_04 = 4
    UNUSED_05 = 5
    DEEP_SAND = 6
    SHORT_GRASS = 7
    CAVE = 8
    LONG_GRASS_SOUTH_EDGE = 9
    NO_RUNNING = 10
    INDOOR_ENCOUNTER = 11
    MOUNTAIN_TOP = 12
    BATTLE_PYRAMID_WARP = 13
    MOSSDEEP_GYM_WARP = 14
    MT_PYRE_HOLE = 15
    POND_WATER = 16
    INTERIOR_DEEP_WATER = 17
    DEEP_WATER = 18
    WATERFALL = 19
    SOOTOPOLIS_DEEP_WATER = 20
    OCEAN_WATER = 21
    PUDDLE = 22
    SHALLOW_WATER = 23
    UNUSED_SOOTOPOLIS_DEEP_WATER = 24
    NO_SURFACING = 25
    UNUSED_SOOTOPOLIS_DEEP_WATER_2 = 26
    STAIRS_OUTSIDE_ABANDONED_SHIP = 27
    SHOAL_CAVE_ENTRANCE = 28
    UNUSED_1D = 29
    UNUSED_1E = 30
    UNUSED_1F = 31
    ICE = 32
    SAND = 33
    SEAWEED = 34
    UNUSED_23 = 35
    ASHGRASS = 36
    FOOTPRINTS = 37
    THIN_ICE = 38
    CRACKED_ICE = 39
    HOT_SPRINGS = 40
    LAVARIDGE_GYM_B1F_WARP = 41
    SEAWEED_NO_SURFACING = 42
    REFLECTION_UNDER_BRIDGE = 43
    UNUSED_2C = 44
    UNUSED_2D = 45
    UNUSED_2E = 46
    UNUSED_2F = 47
    IMPASSABLE_EAST = 48
    IMPASSABLE_WEST = 49
    IMPASSABLE_NORTH = 50
    IMPASSABLE_SOUTH = 51
    IMPASSABLE_NORTHEAST = 52
    IMPASSABLE_NORTHWEST = 53
    IMPASSABLE_SOUTHEAST = 54
    IMPASSABLE_SOUTHWEST = 55
    JUMP_EAST = 56
    JUMP_WEST = 57
    JUMP_NORTH = 58
    JUMP_SOUTH = 59
    JUMP_NORTHEAST = 60
    JUMP_NORTHWEST = 61
    JUMP_SOUTHEAST = 62
    JUMP_SOUTHWEST = 63
    WALK_EAST = 64
    WALK_WEST = 65
    WALK_NORTH = 66
    WALK_SOUTH = 67
    SLIDE_EAST = 68
    SLIDE_WEST = 69
    SLIDE_NORTH = 70
    SLIDE_SOUTH = 71
    TRICK_HOUSE_PUZZLE_8_FLOOR = 72
    UNUSED_49 = 73
    UNUSED_4A = 74
    UNUSED_4B = 75
    UNUSED_4C = 76
    UNUSED_4D = 77
    UNUSED_4E = 78
    UNUSED_4F = 79
    EASTWARD_CURRENT = 80
    WESTWARD_CURRENT = 81
    NORTHWARD_CURRENT = 82
    SOUTHWARD_CURRENT = 83
    UNUSED_54 = 84
    UNUSED_55 = 85
    UNUSED_56 = 86
    UNUSED_57 = 87
    UNUSED_58 = 88
    UNUSED_59 = 89
    UNUSED_5A = 90
    UNUSED_5B = 91
    UNUSED_5C = 92
    UNUSED_5D = 93
    UNUSED_5E = 94
    UNUSED_5F = 95
    NON_ANIMATED_DOOR = 96
    LADDER = 97
    EAST_ARROW_WARP = 98
    WEST_ARROW_WARP = 99
    NORTH_ARROW_WARP = 100
    SOUTH_ARROW_WARP = 101
    CRACKED_FLOOR_HOLE = 102
    AQUA_HIDEOUT_WARP = 103
    LAVARIDGE_GYM_1F_WARP = 104
    ANIMATED_DOOR = 105
    UP_ESCALATOR = 106
    DOWN_ESCALATOR = 107
    WATER_DOOR = 108
    WATER_SOUTH_ARROW_WARP = 109
    DEEP_SOUTH_WARP = 110
    UNUSED_6F = 111
    BRIDGE_OVER_OCEAN = 112
    BRIDGE_OVER_POND_LOW = 113
    BRIDGE_OVER_POND_MED = 114
    BRIDGE_OVER_POND_HIGH = 115
    PACIFIDLOG_VERTICAL_LOG_TOP = 116
    PACIFIDLOG_VERTICAL_LOG_BOTTOM = 117
    PACIFIDLOG_HORIZONTAL_LOG_LEFT = 118
    PACIFIDLOG_HORIZONTAL_LOG_RIGHT = 119
    FORTREE_BRIDGE = 120
    UNUSED_79 = 121
    BRIDGE_OVER_POND_MED_EDGE_1 = 122
    BRIDGE_OVER_POND_MED_EDGE_2 = 123
    BRIDGE_OVER_POND_HIGH_EDGE_1 = 124
    BRIDGE_OVER_POND_HIGH_EDGE_2 = 125
    UNUSED_BRIDGE = 126
    BIKE_BRIDGE_OVER_BARRIER = 127
    COUNTER = 128
    UNUSED_81 = 129
    UNUSED_82 = 130
    PC = 131
    CABLE_BOX_RESULTS_1 = 132
    REGION_MAP = 133
    TELEVISION = 134
    POKEBLOCK_FEEDER = 135
    UNUSED_88 = 136
    SLOT_MACHINE = 137
    ROULETTE = 138
    CLOSED_SOOTOPOLIS_DOOR = 139
    TRICK_HOUSE_PUZZLE_DOOR = 140
    PETALBURG_GYM_DOOR = 141
    RUNNING_SHOES_INSTRUCTION = 142
    QUESTIONNAIRE = 143
    SECRET_BASE_SPOT_RED_CAVE = 144
    SECRET_BASE_SPOT_RED_CAVE_OPEN = 145
    SECRET_BASE_SPOT_BROWN_CAVE = 146
    SECRET_BASE_SPOT_BROWN_CAVE_OPEN = 147
    SECRET_BASE_SPOT_YELLOW_CAVE = 148
    SECRET_BASE_SPOT_YELLOW_CAVE_OPEN = 149
    SECRET_BASE_SPOT_TREE_LEFT = 150
    SECRET_BASE_SPOT_TREE_LEFT_OPEN = 151
    SECRET_BASE_SPOT_SHRUB = 152
    SECRET_BASE_SPOT_SHRUB_OPEN = 153
    SECRET_BASE_SPOT_BLUE_CAVE = 154
    SECRET_BASE_SPOT_BLUE_CAVE_OPEN = 155
    SECRET_BASE_SPOT_TREE_RIGHT = 156
    SECRET_BASE_SPOT_TREE_RIGHT_OPEN = 157
    UNUSED_9E = 158
    UNUSED_9F = 159
    BERRY_TREE_SOIL = 160
    UNUSED_A1 = 161
    UNUSED_A2 = 162
    UNUSED_A3 = 163
    UNUSED_A4 = 164
    UNUSED_A5 = 165
    UNUSED_A6 = 166
    UNUSED_A7 = 167
    UNUSED_A8 = 168
    UNUSED_A9 = 169
    UNUSED_AA = 170
    UNUSED_AB = 171
    UNUSED_AC = 172
    UNUSED_AD = 173
    UNUSED_AE = 174
    UNUSED_AF = 175
    SECRET_BASE_PC = 176
    SECRET_BASE_REGISTER_PC = 177
    SECRET_BASE_SCENERY = 178
    SECRET_BASE_TRAINER_SPOT = 179
    SECRET_BASE_DECORATION = 180
    HOLDS_SMALL_DECORATION = 181
    UNUSED_B6 = 182
    SECRET_BASE_NORTH_WALL = 183
    SECRET_BASE_BALLOON = 184
    SECRET_BASE_IMPASSABLE = 185
    SECRET_BASE_GLITTER_MAT = 186
    SECRET_BASE_JUMP_MAT = 187
    SECRET_BASE_SPIN_MAT = 188
    SECRET_BASE_SOUND_MAT = 189
    SECRET_BASE_BREAKABLE_DOOR = 190
    SECRET_BASE_SAND_ORNAMENT = 191
    IMPASSABLE_SOUTH_AND_NORTH = 192
    IMPASSABLE_WEST_AND_EAST = 193
    SECRET_BASE_HOLE = 194
    HOLDS_LARGE_DECORATION = 195
    SECRET_BASE_TV_SHIELD = 196
    PLAYER_ROOM_PC_ON = 197
    SECRET_BASE_DECORATION_BASE = 198
    SECRET_BASE_POSTER = 199
    UNUSED_C8 = 200
    UNUSED_C9 = 201
    UNUSED_CA = 202
    UNUSED_CB = 203
    UNUSED_CC = 204
    UNUSED_CD = 205
    UNUSED_CE = 206
    UNUSED_CF = 207
    MUDDY_SLOPE = 208
    BUMPY_SLOPE = 209
    CRACKED_FLOOR = 210
    ISOLATED_VERTICAL_RAIL = 211
    ISOLATED_HORIZONTAL_RAIL = 212
    VERTICAL_RAIL = 213
    HORIZONTAL_RAIL = 214
    UNUSED_D7 = 215
    UNUSED_D8 = 216
    UNUSED_D9 = 217
    UNUSED_DA = 218
    UNUSED_DB = 219
    UNUSED_DC = 220
    UNUSED_DD = 221
    UNUSED_DE = 222
    UNUSED_DF = 223
    PICTURE_BOOK_SHELF = 224
    BOOKSHELF = 225
    POKEMON_CENTER_BOOKSHELF = 226
    VASE = 227
    TRASH_CAN = 228
    SHOP_SHELF = 229
    BLUEPRINT = 230
    CABLE_BOX_RESULTS_2 = 231
    WIRELESS_BOX_RESULTS = 232
    TRAINER_HILL_TIMER = 233
    SKY_PILLAR_CLOSED_DOOR = 234
    UNUSED_EB = 235
    UNUSED_EC = 236
    UNUSED_ED = 237
    UNUSED_EE = 238
    UNUSED_EF = 239


class PokemonType(IntEnum):
    """Pokemon types in Emerald"""
    NORMAL = 0
    FIGHTING = 1
    FLYING = 2
    POISON = 3
    GROUND = 4
    ROCK = 5
    BUG = 6
    GHOST = 7
    STEEL = 8
    MYSTERY = 9  # Used for Curse
    FIRE = 10
    WATER = 11
    GRASS = 12
    ELECTRIC = 13
    PSYCHIC = 14
    ICE = 15
    DRAGON = 16
    DARK = 17


class PokemonSpecies(IntEnum):
    """Pokemon species IDs in Emerald (Hoenn Dex order)"""
    NONE = 0
    TREECKO = 1
    GROVYLE = 2
    SCEPTILE = 3
    TORCHIC = 4
    COMBUSKEN = 5
    BLAZIKEN = 6
    MUDKIP = 7
    MARSHTOMP = 8
    SWAMPERT = 9
    POOCHYENA = 10
    MIGHTYENA = 11
    ZIGZAGOON = 12
    LINOONE = 13
    WURMPLE = 14
    SILCOON = 15
    BEAUTIFLY = 16
    CASCOON = 17
    DUSTOX = 18
    LOTAD = 19
    LOMBRE = 20
    LUDICOLO = 21
    SEEDOT = 22
    NUZLEAF = 23
    SHIFTRY = 24
    TAILLOW = 25
    SWELLOW = 26
    WINGULL = 27
    PELIPPER = 28
    RALTS = 29
    KIRLIA = 30
    GARDEVOIR = 31
    SURSKIT = 32
    MASQUERAIN = 33
    SHROOMISH = 34
    BRELOOM = 35
    SLAKOTH = 36
    VIGOROTH = 37
    SLAKING = 38
    ABRA = 39
    KADABRA = 40
    ALAKAZAM = 41
    NINCADA = 42
    NINJASK = 43
    SHEDINJA = 44
    WHISMUR = 45
    LOUDRED = 46
    EXPLOUD = 47
    MAKUHITA = 48
    HARIYAMA = 49
    GOLDEEN = 50
    SEAKING = 51
    MAGIKARP = 52
    GYARADOS = 53
    AZURILL = 54
    MARILL = 55
    AZUMARILL = 56
    GEODUDE = 57
    GRAVELER = 58
    GOLEM = 59
    NOSEPASS = 60
    SKITTY = 61
    DELCATTY = 62
    ZUBAT = 63
    GOLBAT = 64
    CROBAT = 65
    TENTACOOL = 66
    TENTACRUEL = 67
    SABLEYE = 68
    MAWILE = 69
    ARON = 70
    LAIRON = 71
    AGGRON = 72
    MACHOP = 73
    MACHOKE = 74
    MACHAMP = 75
    MEDITITE = 76
    MEDICHAM = 77
    ELECTRIKE = 78
    MANECTRIC = 79
    PLUSLE = 80
    MINUN = 81
    MAGNEMITE = 82
    MAGNETON = 83
    VOLTORB = 84
    ELECTRODE = 85
    # Add more species as needed...


class Move(IntEnum):
    """Move IDs in Emerald"""
    NONE = 0
    POUND = 1
    KARATE_CHOP = 2
    DOUBLE_SLAP = 3
    COMET_PUNCH = 4
    MEGA_PUNCH = 5
    PAY_DAY = 6
    FIRE_PUNCH = 7
    ICE_PUNCH = 8
    THUNDER_PUNCH = 9
    SCRATCH = 10
    VICE_GRIP = 11
    GUILLOTINE = 12
    RAZOR_WIND = 13
    SWORDS_DANCE = 14
    CUT = 15
    GUST = 16
    WING_ATTACK = 17
    WHIRLWIND = 18
    FLY = 19
    BIND = 20
    SLAM = 21
    VINE_WHIP = 22
    STOMP = 23
    DOUBLE_KICK = 24
    MEGA_KICK = 25
    JUMP_KICK = 26
    ROLLING_KICK = 27
    SAND_ATTACK = 28
    HEADBUTT = 29
    HORN_ATTACK = 30
    FURY_ATTACK = 31
    HORN_DRILL = 32
    TACKLE = 33
    BODY_SLAM = 34
    WRAP = 35
    TAKE_DOWN = 36
    THRASH = 37
    DOUBLE_EDGE = 38
    TAIL_WHIP = 39
    POISON_STING = 40
    TWINEEDLE = 41
    PIN_MISSILE = 42
    LEER = 43
    BITE = 44
    GROWL = 45
    ROAR = 46
    SING = 47
    SUPERSONIC = 48
    SONIC_BOOM = 49
    DISABLE = 50
    ACID = 51
    EMBER = 52
    FLAMETHROWER = 53
    MIST = 54
    WATER_GUN = 55
    HYDRO_PUMP = 56
    SURF = 57
    ICE_BEAM = 58
    BLIZZARD = 59
    PSYBEAM = 60
    BUBBLE_BEAM = 61
    AURORA_BEAM = 62
    HYPER_BEAM = 63
    PECK = 64
    DRILL_PECK = 65
    SUBMISSION = 66
    LOW_KICK = 67
    COUNTER = 68
    SEISMIC_TOSS = 69
    STRENGTH = 70
    ABSORB = 71
    MEGA_DRAIN = 72
    LEECH_SEED = 73
    GROWTH = 74
    RAZOR_LEAF = 75
    SOLAR_BEAM = 76
    POISON_POWDER = 77
    STUN_SPORE = 78
    SLEEP_POWDER = 79
    PETAL_DANCE = 80
    STRING_SHOT = 81
    DRAGON_RAGE = 82
    FIRE_SPIN = 83
    THUNDER_SHOCK = 84
    THUNDERBOLT = 85
    THUNDER_WAVE = 86
    THUNDER = 87
    ROCK_THROW = 88
    EARTHQUAKE = 89
    FISSURE = 90
    DIG = 91
    TOXIC = 92
    CONFUSION = 93
    PSYCHIC = 94
    HYPNOSIS = 95
    MEDITATE = 96
    AGILITY = 97
    QUICK_ATTACK = 98
    RAGE = 99
    TELEPORT = 100
    NIGHT_SHADE = 101
    MIMIC = 102
    SCREECH = 103
    DOUBLE_TEAM = 104
    RECOVER = 105
    HARDEN = 106
    MINIMIZE = 107
    SMOKESCREEN = 108
    CONFUSE_RAY = 109
    WITHDRAW = 110
    DEFENSE_CURL = 111
    BARRIER = 112
    LIGHT_SCREEN = 113
    HAZE = 114
    REFLECT = 115
    FOCUS_ENERGY = 116
    BIDE = 117
    METRONOME = 118
    MIRROR_MOVE = 119
    SELFDESTRUCT = 120
    EGG_BOMB = 121
    LICK = 122
    SMOG = 123
    SLUDGE = 124
    BONE_CLUB = 125
    FIRE_BLAST = 126
    WATERFALL = 127
    CLAMP = 128
    SWIFT = 129
    SKULL_BASH = 130
    SPIKE_CANNON = 131
    CONSTRICT = 132
    AMNESIA = 133
    KINESIS = 134
    SOFTBOILED = 135
    HI_JUMP_KICK = 136
    GLARE = 137
    DREAM_EATER = 138
    POISON_GAS = 139
    BARRAGE = 140
    LEECH_LIFE = 141
    LOVELY_KISS = 142
    SKY_ATTACK = 143
    TRANSFORM = 144
    BUBBLE = 145
    DIZZY_PUNCH = 146
    SPORE = 147
    FLASH = 148
    PSYWAVE = 149
    SPLASH = 150
    ACID_ARMOR = 151
    CRABHAMMER = 152
    EXPLOSION = 153
    FURY_SWIPES = 154
    BONEMERANG = 155
    REST = 156
    ROCK_SLIDE = 157
    HYPER_FANG = 158
    SHARPEN = 159
    CONVERSION = 160
    TRI_ATTACK = 161
    SUPER_FANG = 162
    SLASH = 163
    SUBSTITUTE = 164
    STRUGGLE = 165
    # Add more moves as needed...


class Badge(IntFlag):
    """Gym badges in Emerald"""
    STONE = 1 << 0
    KNUCKLE = 1 << 1
    DYNAMO = 1 << 2
    HEAT = 1 << 3
    BALANCE = 1 << 4
    FEATHER = 1 << 5
    MIND = 1 << 6
    RAIN = 1 << 7
    
class MapLocation(IntEnum):
    """Maps location IDs to their names in Pokemon Emerald"""
    # Towns and Cities (Group 0)
    PETALBURG_CITY = 0x00
    SLATEPORT_CITY = 0x01
    MAUVILLE_CITY = 0x02
    RUSTBORO_CITY = 0x03
    FORTREE_CITY = 0x04
    LILYCOVE_CITY = 0x05
    MOSSDEEP_CITY = 0x06
    SOOTOPOLIS_CITY = 0x07
    EVER_GRANDE_CITY = 0x08
    LITTLEROOT_TOWN = 0x09
    OLDALE_TOWN = 0x0A
    DEWFORD_TOWN = 0x0B
    LAVARIDGE_TOWN = 0x0C
    FALLARBOR_TOWN = 0x0D
    VERDANTURF_TOWN = 0x0E
    PACIFIDLOG_TOWN = 0x0F
    
    # Routes (Group 0)
    ROUTE_101 = 0x10
    ROUTE_102 = 0x11
    ROUTE_103 = 0x12
    ROUTE_104 = 0x13
    ROUTE_105 = 0x14
    ROUTE_106 = 0x15
    ROUTE_107 = 0x16
    ROUTE_108 = 0x17
    ROUTE_109 = 0x18
    ROUTE_110 = 0x19
    ROUTE_111 = 0x1A
    ROUTE_112 = 0x1B
    ROUTE_113 = 0x1C
    ROUTE_114 = 0x1D
    ROUTE_115 = 0x1E
    ROUTE_116 = 0x1F
    ROUTE_117 = 0x20
    ROUTE_118 = 0x21
    ROUTE_119 = 0x22
    ROUTE_120 = 0x23
    ROUTE_121 = 0x24
    ROUTE_122 = 0x25
    ROUTE_123 = 0x26
    ROUTE_124 = 0x27
    ROUTE_125 = 0x28
    ROUTE_126 = 0x29
    ROUTE_127 = 0x2A
    ROUTE_128 = 0x2B
    ROUTE_129 = 0x2C
    ROUTE_130 = 0x2D
    ROUTE_131 = 0x2E
    ROUTE_132 = 0x2F
    ROUTE_133 = 0x30
    ROUTE_134 = 0x31
    
    # Underwater Routes (Group 0)
    UNDERWATER_ROUTE_124 = 0x32
    UNDERWATER_ROUTE_126 = 0x33
    UNDERWATER_ROUTE_127 = 0x34
    UNDERWATER_ROUTE_128 = 0x35
    UNDERWATER_ROUTE_129 = 0x36
    UNDERWATER_ROUTE_105 = 0x37
    UNDERWATER_ROUTE_125 = 0x38
    
    # Indoor Littleroot (Group 1)
    LITTLEROOT_TOWN_BRENDANS_HOUSE_1F = 0x100
    LITTLEROOT_TOWN_BRENDANS_HOUSE_2F = 0x101
    LITTLEROOT_TOWN_MAYS_HOUSE_1F = 0x102
    LITTLEROOT_TOWN_MAYS_HOUSE_2F = 0x103
    LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB = 0x104
    
    # Indoor Oldale (Group 2)
    OLDALE_TOWN_HOUSE1 = 0x200
    OLDALE_TOWN_HOUSE2 = 0x201
    OLDALE_TOWN_POKEMON_CENTER_1F = 0x202
    OLDALE_TOWN_POKEMON_CENTER_2F = 0x203
    OLDALE_TOWN_MART = 0x204
    
    # Indoor Dewford (Group 3)
    DEWFORD_TOWN_HOUSE1 = 0x300
    DEWFORD_TOWN_POKEMON_CENTER_1F = 0x301
    DEWFORD_TOWN_POKEMON_CENTER_2F = 0x302
    DEWFORD_TOWN_GYM = 0x303
    DEWFORD_TOWN_HALL = 0x304
    DEWFORD_TOWN_HOUSE2 = 0x305
    
    # Indoor Lavaridge (Group 4)
    LAVARIDGE_TOWN_HERB_SHOP = 0x400
    LAVARIDGE_TOWN_GYM_1F = 0x401
    LAVARIDGE_TOWN_GYM_B1F = 0x402
    LAVARIDGE_TOWN_HOUSE = 0x403
    LAVARIDGE_TOWN_MART = 0x404
    LAVARIDGE_TOWN_POKEMON_CENTER_1F = 0x405
    LAVARIDGE_TOWN_POKEMON_CENTER_2F = 0x406
    
    # Indoor Fallarbor (Group 5)
    FALLARBOR_TOWN_MART = 0x500
    FALLARBOR_TOWN_BATTLE_TENT_LOBBY = 0x501
    FALLARBOR_TOWN_BATTLE_TENT_CORRIDOR = 0x502
    FALLARBOR_TOWN_BATTLE_TENT_BATTLE_ROOM = 0x503
    FALLARBOR_TOWN_POKEMON_CENTER_1F = 0x504
    FALLARBOR_TOWN_POKEMON_CENTER_2F = 0x505
    FALLARBOR_TOWN_COZMOS_HOUSE = 0x506
    FALLARBOR_TOWN_MOVE_RELEARNERS_HOUSE = 0x507
    
    # Indoor Verdanturf (Group 6)
    VERDANTURF_TOWN_BATTLE_TENT_LOBBY = 0x600
    VERDANTURF_TOWN_BATTLE_TENT_CORRIDOR = 0x601
    VERDANTURF_TOWN_BATTLE_TENT_BATTLE_ROOM = 0x602
    VERDANTURF_TOWN_MART = 0x603
    VERDANTURF_TOWN_POKEMON_CENTER_1F = 0x604
    VERDANTURF_TOWN_POKEMON_CENTER_2F = 0x605
    VERDANTURF_TOWN_WANDAS_HOUSE = 0x606
    VERDANTURF_TOWN_FRIENDSHIP_RATERS_HOUSE = 0x607
    VERDANTURF_TOWN_HOUSE = 0x608
    
    # Indoor Pacifidlog (Group 7)
    PACIFIDLOG_TOWN_POKEMON_CENTER_1F = 0x700
    PACIFIDLOG_TOWN_POKEMON_CENTER_2F = 0x701
    PACIFIDLOG_TOWN_HOUSE1 = 0x702
    PACIFIDLOG_TOWN_HOUSE2 = 0x703
    PACIFIDLOG_TOWN_HOUSE3 = 0x704
    PACIFIDLOG_TOWN_HOUSE4 = 0x705
    PACIFIDLOG_TOWN_HOUSE5 = 0x706
    
    # Indoor Petalburg (Group 8)
    PETALBURG_CITY_WALLYS_HOUSE = 0x800
    PETALBURG_CITY_GYM = 0x801
    PETALBURG_CITY_HOUSE1 = 0x802
    PETALBURG_CITY_HOUSE2 = 0x803
    PETALBURG_CITY_POKEMON_CENTER_1F = 0x804
    PETALBURG_CITY_POKEMON_CENTER_2F = 0x805
    PETALBURG_CITY_MART = 0x806
    
    # Indoor Slateport (Group 9)
    SLATEPORT_CITY_STERNS_SHIPYARD_1F = 0x900
    SLATEPORT_CITY_STERNS_SHIPYARD_2F = 0x901
    SLATEPORT_CITY_BATTLE_TENT_LOBBY = 0x902
    SLATEPORT_CITY_BATTLE_TENT_CORRIDOR = 0x903
    SLATEPORT_CITY_BATTLE_TENT_BATTLE_ROOM = 0x904
    SLATEPORT_CITY_NAME_RATERS_HOUSE = 0x905
    SLATEPORT_CITY_POKEMON_FAN_CLUB = 0x906
    SLATEPORT_CITY_OCEANIC_MUSEUM_1F = 0x907
    SLATEPORT_CITY_OCEANIC_MUSEUM_2F = 0x908
    SLATEPORT_CITY_HARBOR = 0x909
    SLATEPORT_CITY_HOUSE = 0x90A
    SLATEPORT_CITY_POKEMON_CENTER_1F = 0x90B
    SLATEPORT_CITY_POKEMON_CENTER_2F = 0x90C
    SLATEPORT_CITY_MART = 0x90D
    
    # Indoor Mauville (Group 10)
    MAUVILLE_CITY_GYM = 0xA00
    MAUVILLE_CITY_BIKE_SHOP = 0xA01
    MAUVILLE_CITY_HOUSE1 = 0xA02
    MAUVILLE_CITY_GAME_CORNER = 0xA03
    MAUVILLE_CITY_HOUSE2 = 0xA04
    MAUVILLE_CITY_POKEMON_CENTER_1F = 0xA05
    MAUVILLE_CITY_POKEMON_CENTER_2F = 0xA06
    MAUVILLE_CITY_MART = 0xA07
    
    # Indoor Rustboro (Group 11)
    RUSTBORO_CITY_DEVON_CORP_1F = 0xB00
    RUSTBORO_CITY_DEVON_CORP_2F = 0xB01
    RUSTBORO_CITY_DEVON_CORP_3F = 0xB02
    RUSTBORO_CITY_GYM = 0xB03
    RUSTBORO_CITY_POKEMON_SCHOOL = 0xB04
    RUSTBORO_CITY_POKEMON_CENTER_1F = 0xB05
    RUSTBORO_CITY_POKEMON_CENTER_2F = 0xB06
    RUSTBORO_CITY_MART = 0xB07
    RUSTBORO_CITY_FLAT1_1F = 0xB08
    RUSTBORO_CITY_FLAT1_2F = 0xB09
    RUSTBORO_CITY_HOUSE1 = 0xB0A
    RUSTBORO_CITY_CUTTERS_HOUSE = 0xB0B
    RUSTBORO_CITY_HOUSE2 = 0xB0C
    RUSTBORO_CITY_FLAT2_1F = 0xB0D
    RUSTBORO_CITY_FLAT2_2F = 0xB0E
    RUSTBORO_CITY_FLAT2_3F = 0xB0F
    RUSTBORO_CITY_HOUSE3 = 0xB10
    
    # Indoor Route 104 (Group 18)
    ROUTE_104_MR_BRINEYS_HOUSE = 0x1200
    ROUTE_104_PRETTY_PETAL_FLOWER_SHOP = 0x1201
    
    # Indoor Route 111 (Group 19)
    ROUTE_111_WINSTRATE_FAMILYS_HOUSE = 0x1300
    ROUTE_111_OLD_LADYS_REST_STOP = 0x1301
    
    # Indoor Route 112 (Group 20)
    ROUTE_112_CABLE_CAR_STATION = 0x1400
    MT_CHIMNEY_CABLE_CAR_STATION = 0x1401
    
    # Indoor Route 114 (Group 21)
    ROUTE_114_FOSSIL_MANIACS_HOUSE = 0x1500
    ROUTE_114_FOSSIL_MANIACS_TUNNEL = 0x1501
    ROUTE_114_LANETTES_HOUSE = 0x1502
    
    # Indoor Route 116 (Group 22)
    ROUTE_116_TUNNELERS_REST_HOUSE = 0x1600
    
    # Indoor Route 117 (Group 23)
    ROUTE_117_POKEMON_DAY_CARE = 0x1700
    
    # Indoor Route 121 (Group 24)
    ROUTE_121_SAFARI_ZONE_ENTRANCE = 0x1800
    
    # Indoor Fortree (Group 12)
    FORTREE_CITY_HOUSE1 = 0xC00
    FORTREE_CITY_GYM = 0xC01
    FORTREE_CITY_POKEMON_CENTER_1F = 0xC02
    FORTREE_CITY_POKEMON_CENTER_2F = 0xC03
    FORTREE_CITY_MART = 0xC04
    FORTREE_CITY_HOUSE2 = 0xC05
    FORTREE_CITY_HOUSE3 = 0xC06
    FORTREE_CITY_HOUSE4 = 0xC07
    FORTREE_CITY_HOUSE5 = 0xC08
    FORTREE_CITY_DECORATION_SHOP = 0xC09
    
    # Indoor Lilycove (Group 13)
    LILYCOVE_CITY_COVE_LILY_MOTEL_1F = 0xD00
    LILYCOVE_CITY_COVE_LILY_MOTEL_2F = 0xD01
    LILYCOVE_CITY_LILYCOVE_MUSEUM_1F = 0xD02
    LILYCOVE_CITY_LILYCOVE_MUSEUM_2F = 0xD03
    LILYCOVE_CITY_CONTEST_LOBBY = 0xD04
    LILYCOVE_CITY_CONTEST_HALL = 0xD05
    LILYCOVE_CITY_POKEMON_CENTER_1F = 0xD06
    LILYCOVE_CITY_POKEMON_CENTER_2F = 0xD07
    LILYCOVE_CITY_UNUSED_MART = 0xD08
    LILYCOVE_CITY_POKEMON_TRAINER_FAN_CLUB = 0xD09
    LILYCOVE_CITY_HARBOR = 0xD0A
    LILYCOVE_CITY_MOVE_DELETERS_HOUSE = 0xD0B
    LILYCOVE_CITY_HOUSE1 = 0xD0C
    LILYCOVE_CITY_HOUSE2 = 0xD0D
    LILYCOVE_CITY_HOUSE3 = 0xD0E
    LILYCOVE_CITY_HOUSE4 = 0xD0F
    LILYCOVE_CITY_DEPARTMENT_STORE_1F = 0xD10
    LILYCOVE_CITY_DEPARTMENT_STORE_2F = 0xD11
    LILYCOVE_CITY_DEPARTMENT_STORE_3F = 0xD12
    LILYCOVE_CITY_DEPARTMENT_STORE_4F = 0xD13
    LILYCOVE_CITY_DEPARTMENT_STORE_5F = 0xD14
    LILYCOVE_CITY_DEPARTMENT_STORE_ROOFTOP = 0xD15
    LILYCOVE_CITY_DEPARTMENT_STORE_ELEVATOR = 0xD16
    
    # Indoor Mossdeep (Group 14)
    MOSSDEEP_CITY_GYM = 0xE00
    MOSSDEEP_CITY_HOUSE1 = 0xE01
    MOSSDEEP_CITY_HOUSE2 = 0xE02
    MOSSDEEP_CITY_POKEMON_CENTER_1F = 0xE03
    MOSSDEEP_CITY_POKEMON_CENTER_2F = 0xE04
    MOSSDEEP_CITY_MART = 0xE05
    MOSSDEEP_CITY_HOUSE3 = 0xE06
    MOSSDEEP_CITY_STEVENS_HOUSE = 0xE07
    MOSSDEEP_CITY_HOUSE4 = 0xE08
    MOSSDEEP_CITY_SPACE_CENTER_1F = 0xE09
    MOSSDEEP_CITY_SPACE_CENTER_2F = 0xE0A
    MOSSDEEP_CITY_GAME_CORNER_1F = 0xE0B
    MOSSDEEP_CITY_GAME_CORNER_B1F = 0xE0C
    
    # Indoor Sootopolis (Group 15)
    SOOTOPOLIS_CITY_GYM_1F = 0xF00
    SOOTOPOLIS_CITY_GYM_B1F = 0xF01
    SOOTOPOLIS_CITY_POKEMON_CENTER_1F = 0xF02
    SOOTOPOLIS_CITY_POKEMON_CENTER_2F = 0xF03
    SOOTOPOLIS_CITY_MART = 0xF04
    SOOTOPOLIS_CITY_HOUSE1 = 0xF05
    SOOTOPOLIS_CITY_HOUSE2 = 0xF06
    SOOTOPOLIS_CITY_HOUSE3 = 0xF07
    SOOTOPOLIS_CITY_HOUSE4 = 0xF08
    SOOTOPOLIS_CITY_HOUSE5 = 0xF09
    SOOTOPOLIS_CITY_HOUSE6 = 0xF0A
    SOOTOPOLIS_CITY_HOUSE7 = 0xF0B
    SOOTOPOLIS_CITY_LOTAD_AND_SEEDOT_HOUSE = 0xF0C
    SOOTOPOLIS_CITY_MYSTERY_EVENTS_HOUSE_1F = 0xF0D
    SOOTOPOLIS_CITY_MYSTERY_EVENTS_HOUSE_B1F = 0xF0E
    
    # Indoor Ever Grande (Group 16)
    EVER_GRANDE_CITY_SIDNEYS_ROOM = 0x1000
    EVER_GRANDE_CITY_PHOEBES_ROOM = 0x1001
    EVER_GRANDE_CITY_GLACIAS_ROOM = 0x1002
    EVER_GRANDE_CITY_DRAKES_ROOM = 0x1003
    EVER_GRANDE_CITY_CHAMPIONS_ROOM = 0x1004
    EVER_GRANDE_CITY_HALL1 = 0x1005
    EVER_GRANDE_CITY_HALL2 = 0x1006
    EVER_GRANDE_CITY_HALL3 = 0x1007
    EVER_GRANDE_CITY_HALL4 = 0x1008
    EVER_GRANDE_CITY_HALL5 = 0x1009
    EVER_GRANDE_CITY_POKEMON_LEAGUE_1F = 0x100A
    EVER_GRANDE_CITY_HALL_OF_FAME = 0x100B
    EVER_GRANDE_CITY_POKEMON_CENTER_1F = 0x100C
    EVER_GRANDE_CITY_POKEMON_CENTER_2F = 0x100D
    EVER_GRANDE_CITY_POKEMON_LEAGUE_2F = 0x100E
    
    # Dungeons (Group 17)
    METEOR_FALLS_1F_1R = 0x1100
    METEOR_FALLS_1F_2R = 0x1101
    METEOR_FALLS_B1F_1R = 0x1102
    METEOR_FALLS_B1F_2R = 0x1103
    RUSTURF_TUNNEL = 0x1104
    UNDERWATER_SOOTOPOLIS_CITY = 0x1105
    DESERT_RUINS = 0x1106
    GRANITE_CAVE_1F = 0x1107
    GRANITE_CAVE_B1F = 0x1108
    GRANITE_CAVE_B2F = 0x1109
    GRANITE_CAVE_STEVENS_ROOM = 0x110A
    PETALBURG_WOODS = 0x110B
    MT_CHIMNEY = 0x110C
    JAGGED_PASS = 0x110D
    FIERY_PATH = 0x110E
    MT_PYRE_1F = 0x110F
    MT_PYRE_2F = 0x1110
    MT_PYRE_3F = 0x1111
    MT_PYRE_4F = 0x1112
    MT_PYRE_5F = 0x1113
    MT_PYRE_6F = 0x1114
    MT_PYRE_EXTERIOR = 0x1115
    MT_PYRE_SUMMIT = 0x1116
    AQUA_HIDEOUT_1F = 0x1117
    AQUA_HIDEOUT_B1F = 0x1118
    AQUA_HIDEOUT_B2F = 0x1119
    UNDERWATER_SEAFLOOR_CAVERN = 0x111A
    SEAFLOOR_CAVERN_ENTRANCE = 0x111B
    SEAFLOOR_CAVERN_ROOM1 = 0x111C
    SEAFLOOR_CAVERN_ROOM2 = 0x111D
    SEAFLOOR_CAVERN_ROOM3 = 0x111E
    SEAFLOOR_CAVERN_ROOM4 = 0x111F
    SEAFLOOR_CAVERN_ROOM5 = 0x1120
    SEAFLOOR_CAVERN_ROOM6 = 0x1121
    SEAFLOOR_CAVERN_ROOM7 = 0x1122
    SEAFLOOR_CAVERN_ROOM8 = 0x1123
    SEAFLOOR_CAVERN_ROOM9 = 0x1124
    CAVE_OF_ORIGIN_ENTRANCE = 0x1125
    CAVE_OF_ORIGIN_1F = 0x1126
    CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1 = 0x1127
    CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP2 = 0x1128
    CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP3 = 0x1129
    CAVE_OF_ORIGIN_B1F = 0x112A
    VICTORY_ROAD_1F = 0x112B
    VICTORY_ROAD_B1F = 0x112C
    VICTORY_ROAD_B2F = 0x112D
    SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM = 0x112E
    SHOAL_CAVE_LOW_TIDE_INNER_ROOM = 0x112F
    SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM = 0x1130
    SHOAL_CAVE_LOW_TIDE_LOWER_ROOM = 0x1131
    SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM = 0x1132
    SHOAL_CAVE_HIGH_TIDE_INNER_ROOM = 0x1133
    NEW_MAUVILLE_ENTRANCE = 0x1134
    NEW_MAUVILLE_INSIDE = 0x1135
    ABANDONED_SHIP_DECK = 0x1136
    ABANDONED_SHIP_CORRIDORS_1F = 0x1137
    ABANDONED_SHIP_ROOMS_1F = 0x1138
    ABANDONED_SHIP_CORRIDORS_B1F = 0x1139
    ABANDONED_SHIP_ROOMS_B1F = 0x113A
    ABANDONED_SHIP_ROOMS2_B1F = 0x113B
    ABANDONED_SHIP_UNDERWATER1 = 0x113C
    ABANDONED_SHIP_ROOM_B1F = 0x113D
    ABANDONED_SHIP_ROOMS2_1F = 0x113E
    ABANDONED_SHIP_CAPTAINS_OFFICE = 0x113F
    ABANDONED_SHIP_UNDERWATER2 = 0x1140
    ABANDONED_SHIP_HIDDEN_FLOOR_CORRIDORS = 0x1141
    ABANDONED_SHIP_HIDDEN_FLOOR_ROOMS = 0x1142
    ISLAND_CAVE = 0x1143
    ANCIENT_TOMB = 0x1144
    UNDERWATER_ROUTE134 = 0x1145
    UNDERWATER_SEALED_CHAMBER = 0x1146
    SEALED_CHAMBER_OUTER_ROOM = 0x1147
    SEALED_CHAMBER_INNER_ROOM = 0x1148
    SCORCHED_SLAB = 0x1149
    AQUA_HIDEOUT_UNUSED_RUBY_MAP1 = 0x114A
    AQUA_HIDEOUT_UNUSED_RUBY_MAP2 = 0x114B
    AQUA_HIDEOUT_UNUSED_RUBY_MAP3 = 0x114C
    SKY_PILLAR_ENTRANCE = 0x114D
    SKY_PILLAR_OUTSIDE = 0x114E
    SKY_PILLAR_1F = 0x114F
    SKY_PILLAR_2F = 0x1150
    SKY_PILLAR_3F = 0x1151
    SKY_PILLAR_4F = 0x1152
    SHOAL_CAVE_LOW_TIDE_ICE_ROOM = 0x1153
    SKY_PILLAR_5F = 0x1154
    SKY_PILLAR_TOP = 0x1155
    MAGMA_HIDEOUT_1F = 0x1156
    MAGMA_HIDEOUT_2F_1R = 0x1157
    MAGMA_HIDEOUT_2F_2R = 0x1158
    MAGMA_HIDEOUT_3F_1R = 0x1159
    MAGMA_HIDEOUT_3F_2R = 0x115A
    MAGMA_HIDEOUT_4F = 0x115B
    MAGMA_HIDEOUT_3F_3R = 0x115C
    MAGMA_HIDEOUT_2F_3R = 0x115D
    MIRAGE_TOWER_1F = 0x115E
    MIRAGE_TOWER_2F = 0x115F
    MIRAGE_TOWER_3F = 0x1160
    MIRAGE_TOWER_4F = 0x1161
    DESERT_UNDERPASS = 0x1162
    ARTISAN_CAVE_B1F = 0x1163
    ARTISAN_CAVE_1F = 0x1164
    UNDERWATER_MARINE_CAVE = 0x1165
    MARINE_CAVE_ENTRANCE = 0x1166
    MARINE_CAVE_END = 0x1167
    TERRA_CAVE_ENTRANCE = 0x1168
    TERRA_CAVE_END = 0x1169
    ALTERING_CAVE = 0x116A
    METEOR_FALLS_STEVENS_CAVE = 0x116B
    
    # Indoor Route 109 (Group 26)
    ROUTE_109_SEASHORE_HOUSE = 0x1A00
    
    # Indoor Route 110 (Group 27)
    ROUTE_110_TRICK_HOUSE_ENTRANCE = 0x1B00
    ROUTE_110_TRICK_HOUSE_END = 0x1B01
    ROUTE_110_TRICK_HOUSE_CORRIDOR = 0x1B02
    ROUTE_110_TRICK_HOUSE_PUZZLE1 = 0x1B03
    ROUTE_110_TRICK_HOUSE_PUZZLE2 = 0x1B04
    ROUTE_110_TRICK_HOUSE_PUZZLE3 = 0x1B05
    ROUTE_110_TRICK_HOUSE_PUZZLE4 = 0x1B06
    ROUTE_110_TRICK_HOUSE_PUZZLE5 = 0x1B07
    ROUTE_110_TRICK_HOUSE_PUZZLE6 = 0x1B08
    ROUTE_110_TRICK_HOUSE_PUZZLE7 = 0x1B09
    ROUTE_110_TRICK_HOUSE_PUZZLE8 = 0x1B0A
    ROUTE_110_SEASIDE_CYCLING_ROAD_SOUTH_ENTRANCE = 0x1B0B
    ROUTE_110_SEASIDE_CYCLING_ROAD_NORTH_ENTRANCE = 0x1B0C
    
    # Indoor Route 113 (Group 28)
    ROUTE_113_GLASS_WORKSHOP = 0x1C00
    
    # Indoor Route 123 (Group 29)
    ROUTE_123_BERRY_MASTERS_HOUSE = 0x1D00
    
    # Indoor Route 119 (Group 30)
    ROUTE_119_WEATHER_INSTITUTE_1F = 0x1E00
    ROUTE_119_WEATHER_INSTITUTE_2F = 0x1E01
    ROUTE_119_HOUSE = 0x1E02
    
    # Indoor Route 124 (Group 31)
    ROUTE_124_DIVING_TREASURE_HUNTERS_HOUSE = 0x1F00
    
    # Special Areas (Group 25)
    SAFARI_ZONE_NORTHWEST = 0x1900
    SAFARI_ZONE_NORTH = 0x1901
    SAFARI_ZONE_SOUTHWEST = 0x1902
    SAFARI_ZONE_SOUTH = 0x1903
    BATTLE_FRONTIER_OUTSIDE_WEST = 0x1904
    BATTLE_FRONTIER_BATTLE_TOWER_LOBBY = 0x1905
    BATTLE_FRONTIER_BATTLE_TOWER_ELEVATOR = 0x1906
    BATTLE_FRONTIER_BATTLE_TOWER_CORRIDOR = 0x1907
    BATTLE_FRONTIER_BATTLE_TOWER_BATTLE_ROOM = 0x1908
    SOUTHERN_ISLAND_EXTERIOR = 0x1909
    SOUTHERN_ISLAND_INTERIOR = 0x190A
    SAFARI_ZONE_REST_HOUSE = 0x190B
    SAFARI_ZONE_NORTHEAST = 0x190C
    SAFARI_ZONE_SOUTHEAST = 0x190D
    BATTLE_FRONTIER_OUTSIDE_EAST = 0x190E
    BATTLE_FRONTIER_BATTLE_TOWER_MULTI_PARTNER_ROOM = 0x190F
    BATTLE_FRONTIER_BATTLE_TOWER_MULTI_CORRIDOR = 0x1910
    BATTLE_FRONTIER_BATTLE_TOWER_MULTI_BATTLE_ROOM = 0x1911
    BATTLE_FRONTIER_BATTLE_DOME_LOBBY = 0x1912
    BATTLE_FRONTIER_BATTLE_DOME_CORRIDOR = 0x1913
    BATTLE_FRONTIER_BATTLE_DOME_PRE_BATTLE_ROOM = 0x1914
    BATTLE_FRONTIER_BATTLE_DOME_BATTLE_ROOM = 0x1915
    BATTLE_FRONTIER_BATTLE_PALACE_LOBBY = 0x1916
    BATTLE_FRONTIER_BATTLE_PALACE_CORRIDOR = 0x1917
    BATTLE_FRONTIER_BATTLE_PALACE_BATTLE_ROOM = 0x1918
    BATTLE_FRONTIER_BATTLE_PYRAMID_LOBBY = 0x1919
    BATTLE_FRONTIER_BATTLE_PYRAMID_FLOOR = 0x191A
    BATTLE_FRONTIER_BATTLE_PYRAMID_TOP = 0x191B
    BATTLE_FRONTIER_BATTLE_ARENA_LOBBY = 0x191C
    BATTLE_FRONTIER_BATTLE_ARENA_CORRIDOR = 0x191D
    BATTLE_FRONTIER_BATTLE_ARENA_BATTLE_ROOM = 0x191E
    BATTLE_FRONTIER_BATTLE_FACTORY_LOBBY = 0x191F
    BATTLE_FRONTIER_BATTLE_FACTORY_PRE_BATTLE_ROOM = 0x1920
    BATTLE_FRONTIER_BATTLE_FACTORY_BATTLE_ROOM = 0x1921
    BATTLE_FRONTIER_BATTLE_PIKE_LOBBY = 0x1922
    BATTLE_FRONTIER_BATTLE_PIKE_CORRIDOR = 0x1923
    BATTLE_FRONTIER_BATTLE_PIKE_THREE_PATH_ROOM = 0x1924
    BATTLE_FRONTIER_BATTLE_PIKE_ROOM_NORMAL = 0x1925
    BATTLE_FRONTIER_BATTLE_PIKE_ROOM_FINAL = 0x1926
    BATTLE_FRONTIER_BATTLE_PIKE_ROOM_WILD_MONS = 0x1927
    BATTLE_FRONTIER_RANKING_HALL = 0x1928
    BATTLE_FRONTIER_LOUNGE1 = 0x1929
    BATTLE_FRONTIER_EXCHANGE_SERVICE_CORNER = 0x192A
    BATTLE_FRONTIER_LOUNGE2 = 0x192B
    BATTLE_FRONTIER_LOUNGE3 = 0x192C
    BATTLE_FRONTIER_LOUNGE4 = 0x192D
    BATTLE_FRONTIER_SCOTTS_HOUSE = 0x192E
    BATTLE_FRONTIER_LOUNGE5 = 0x192F
    BATTLE_FRONTIER_LOUNGE6 = 0x1930
    BATTLE_FRONTIER_LOUNGE7 = 0x1931
    BATTLE_FRONTIER_RECEPTION_GATE = 0x1932
    BATTLE_FRONTIER_LOUNGE8 = 0x1933
    BATTLE_FRONTIER_LOUNGE9 = 0x1934
    BATTLE_FRONTIER_POKEMON_CENTER_1F = 0x1935
    BATTLE_FRONTIER_POKEMON_CENTER_2F = 0x1936
    BATTLE_FRONTIER_MART = 0x1937
    FARAWAY_ISLAND_ENTRANCE = 0x1938
    FARAWAY_ISLAND_INTERIOR = 0x1939
    BIRTH_ISLAND_EXTERIOR = 0x193A
    BIRTH_ISLAND_HARBOR = 0x193B
    TRAINER_HILL_ENTRANCE = 0x193C
    TRAINER_HILL_1F = 0x193D
    TRAINER_HILL_2F = 0x193E
    TRAINER_HILL_3F = 0x193F
    TRAINER_HILL_4F = 0x1940
    TRAINER_HILL_ROOF = 0x1941
    NAVEL_ROCK_EXTERIOR = 0x1942
    NAVEL_ROCK_HARBOR = 0x1943
    NAVEL_ROCK_ENTRANCE = 0x1944
    NAVEL_ROCK_B1F = 0x1945
    NAVEL_ROCK_FORK = 0x1946
    NAVEL_ROCK_UP1 = 0x1947
    NAVEL_ROCK_UP2 = 0x1948
    NAVEL_ROCK_UP3 = 0x1949
    NAVEL_ROCK_UP4 = 0x194A
    NAVEL_ROCK_TOP = 0x194B
    NAVEL_ROCK_DOWN01 = 0x194C
    NAVEL_ROCK_DOWN02 = 0x194D
    NAVEL_ROCK_DOWN03 = 0x194E
    NAVEL_ROCK_DOWN04 = 0x194F
    NAVEL_ROCK_DOWN05 = 0x1950
    NAVEL_ROCK_DOWN06 = 0x1951
    NAVEL_ROCK_DOWN07 = 0x1952
    NAVEL_ROCK_DOWN08 = 0x1953
    NAVEL_ROCK_DOWN09 = 0x1954
    NAVEL_ROCK_DOWN10 = 0x1955
    NAVEL_ROCK_DOWN11 = 0x1956
    NAVEL_ROCK_BOTTOM = 0x1957
    TRAINER_HILL_ELEVATOR = 0x1958

class Tileset(IntEnum):
    NONE = 0
    TOWN = 1
    CITY = 2
    ROUTE = 3
    UNDERGROUND = 4
    UNDERWATER = 5
    OCEAN_ROUTE = 6
    UNKNOWN = 7
    INDOOR = 8
    SECRET_BASE = 9

class StatusCondition(IntFlag):
    """Status conditions for Pokemon in Emerald"""
    NONE = 0
    SLEEP_MASK = 0b111  # Bits 0-2
    SLEEP = 0b001  # For name display purposes
    POISON = 0b1000  # Bit 3
    BURN = 0b10000  # Bit 4
    FREEZE = 0b100000  # Bit 5
    PARALYSIS = 0b1000000  # Bit 6
    
    @property
    def is_asleep(self) -> bool:
        """Check if the Pokémon is asleep (any value in bits 0-2)"""
        return bool(int(self) & 0b111)
    
    def get_status_name(self) -> str:
        """Get a human-readable status name"""
        if self.is_asleep:
            return "SLEEP"
        elif self & StatusCondition.PARALYSIS:
            return "PARALYSIS"
        elif self & StatusCondition.FREEZE:
            return "FREEZE"
        elif self & StatusCondition.BURN:
            return "BURN"
        elif self & StatusCondition.POISON:
            return "POISON"
        return "OK"

    def _find_map_buffer_addresses(self):
        """Find the map buffer addresses by scanning for the BackupMapLayout structure"""
        # The BackupMapLayout structure is in COMMON_DATA (IWRAM) at gBackupMapLayout
        # We need to find where it's located in memory
        
        # Try to find the BackupMapLayout by looking for reasonable width/height values
        # The structure is: s32 width, s32 height, u16 *map
        for offset in range(0, 0x8000 - 12, 4):  # Search in IWRAM (0x03000000)
            try:
                # Read width and height (both should be reasonable values)
                width = (
                    (self.memory[0x03000000 + offset] << 24) |
                    (self.memory[0x03000000 + offset + 1] << 16) |
                    (self.memory[0x03000000 + offset + 2] << 8) |
                    self.memory[0x03000000 + offset + 3]
                )
                height = (
                    (self.memory[0x03000000 + offset + 4] << 24) |
                    (self.memory[0x03000000 + offset + 5] << 16) |
                    (self.memory[0x03000000 + offset + 6] << 8) |
                    self.memory[0x03000000 + offset + 7]
                )
                
                # Width and height should be reasonable values (typically 15-100)
                if 10 <= width <= 200 and 10 <= height <= 200:
                    # Read the map pointer (should point to EWRAM)
                    map_ptr = (
                        (self.memory[0x03000000 + offset + 8] << 24) |
                        (self.memory[0x03000000 + offset + 9] << 16) |
                        (self.memory[0x03000000 + offset + 10] << 8) |
                        self.memory[0x03000000 + offset + 11]
                    )
                    
                    # Map pointer should be in EWRAM range (0x02000000-0x02040000)
                    if 0x02000000 <= map_ptr <= 0x02040000:
                        self.backup_map_layout_addr = 0x03000000 + offset
                        self.map_buffer_addr = map_ptr
                        self.map_width = width
                        self.map_height = height
                        return True
            except:
                continue
        return False

    def read_current_tile_behavior(self) -> MetatileBehavior:
        """
        Reads the metatile behavior at the player's current position.
        Returns a MetatileBehavior enum value.
        """
        if not hasattr(self, 'map_buffer_addr'):
            if not self._find_map_buffer_addresses():
                return MetatileBehavior.NORMAL
        
        # Get player coordinates
        x, y = self.read_coordinates()
        
        # The map buffer uses MAP_OFFSET (7) for border tiles
        # So we need to add MAP_OFFSET to get the correct index
        map_x = x + 7  # MAP_OFFSET
        map_y = y + 7  # MAP_OFFSET
        
        # Calculate index in the map buffer
        index = map_x + map_y * self.map_width
        
        # Read the metatile value (16-bit)
        metatile_addr = self.map_buffer_addr + (index * 2)
        metatile_value = (
            (self.memory[metatile_addr + 1] << 8) |
            self.memory[metatile_addr]
        )
        
        # Extract metatile ID (lower 10 bits)
        metatile_id = metatile_value & 0x03FF
        
        # Get the behavior from the metatile attributes
        # This is a simplified approach - in the real game, it would look up
        # the behavior in the tileset's metatile attributes table
        # For now, we'll use the metatile ID as a proxy for behavior
        # (This is not 100% accurate but works for most cases)
        try:
            return MetatileBehavior(metatile_id & 0xFF)
        except ValueError:
            return MetatileBehavior.NORMAL

    def read_map_metatiles(self, x_start: int = 0, y_start: int = 0, width: int = None, height: int = None) -> list[list[tuple[int, MetatileBehavior]]]:
        """
        Read a section of the current map's metatiles.
        
        Args:
            x_start: Starting X coordinate (relative to map, not player)
            y_start: Starting Y coordinate (relative to map, not player)
            width: Width of area to read (None for full map width)
            height: Height of area to read (None for full map height)
            
        Returns:
            2D list of (metatile_id, behavior) tuples
        """
        if not hasattr(self, 'map_buffer_addr'):
            if not self._find_map_buffer_addresses():
                return []
        
        if width is None:
            width = self.map_width
        if height is None:
            height = self.map_height
        
        # Clamp to map bounds
        width = min(width, self.map_width - x_start)
        height = min(height, self.map_height - y_start)
        
        metatiles = []
        
        for y in range(y_start, y_start + height):
            row = []
            for x in range(x_start, x_start + width):
                # Calculate index in the map buffer
                index = x + y * self.map_width
                
                # Read the metatile value (16-bit)
                metatile_addr = self.map_buffer_addr + (index * 2)
                metatile_value = (
                    (self.memory[metatile_addr + 1] << 8) |
                    self.memory[metatile_addr]
                )
                
                # Extract metatile ID (lower 10 bits)
                metatile_id = metatile_value & 0x03FF
                
                # Extract collision (bits 10-11)
                collision = (metatile_value & 0x0C00) >> 10
                
                # Extract elevation (bits 12-15)
                elevation = (metatile_value & 0xF000) >> 12
                
                # Get behavior (simplified - using metatile ID as proxy)
                try:
                    behavior = MetatileBehavior(metatile_id & 0xFF)
                except ValueError:
                    behavior = MetatileBehavior.NORMAL
                
                row.append((metatile_id, behavior))
            metatiles.append(row)
        
        return metatiles

    def read_map_around_player(self, radius: int = 7) -> list[list[tuple[int, MetatileBehavior]]]:
        """
        Read the map area around the player.
        
        Args:
            radius: How many tiles in each direction to read
            
        Returns:
            2D list of (metatile_id, behavior) tuples centered on player
        """
        if not hasattr(self, 'map_buffer_addr'):
            if not self._find_map_buffer_addresses():
                return []
        
        # Get player coordinates
        player_x, player_y = self.read_coordinates()
        
        # Calculate the area to read (with MAP_OFFSET adjustment)
        map_x = player_x + 7  # MAP_OFFSET
        map_y = player_y + 7  # MAP_OFFSET
        
        x_start = max(0, map_x - radius)
        y_start = max(0, map_y - radius)
        x_end = min(self.map_width, map_x + radius + 1)
        y_end = min(self.map_height, map_y + radius + 1)
        
        width = x_end - x_start
        height = y_end - y_start
        
        return self.read_map_metatiles(x_start, y_start, width, height)

    def get_metatile_info_at(self, x: int, y: int) -> dict:
        """
        Get detailed information about a metatile at the given coordinates.
        
        Args:
            x: X coordinate (relative to player's position)
            y: Y coordinate (relative to player's position)
            
        Returns:
            Dictionary with metatile information
        """
        if not hasattr(self, 'map_buffer_addr'):
            if not self._find_map_buffer_addresses():
                return {}
        
        # Get player coordinates
        player_x, player_y = self.read_coordinates()
        
        # Calculate absolute map coordinates
        map_x = player_x + 7 + x  # MAP_OFFSET + relative position
        map_y = player_y + 7 + y  # MAP_OFFSET + relative position
        
        # Check bounds
        if not (0 <= map_x < self.map_width and 0 <= map_y < self.map_height):
            return {}
        
        # Calculate index in the map buffer
        index = map_x + map_y * self.map_width
        
        # Read the metatile value (16-bit)
        metatile_addr = self.map_buffer_addr + (index * 2)
        metatile_value = (
            (self.memory[metatile_addr + 1] << 8) |
            self.memory[metatile_addr]
        )
        
        # Extract components
        metatile_id = metatile_value & 0x03FF
        collision = (metatile_value & 0x0C00) >> 10
        elevation = (metatile_value & 0xF000) >> 12
        
        # Get behavior
        try:
            behavior = MetatileBehavior(metatile_id & 0xFF)
        except ValueError:
            behavior = MetatileBehavior.NORMAL
        
        return {
            'metatile_id': metatile_id,
            'behavior': behavior,
            'behavior_name': behavior.name,
            'collision': collision,
            'elevation': elevation,
            'raw_value': metatile_value,
            'map_x': map_x,
            'map_y': map_y,
            'relative_x': x,
            'relative_y': y
        }

    def is_tile_passable(self, x: int, y: int) -> bool:
        """
        Check if a tile at the given coordinates is passable.
        
        Args:
            x: X coordinate (relative to player's position)
            y: Y coordinate (relative to player's position)
            
        Returns:
            True if the tile is passable, False otherwise
        """
        info = self.get_metatile_info_at(x, y)
        if not info:
            return False
        
        # Check collision value (0 = passable, 1-3 = impassable)
        return info['collision'] == 0

    def is_tile_encounter_tile(self, x: int, y: int) -> bool:
        """
        Check if a tile can trigger wild encounters.
        
        Args:
            x: X coordinate (relative to player's position)
            y: Y coordinate (relative to player's position)
            
        Returns:
            True if the tile can trigger encounters, False otherwise
        """
        info = self.get_metatile_info_at(x, y)
        if not info:
            return False
        
        behavior = info['behavior']
        
        # Check for encounter tiles based on behavior
        encounter_behaviors = {
            MetatileBehavior.TALL_GRASS,
            MetatileBehavior.LONG_GRASS,
            MetatileBehavior.UNUSED_05,
            MetatileBehavior.DEEP_SAND,
            MetatileBehavior.CAVE,
            MetatileBehavior.INDOOR_ENCOUNTER,
            MetatileBehavior.POND_WATER,
            MetatileBehavior.INTERIOR_DEEP_WATER,
            MetatileBehavior.DEEP_WATER,
            MetatileBehavior.OCEAN_WATER,
            MetatileBehavior.SEAWEED,
            MetatileBehavior.ASHGRASS,
            MetatileBehavior.FOOTPRINTS,
            MetatileBehavior.SEAWEED_NO_SURFACING
        }
        
        return behavior in encounter_behaviors

    def is_tile_surfable(self, x: int, y: int) -> bool:
        """
        Check if a tile can be surfed on.
        
        Args:
            x: X coordinate (relative to player's position)
            y: Y coordinate (relative to player's position)
            
        Returns:
            True if the tile can be surfed, False otherwise
        """
        info = self.get_metatile_info_at(x, y)
        if not info:
            return False
        
        behavior = info['behavior']
        
        # Check for surfable tiles based on behavior
        surfable_behaviors = {
            MetatileBehavior.POND_WATER,
            MetatileBehavior.INTERIOR_DEEP_WATER,
            MetatileBehavior.DEEP_WATER,
            MetatileBehavior.SOOTOPOLIS_DEEP_WATER,
            MetatileBehavior.OCEAN_WATER,
            MetatileBehavior.NO_SURFACING,
            MetatileBehavior.SEAWEED,
            MetatileBehavior.SEAWEED_NO_SURFACING
        }
        
        return behavior in surfable_behaviors
