#!/usr/bin/env python3
"""*catssm64pyport0.1.py — cat's SM64 PC-port style Python engine (FILES_OFF).

Full course set inspired by sm64-port / Super Mario 64 structure:
  Castle Grounds hub + Courses 1–15 (BoB … Rainbow Ride).

FILES_OFF: no ROM, no ripped textures/models/audio — procedural geometry +
software 3D + synthesized feel. Original clean-room tribute, not a decomp.

Install:  python -m pip install pygame
Run:      python "*catssm64pyport0.1.py"

Controls (sm64-port style):
  WASD / Arrows   move (camera-relative)
  Space           jump (chain = double / triple)
  Shift+Space     long jump (while running)
  Shift (air)     ground pound
  Ctrl / Z (air)  dive
  Ctrl / Z (gnd)  punch / crouch slide
  Q / E / Mouse   Lakitu camera
  Esc             course select
"""

FILES_OFF = True

# Course unlock gates (session stars) — PC-port hub pacing
STAR_GATES = {
    "Castle Grounds": 0,
    "Bob-omb Battlefield": 0,
    "Whomp's Fortress": 1,
    "Jolly Roger Bay": 3,
    "Cool, Cool Mountain": 3,
    "Big Boo's Haunt": 12,
    "Hazy Maze Cave": 3,
    "Lethal Lava Land": 8,
    "Shifting Sand Land": 8,
    "Dire, Dire Docks": 30,
    "Snowman's Land": 10,
    "Wet-Dry World": 10,
    "Tall, Tall Mountain": 10,
    "Tiny-Huge Island": 10,
    "Tick Tock Clock": 15,
    "Rainbow Ride": 15,
}

import pygame
import sys
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
HALF_W, HALF_H = WIDTH // 2, HEIGHT // 2
FOV_FACTOR = HALF_W / math.tan(math.radians(45))
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("acs's sm64 py port 0.1  [FILES_OFF]")
clock = pygame.time.Clock()

# --- FILES_OFF SFX (procedural) ---
def _sfx_tone(freq, ms, vol=0.25):
    import array as _arr
    rate = 22050
    n = max(1, int(rate * ms / 1000))
    buf = _arr.array("h")
    amp = int(32767 * vol)
    period = max(1, int(rate / max(1, freq)))
    for i in range(n):
        buf.append(amp if (i % period) < period // 2 else -amp)
    return pygame.mixer.Sound(buffer=buf)

try:
    pygame.mixer.init(22050, -16, 1, 512)
    SFX = {
        "jump": _sfx_tone(420, 80, 0.18),
        "coin": _sfx_tone(980, 70, 0.2),
        "star": _sfx_tone(660, 220, 0.22),
        "hurt": _sfx_tone(140, 120, 0.25),
        "pound": _sfx_tone(90, 100, 0.28),
        "1up": _sfx_tone(520, 180, 0.22),
    }
except Exception:
    SFX = {}

def play_sfx(name):
    s = SFX.get(name)
    if s:
        try:
            s.play()
        except Exception:
            pass


SKY_BLUE       = (100, 149, 237)
GRASS_GREEN    = (50, 160, 60)
DARK_GREEN     = (30, 120, 30)
STONE_GRAY     = (220, 220, 220)
DARK_GRAY      = (140, 140, 140)
ROOF_RED       = (180, 40, 40)
BLACK          = (20, 20, 20)
WHITE          = (255, 255, 255)
YELLOW         = (255, 230, 0)
MARIO_RED      = (255, 50, 50)
MARIO_BLUE     = (0, 70, 180)
WOOD_BROWN     = (140, 100, 60)
TRUNK_BROWN    = (120, 80, 40)
TREE_GREEN     = (40, 140, 40)
SAND_YELLOW    = (210, 180, 100)
LAVA_RED       = (220, 60, 20)
LAVA_ORANGE    = (255, 120, 30)
SNOW_WHITE     = (240, 245, 255)
ICE_BLUE       = (180, 210, 240)
WATER_BLUE     = (50, 120, 210)
DEEP_WATER     = (20, 60, 150)
PURPLE         = (120, 40, 160)
CAVE_BROWN     = (100, 80, 55)
CAVE_DARK      = (70, 55, 40)
METAL_GRAY     = (170, 175, 180)
GOLD           = (230, 190, 40)
CLOCK_BEIGE    = (220, 200, 160)
RAINBOW_PINK   = (255, 150, 200)
RAINBOW_CYAN   = (100, 240, 255)
RAINBOW_LIME   = (150, 255, 100)
MANSION_PURPLE = (90, 70, 110)
MANSION_GREEN  = (60, 90, 60)
DOCK_BLUE      = (30, 80, 160)
VOLCANO_GRAY   = (90, 80, 75)
VOLCANO_RED    = (170, 50, 30)
PYRAMID_TAN    = (200, 170, 110)
PYRAMID_DARK   = (160, 130, 80)
CANNON_BLACK   = (40, 40, 40)
NES_BLUE       = (92, 148, 252)
STAR_YELLOW    = (255, 255, 100)
PARCHMENT      = (250, 240, 200)
INK_COLOR      = (50, 40, 100)
STONE_PATH     = (200, 200, 200)
BRICK_RED      = (160, 60, 50)
DARK_BROWN     = (80, 50, 25)
FENCE_BROWN    = (110, 75, 40)
MOAT_BLUE      = (40, 100, 200)
SKY_SNOW       = (180, 200, 230)
SKY_LAVA       = (60, 20, 10)
SKY_CAVE       = (40, 35, 30)
SKY_UNDERWATER = (20, 50, 100)
SKY_DESERT     = (220, 180, 120)
SKY_MANSION    = (30, 20, 40)
SKY_RAINBOW    = (140, 160, 255)
CHAIN_GRAY     = (80, 80, 80)
LIGHT_DIR      = (0.577, 0.577, 0.577)

try:
    title_font  = pygame.font.SysFont("Arial Black", 55, bold=True)
    letter_font = pygame.font.SysFont("Georgia", 30, italic=True)
    menu_font   = pygame.font.SysFont("Arial", 28, bold=True)
    hud_font    = pygame.font.SysFont("Courier New", 18, bold=True)
    select_font = pygame.font.SysFont("Arial", 22, bold=True)
    star_font   = pygame.font.SysFont("Arial Black", 36, bold=True)
    small_font  = pygame.font.SysFont("Arial", 16)
except:
    title_font  = pygame.font.Font(None, 70)
    letter_font = pygame.font.Font(None, 36)
    menu_font   = pygame.font.Font(None, 40)
    hud_font    = pygame.font.Font(None, 22)
    select_font = pygame.font.Font(None, 28)
    star_font   = pygame.font.Font(None, 44)
    small_font  = pygame.font.Font(None, 20)

# ============================================================
# SM64 Behavior Script System (ported from sm64-port)
# Opcodes match behavior_script.h / behavior_script.c
# ============================================================

# --- Behavior Opcodes ---
BHV_BEGIN                    = 0x00
BHV_DELAY                    = 0x01
BHV_CALL                     = 0x02
BHV_RETURN                   = 0x03
BHV_GOTO                     = 0x04
BHV_BEGIN_REPEAT             = 0x05
BHV_END_REPEAT               = 0x06
BHV_END_REPEAT_CONTINUE      = 0x07
BHV_BEGIN_LOOP               = 0x08
BHV_END_LOOP                 = 0x09
BHV_BREAK                    = 0x0A
BHV_BREAK_UNUSED             = 0x0B
BHV_CALL_NATIVE              = 0x0C
BHV_ADD_FLOAT                = 0x0D
BHV_SET_FLOAT                = 0x0E
BHV_ADD_INT                  = 0x0F
BHV_SET_INT                  = 0x10
BHV_OR_INT                   = 0x11
BHV_BIT_CLEAR                = 0x12
BHV_SET_INT_RAND_RSHIFT      = 0x13
BHV_SET_RANDOM_FLOAT         = 0x14
BHV_SET_RANDOM_INT           = 0x15
BHV_ADD_RANDOM_FLOAT         = 0x16
BHV_ADD_INT_RAND_RSHIFT      = 0x17
BHV_CMD_NOP_1                = 0x18
BHV_CMD_NOP_2                = 0x19
BHV_CMD_NOP_3                = 0x1A
BHV_SET_MODEL                = 0x1B
BHV_SPAWN_CHILD              = 0x1C
BHV_DEACTIVATE               = 0x1D
BHV_DROP_TO_FLOOR            = 0x1E
BHV_SUM_FLOAT                = 0x1F
BHV_SUM_INT                  = 0x20
BHV_BILLBOARD                = 0x21
BHV_HIDE                     = 0x22
BHV_SET_HITBOX               = 0x23
BHV_CMD_NOP_4                = 0x24
BHV_DELAY_VAR                = 0x25
BHV_BEGIN_REPEAT_UNUSED      = 0x26
BHV_LOAD_ANIMATIONS          = 0x27
BHV_ANIMATE                  = 0x28
BHV_SPAWN_CHILD_WITH_PARAM   = 0x29
BHV_LOAD_COLLISION_DATA      = 0x2A
BHV_SET_HITBOX_WITH_OFFSET   = 0x2B
BHV_SPAWN_OBJ                = 0x2C
BHV_SET_HOME                 = 0x2D
BHV_SET_HURTBOX              = 0x2E
BHV_SET_INTERACT_TYPE        = 0x2F
BHV_SET_OBJ_PHYSICS          = 0x30
BHV_SET_INTERACT_SUBTYPE     = 0x31
BHV_SCALE                    = 0x32
BHV_PARENT_BIT_CLEAR         = 0x33
BHV_ANIMATE_TEXTURE          = 0x34
BHV_DISABLE_RENDERING        = 0x35
BHV_SET_INT_UNUSED           = 0x36
BHV_SPAWN_WATER_DROPLET      = 0x37

BHV_PROC_CONTINUE = 0
BHV_PROC_BREAK = 1

# --- Object List IDs ---
OBJ_LIST_DEFAULT      = 0
OBJ_LIST_SURFACE      = 1
OBJ_LIST_POLELIKE     = 2
OBJ_LIST_SPAWNER      = 3
OBJ_LIST_UNIMPORTANT  = 4
OBJ_LIST_LEVEL        = 5
OBJ_LIST_GENACTOR     = 6

# --- Object Field Indices --- (matching object_fields.h)
O_FIELD_START = 0x00
OFFLAGS = 0x01
ODIALOGRESPONSE = 0x02
ODIALOGSTATE = 0x02
OUNK94 = 0x03
OINTANGIBLETIMER = 0x05
OPOSX = 0x06
OPOSY = 0x07
OPOSZ = 0x08
OVELX = 0x09
OVELY = 0x0A
OVELZ = 0x0B
OFORWARDVEL = 0x0C
OLEFTVEL = 0x0D
OUPVEL = 0x0E
OMOVEANGLEPITCH = 0x0F
OMOVEANGLEYAW = 0x10
OMOVEANGLEROLL = 0x11
OFACEANGLEPITCH = 0x12
OFACEANGLEYAW = 0x13
OFACEANGLEROLL = 0x14
OGRAPHYOFFSET = 0x15
OACTIVEPARTICLEFLAGS = 0x16
OGRAVITY = 0x17
OFLOORHEIGHT = 0x18
OMOVEFLAGS = 0x19
OANIMSTATE = 0x1A
OANGLEVELPITCH = 0x23
OANGLEVELYAW = 0x24
OANGLEVELROLL = 0x25
OANIMATIONS = 0x26
OHELDSTATE = 0x27
OWALLHITBOXRADIUS = 0x28
ODRAGSTRENGTH = 0x29
OINTERACTTYPE = 0x2A
OINTERACTSTATUS = 0x2B
OPARENTRELATIVEPOSX = 0x2C
OPARENTRELATIVEPOSY = 0x2D
OPARENTRELATIVEPOSZ = 0x2E
OBHVPARAMS2NDBYTE = 0x2F
OACTION = 0x31
OSUBACTION = 0x32
OTIMER = 0x33
OBOUNCINESS = 0x34
ODISTANCETOMARIO = 0x35
OANGLETOMARIO = 0x36
OHOMEX = 0x37
OHOMEY = 0x38
OHOMEZ = 0x39
OFRICTION = 0x3A
OBUOYANCY = 0x3B
OSOUNDSTATEID = 0x3C
OOPACITY = 0x3D
ODAMAGEORCOINVALUE = 0x3E
OHEALTH = 0x3F
OBHVPARAMS = 0x40
OPREVACTION = 0x41
OINTERACTIONSUBTYPE = 0x42
OCOLLISIONDISTANCE = 0x43
ONUMLOOTCOINS = 0x44
ODRAWINGDISTANCE = 0x45
OROOM = 0x46
OUNUSEDBHVPARAMS = 0x48
OWALLANGLE = 0x4B
OFLOORTYPE = 0x4C
OFLOORROOM = 0x4C
OANGLETOHOME = 0x4D
OFLOOR = 0x4E
ODEATHSOUND = 0x4F

# --- Object Flags ---
OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE        = 1 << 0
OBJ_FLAG_MOVE_XZ_USING_FVEL              = 1 << 1
OBJ_FLAG_MOVE_Y_WITH_TERMINAL_VEL        = 1 << 2
OBJ_FLAG_SET_FACE_YAW_TO_MOVE_YAW        = 1 << 3
OBJ_FLAG_SET_FACE_ANGLE_TO_MOVE_ANGLE    = 1 << 4
OBJ_FLAG_COMPUTE_DIST_TO_MARIO           = 1 << 6
OBJ_FLAG_ACTIVE_FROM_AFAR                = 1 << 7
OBJ_FLAG_TRANSFORM_RELATIVE_TO_PARENT    = 1 << 9
OBJ_FLAG_HOLDABLE                        = 1 << 10
OBJ_FLAG_SET_THROW_MATRIX_FROM_TRANSFORM = 1 << 11
OBJ_FLAG_COMPUTE_ANGLE_TO_MARIO          = 1 << 13
OBJ_FLAG_PERSISTENT_RESPAWN              = 1 << 14

# --- Active Flags ---
ACTIVE_FLAG_ACTIVE          = 1 << 0
ACTIVE_FLAG_FAR_AWAY        = 1 << 1
ACTIVE_FLAG_DEACTIVATED     = 0

# --- Behavior script macro helpers (matching behavior_data.c) ---
def _BC_B(op):
    return (op << 24) & 0xFF000000

def _BC_BB(op, a):
    return ((op << 24) & 0xFF000000) | ((a << 16) & 0x00FF0000)

def _BC_B0H(op, h):
    return ((op << 24) & 0xFF000000) | (h & 0x0000FFFF)

def _BC_BBH(op, b, h):
    return ((op << 24) & 0xFF000000) | ((b << 16) & 0x00FF0000) | (h & 0x0000FFFF)

def _BC_BBBB(op, a, b, c):
    return ((op << 24) & 0xFF000000) | ((a << 16) & 0x00FF0000) | ((b << 8) & 0x0000FF00) | (c & 0x000000FF)

def _BC_H(val):
    return val & 0x0000FFFF

def _BC_HH(a, b):
    return ((a << 16) & 0xFFFF0000) | (b & 0x0000FFFF)

def _BC_W(val):
    return val & 0xFFFFFFFF

# Behavior macro builders - return list of 32-bit command words
def bhv_begin(obj_list):
    return [_BC_BB(BHV_BEGIN, obj_list)]

def bhv_delay(num):
    return [_BC_B0H(BHV_DELAY, num)]

def bhv_call(addr):
    return [_BC_B(BHV_CALL), _BC_W(id(addr))]

def bhv_return():
    return [_BC_B(BHV_RETURN)]

def bhv_goto(addr):
    return [_BC_B(BHV_GOTO), _BC_W(id(addr))]

def bhv_begin_repeat(count):
    return [_BC_B0H(BHV_BEGIN_REPEAT, count)]

def bhv_end_repeat():
    return [_BC_B(BHV_END_REPEAT)]

def bhv_end_repeat_continue():
    return [_BC_B(BHV_END_REPEAT_CONTINUE)]

def bhv_begin_loop():
    return [_BC_B(BHV_BEGIN_LOOP)]

def bhv_end_loop():
    return [_BC_B(BHV_END_LOOP)]

def bhv_break():
    return [_BC_B(BHV_BREAK)]

def bhv_call_native(func):
    return [_BC_B(BHV_CALL_NATIVE), _BC_W(id(func))]

def bhv_set_float(field, value):
    return [_BC_BBH(BHV_SET_FLOAT, field, value)]

def bhv_set_int(field, value):
    return [_BC_BBH(BHV_SET_INT, field, value)]

def bhv_add_float(field, value):
    return [_BC_BBH(BHV_ADD_FLOAT, field, value)]

def bhv_add_int(field, value):
    return [_BC_BBH(BHV_ADD_INT, field, value)]

def bhv_or_int(field, value):
    return [_BC_BBH(BHV_OR_INT, field, value)]

def bhv_set_model(modelID):
    return [_BC_B0H(BHV_SET_MODEL, modelID)]

def bhv_deactivate():
    return [_BC_B(BHV_DEACTIVATE)]

def bhv_drop_to_floor():
    return [_BC_B(BHV_DROP_TO_FLOOR)]

def bhv_set_home():
    return [_BC_B(BHV_SET_HOME)]

def bhv_billboard():
    return [_BC_B(BHV_BILLBOARD)]

def bhv_hide():
    return [_BC_B(BHV_HIDE)]

def bhv_set_hitbox(radius, height):
    return [_BC_B(BHV_SET_HITBOX), _BC_HH(radius, height)]

def bhv_set_hurtbox(radius, height):
    return [_BC_B(BHV_SET_HURTBOX), _BC_HH(radius, height)]

def bhv_disable_rendering():
    return [_BC_B(BHV_DISABLE_RENDERING)]

def bhv_scale(unused_field, percent):
    return [_BC_BBH(BHV_SCALE, unused_field, percent)]

def bhv_set_interact_type(itype):
    return [_BC_B(BHV_SET_INTERACT_TYPE), _BC_W(itype)]

def bhv_spawn_child(modelID, behavior):
    return [_BC_B(BHV_SPAWN_CHILD), _BC_W(modelID), _BC_W(id(behavior))]

def bhv_spawn_obj(modelID, behavior):
    return [_BC_B(BHV_SPAWN_OBJ), _BC_W(modelID), _BC_W(id(behavior))]

def bhv_set_random_float(field, min_val, range_val):
    return [_BC_BBH(BHV_SET_RANDOM_FLOAT, field, min_val), _BC_H(range_val)]

def bhv_set_random_int(field, min_val, range_val):
    return [_BC_BBH(BHV_SET_RANDOM_INT, field, min_val), _BC_H(range_val)]

def bhv_set_obj_physics(wall_hitbox, gravity, bounciness, drag, friction, buoyancy):
    return [_BC_B(BHV_SET_OBJ_PHYSICS),
            _BC_HH(wall_hitbox, gravity),
            _BC_HH(bounciness, drag),
            _BC_HH(friction, buoyancy),
            _BC_HH(0, 0)]

def bhv_delay_var(field):
    return [_BC_BB(BHV_DELAY_VAR, field)]

def bhv_load_collision_data(data):
    return [_BC_B(BHV_LOAD_COLLISION_DATA), _BC_W(id(data))]

def bhv_set_hitbox_with_offset(radius, height, down_offset):
    return [_BC_B(BHV_SET_HITBOX_WITH_OFFSET), _BC_HH(radius, height), _BC_H(down_offset)]

def bhv_spawn_child_with_param(bhv_param, modelID, behavior):
    return [_BC_B0H(BHV_SPAWN_CHILD_WITH_PARAM, bhv_param), _BC_W(modelID), _BC_W(id(behavior))]

def bhv_animate_texture(field, rate):
    return [_BC_BBH(BHV_ANIMATE_TEXTURE, field, rate)]

def bhv_parent_bit_clear(field, flags):
    return [_BC_BB(BHV_PARENT_BIT_CLEAR, field), _BC_W(flags)]

# --- Behavior Object ---
class BhvObject:
    _id_counter = 0

    def __init__(self, bhv_script, model_id=0, obj_list=OBJ_LIST_DEFAULT):
        BhvObject._id_counter += 1
        self.uid = BhvObject._id_counter
        self.behavior = bhv_script
        self.cur_bhv_command = 0
        self.bhv_stack = []
        self.bhv_delay_timer = 0
        self.bhv_stack_index = 0

        self.active_flags = ACTIVE_FLAG_ACTIVE
        self.parent_obj = None
        self.prev_obj = None
        self.collided_obj_interact_types = 0
        self.num_collided_objs = 0
        self.collided_objs = []

        self.oFlags = 0
        self.oDialogResponse = 0
        self.oIntangibleTimer = -1
        self.oPosX = 0.0
        self.oPosY = 0.0
        self.oPosZ = 0.0
        self.oVelX = 0.0
        self.oVelY = 0.0
        self.oVelZ = 0.0
        self.oForwardVel = 0.0
        self.oLeftVel = 0.0
        self.oUpVel = 0.0
        self.oActiveParticleFlags = 0
        self.oSoundStateID = 0
        self.oMoveAnglePitch = 0
        self.oMoveAngleYaw = 0
        self.oMoveAngleRoll = 0
        self.oFaceAnglePitch = 0
        self.oFaceAngleYaw = 0
        self.oFaceAngleRoll = 0
        self.oGraphYOffset = 0.0
        self.oGravity = -400.0
        self.oFloorHeight = 0.0
        self.oMoveFlags = 0
        self.oAnimState = 0
        self.oAngleVelPitch = 0
        self.oAngleVelYaw = 0
        self.oAngleVelRoll = 0
        self.oAnimations = None
        self.oHeldState = 0
        self.oWallHitboxRadius = 30.0
        self.oDragStrength = 1000.0
        self.oInteractType = 0
        self.oInteractStatus = 0
        self.oParentRelativePosX = 0.0
        self.oParentRelativePosY = 0.0
        self.oParentRelativePosZ = 0.0
        self.oBhvParams2ndByte = 0
        self.oAction = 0
        self.oSubAction = 0
        self.oTimer = 0
        self.oPrevAction = 0
        self.oBounciness = -50.0
        self.oDistanceToMario = 0.0
        self.oAngleToMario = 0
        self.oHomeX = 0.0
        self.oHomeY = 0.0
        self.oHomeZ = 0.0
        self.oFriction = 1000.0
        self.oBuoyancy = 200.0
        self.oOpacity = 255
        self.oDamageOrCoinValue = 0
        self.oHealth = 0
        self.oBhvParams = 0
        self.oInteractionSubtype = 0
        self.oCollisionDistance = 0.0
        self.oNumLootCoins = 0
        self.oDrawingDistance = 10000.0
        self.oRoom = -1
        self.oUnusedBhvParams = 0
        self.oWallAngle = 0
        self.oAngleToHome = 0
        self.oDeathSound = 0

        self.hitboxRadius = 0.0
        self.hitboxHeight = 0.0
        self.hurtboxRadius = 0.0
        self.hurtboxHeight = 0.0
        self.hitboxDownOffset = 0.0
        self.collisionData = None
        self.respawnInfoType = 0
        self.respawnInfo = None

        self.obj_list = obj_list
        self.model_id = model_id
        self.render_enabled = True

        # For rendering
        self.mesh_verts = []
        self.mesh_faces = []
        self.color = WHITE
        self.billboard = False

    def get_field_f32(self, index):
        mapping = {
            OPOSX: 'oPosX', OPOSY: 'oPosY', OPOSZ: 'oPosZ',
            OVELX: 'oVelX', OVELY: 'oVelY', OVELZ: 'oVelZ',
            OFORWARDVEL: 'oForwardVel', OLEFTVEL: 'oLeftVel', OUPVEL: 'oUpVel',
            OGRAPHYOFFSET: 'oGraphYOffset', OGRAVITY: 'oGravity',
            OFLOORHEIGHT: 'oFloorHeight', OBOUNCINESS: 'oBounciness',
            ODISTANCETOMARIO: 'oDistanceToMario', OHOMEX: 'oHomeX',
            OHOMEY: 'oHomeY', OHOMEZ: 'oHomeZ', OFRICTION: 'oFriction',
            OBUOYANCY: 'oBuoyancy', OCOLLISIONDISTANCE: 'oCollisionDistance',
            ODRAWINGDISTANCE: 'oDrawingDistance',
            OPARENTRELATIVEPOSX: 'oParentRelativePosX',
            OPARENTRELATIVEPOSY: 'oParentRelativePosY',
            OPARENTRELATIVEPOSZ: 'oParentRelativePosZ',
            ODRAGSTRENGTH: 'oDragStrength',
            OWALLHITBOXRADIUS: 'oWallHitboxRadius',
        }
        attr = mapping.get(index)
        if attr and hasattr(self, attr):
            return getattr(self, attr)
        return 0.0

    def set_field_f32(self, index, value):
        mapping = {
            OPOSX: 'oPosX', OPOSY: 'oPosY', OPOSZ: 'oPosZ',
            OVELX: 'oVelX', OVELY: 'oVelY', OVELZ: 'oVelZ',
            OFORWARDVEL: 'oForwardVel', OLEFTVEL: 'oLeftVel', OUPVEL: 'oUpVel',
            OGRAPHYOFFSET: 'oGraphYOffset', OGRAVITY: 'oGravity',
            OFLOORHEIGHT: 'oFloorHeight', OBOUNCINESS: 'oBounciness',
            ODISTANCETOMARIO: 'oDistanceToMario', OHOMEX: 'oHomeX',
            OHOMEY: 'oHomeY', OHOMEZ: 'oHomeZ', OFRICTION: 'oFriction',
            OBUOYANCY: 'oBuoyancy', OCOLLISIONDISTANCE: 'oCollisionDistance',
            ODRAWINGDISTANCE: 'oDrawingDistance',
            OPARENTRELATIVEPOSX: 'oParentRelativePosX',
            OPARENTRELATIVEPOSY: 'oParentRelativePosY',
            OPARENTRELATIVEPOSZ: 'oParentRelativePosZ',
            ODRAGSTRENGTH: 'oDragStrength',
            OWALLHITBOXRADIUS: 'oWallHitboxRadius',
        }
        attr = mapping.get(index)
        if attr and hasattr(self, attr):
            setattr(self, attr, value)

    def get_field_s32(self, index):
        mapping = {
            OFFLAGS: 'oFlags', OINTANGIBLETIMER: 'oIntangibleTimer',
            OMOVEANGLEPITCH: 'oMoveAnglePitch', OMOVEANGLEYAW: 'oMoveAngleYaw',
            OMOVEANGLEROLL: 'oMoveAngleRoll',
            OFACEANGLEPITCH: 'oFaceAnglePitch', OFACEANGLEYAW: 'oFaceAngleYaw',
            OFACEANGLEROLL: 'oFaceAngleRoll',
            OACTIVEPARTICLEFLAGS: 'oActiveParticleFlags',
            OMOVEFLAGS: 'oMoveFlags', OANIMSTATE: 'oAnimState',
            OANGLEVELPITCH: 'oAngleVelPitch', OANGLEVELYAW: 'oAngleVelYaw',
            OANGLEVELROLL: 'oAngleVelRoll',
            OHELDSTATE: 'oHeldState', OINTERACTTYPE: 'oInteractType',
            OINTERACTSTATUS: 'oInteractStatus',
            OBHVPARAMS2NDBYTE: 'oBhvParams2ndByte',
            OACTION: 'oAction', OSUBACTION: 'oSubAction', OTIMER: 'oTimer',
            OPREVACTION: 'oPrevAction', OINTERACTIONSUBTYPE: 'oInteractionSubtype',
            ONUMLOOTCOINS: 'oNumLootCoins', OROOM: 'oRoom',
            OOPACITY: 'oOpacity', ODAMAGEORCOINVALUE: 'oDamageOrCoinValue',
            OHEALTH: 'oHealth', OBHVPARAMS: 'oBhvParams',
            OWALLANGLE: 'oWallAngle', OANGLETOMARIO: 'oAngleToMario',
            OANGLETOHOME: 'oAngleToHome', ODEATHSOUND: 'oDeathSound',
            OUNUSEDBHVPARAMS: 'oUnusedBhvParams',
            OSOUNDSTATEID: 'oSoundStateID',
        }
        attr = mapping.get(index)
        if attr and hasattr(self, attr):
            return getattr(self, attr)
        return 0

    def set_field_s32(self, index, value):
        mapping = {
            OFFLAGS: 'oFlags', OINTANGIBLETIMER: 'oIntangibleTimer',
            OMOVEANGLEPITCH: 'oMoveAnglePitch', OMOVEANGLEYAW: 'oMoveAngleYaw',
            OMOVEANGLEROLL: 'oMoveAngleRoll',
            OFACEANGLEPITCH: 'oFaceAnglePitch', OFACEANGLEYAW: 'oFaceAngleYaw',
            OFACEANGLEROLL: 'oFaceAngleRoll',
            OACTIVEPARTICLEFLAGS: 'oActiveParticleFlags',
            OMOVEFLAGS: 'oMoveFlags', OANIMSTATE: 'oAnimState',
            OANGLEVELPITCH: 'oAngleVelPitch', OANGLEVELYAW: 'oAngleVelYaw',
            OANGLEVELROLL: 'oAngleVelRoll',
            OHELDSTATE: 'oHeldState', OINTERACTTYPE: 'oInteractType',
            OINTERACTSTATUS: 'oInteractStatus',
            OBHVPARAMS2NDBYTE: 'oBhvParams2ndByte',
            OACTION: 'oAction', OSUBACTION: 'oSubAction', OTIMER: 'oTimer',
            OPREVACTION: 'oPrevAction', OINTERACTIONSUBTYPE: 'oInteractionSubtype',
            ONUMLOOTCOINS: 'oNumLootCoins', OROOM: 'oRoom',
            OOPACITY: 'oOpacity', ODAMAGEORCOINVALUE: 'oDamageOrCoinValue',
            OHEALTH: 'oHealth', OBHVPARAMS: 'oBhvParams',
            OWALLANGLE: 'oWallAngle', OANGLETOMARIO: 'oAngleToMario',
            OANGLETOHOME: 'oAngleToHome', ODEATHSOUND: 'oDeathSound',
            OUNUSEDBHVPARAMS: 'oUnusedBhvParams',
            OSOUNDSTATEID: 'oSoundStateID',
        }
        attr = mapping.get(index)
        if attr and hasattr(self, attr):
            setattr(self, attr, int(value))

# --- Behavior Script Interpreter ---
class BhvInterpreter:
    def __init__(self):
        self.objects = []
        self.global_timer = 0
        self.native_funcs = {}

    def register_native(self, name, func):
        self.native_funcs[name] = func

    def add_object(self, obj):
        self.objects.append(obj)
        return obj

    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def get_field_ptr_f32(self, obj, index):
        if index in (OANIMATIONS,):
            return None
        return None

    def resolve_script(self, data):
        """Convert a list of word values or a list-of-lists script into a flat word array."""
        words = []
        for item in data:
            if isinstance(item, list):
                words.extend(item)
            else:
                words.append(item)
        if not hasattr(self, '_script_addr_map'):
            self._script_addr_map = {}
        self._script_addr_map[id(words)] = 0
        return words

    def _bhv_cmd_begin(self, obj, cmd, idx):
        obj_list = (cmd >> 16) & 0xFF
        obj.obj_list = obj_list
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_delay(self, obj, cmd, idx):
        num = cmd & 0xFFFF
        if obj.bhv_delay_timer < num - 1:
            obj.bhv_delay_timer += 1
        else:
            obj.bhv_delay_timer = 0
            return idx + 1, BHV_PROC_CONTINUE
        return idx, BHV_PROC_BREAK

    def _bhv_cmd_call(self, obj, cmds, idx):
        addr = cmds[idx + 1]
        obj.bhv_stack.append(idx + 2)
        return self._find_script_idx_by_addr(obj.behavior, addr), BHV_PROC_CONTINUE

    def _bhv_cmd_return(self, obj, cmds, idx):
        if obj.bhv_stack:
            return obj.bhv_stack.pop(), BHV_PROC_CONTINUE
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_goto(self, obj, cmds, idx):
        addr = cmds[idx + 1]
        return self._find_script_idx_by_addr(obj.behavior, addr), BHV_PROC_CONTINUE

    def _bhv_cmd_begin_repeat(self, obj, cmds, idx):
        count = cmds[idx] & 0xFFFF
        obj.bhv_stack.append(idx + 1)
        obj.bhv_stack.append(count)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_end_repeat(self, obj, cmds, idx):
        count = obj.bhv_stack.pop()
        count -= 1
        if count != 0:
            addr = obj.bhv_stack.pop()
            obj.bhv_stack.append(addr)
            obj.bhv_stack.append(count)
            return addr, BHV_PROC_CONTINUE
        else:
            obj.bhv_stack.pop()
            return idx + 1, BHV_PROC_BREAK

    def _bhv_cmd_end_repeat_continue(self, obj, cmds, idx):
        count = obj.bhv_stack.pop()
        count -= 1
        if count != 0:
            addr = obj.bhv_stack.pop()
            obj.bhv_stack.append(addr)
            obj.bhv_stack.append(count)
            return addr, BHV_PROC_CONTINUE
        else:
            obj.bhv_stack.pop()
            return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_begin_loop(self, obj, cmds, idx):
        obj.bhv_stack.append(idx + 1)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_end_loop(self, obj, cmds, idx):
        addr = obj.bhv_stack.pop()
        obj.bhv_stack.append(idx)
        return addr, BHV_PROC_BREAK

    def _bhv_cmd_break(self, obj, cmds, idx):
        return idx, BHV_PROC_BREAK

    def _bhv_cmd_break_unused(self, obj, cmds, idx):
        return idx, BHV_PROC_BREAK

    def _bhv_cmd_call_native(self, obj, cmds, idx):
        func_addr = cmds[idx + 1]
        func = self.native_funcs.get(func_addr)
        if func:
            func(obj)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_set_float(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = cmd & 0xFFFF
        obj.set_field_f32(field, float(value))
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_int(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = (cmd & 0xFFFF)
        if value & 0x8000:
            value -= 0x10000
        obj.set_field_s32(field, value)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_add_float(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = cmd & 0xFFFF
        obj.set_field_f32(field, obj.get_field_f32(field) + float(value))
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_add_int(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = cmd & 0xFFFF
        if value & 0x8000:
            value -= 0x10000
        obj.set_field_s32(field, obj.get_field_s32(field) + value)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_or_int(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = cmd & 0xFFFF
        obj.set_field_s32(field, obj.get_field_s32(field) | value)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_bit_clear(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        value = cmd & 0xFFFF
        obj.set_field_s32(field, obj.get_field_s32(field) & ~value)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_model(self, obj, cmds, idx):
        model_id = cmds[idx] & 0xFFFF
        obj.model_id = model_id
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_spawn_child(self, obj, cmds, idx):
        model = cmds[idx + 1]
        behavior_addr = cmds[idx + 2]
        # Find behavior script by address
        child_script = None
        for name, script in self.native_funcs.items():
            if id(script) == behavior_addr:
                child_script = script
                break
        if child_script is None:
            child_script = obj.behavior
        child = BhvObject(child_script, model)
        child.parent_obj = obj
        child.oPosX = obj.oPosX
        child.oPosY = obj.oPosY
        child.oPosZ = obj.oPosZ
        self.add_object(child)
        return idx + 3, BHV_PROC_CONTINUE

    def _bhv_cmd_deactivate(self, obj, cmds, idx):
        obj.active_flags = ACTIVE_FLAG_DEACTIVATED
        return idx, BHV_PROC_BREAK

    def _bhv_cmd_drop_to_floor(self, obj, cmds, idx):
        # Simple floor drop
        obj.oPosY = 0.0
        obj.oMoveFlags |= 1 << 1
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_billboard(self, obj, cmds, idx):
        obj.billboard = True
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_hide(self, obj, cmds, idx):
        obj.render_enabled = False
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_hitbox(self, obj, cmds, idx):
        radius = (cmds[idx + 1] >> 16) & 0xFFFF
        height = cmds[idx + 1] & 0xFFFF
        if radius & 0x8000: radius -= 0x10000
        if height & 0x8000: height -= 0x10000
        obj.hitboxRadius = float(radius)
        obj.hitboxHeight = float(height)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_set_hurtbox(self, obj, cmds, idx):
        radius = (cmds[idx + 1] >> 16) & 0xFFFF
        height = cmds[idx + 1] & 0xFFFF
        if radius & 0x8000: radius -= 0x10000
        if height & 0x8000: height -= 0x10000
        obj.hurtboxRadius = float(radius)
        obj.hurtboxHeight = float(height)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_set_home(self, obj, cmds, idx):
        obj.oHomeX = obj.oPosX
        obj.oHomeY = obj.oPosY
        obj.oHomeZ = obj.oPosZ
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_interact_type(self, obj, cmds, idx):
        obj.oInteractType = cmds[idx + 1]
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_disable_rendering(self, obj, cmds, idx):
        obj.render_enabled = False
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_scale(self, obj, cmds, idx):
        percent = cmds[idx] & 0xFFFF
        # Store scale for rendering
        obj.scale_percent = percent
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_obj_physics(self, obj, cmds, idx):
        wall_hitbox = (cmds[idx + 1] >> 16) & 0xFFFF
        gravity = cmds[idx + 1] & 0xFFFF
        bounciness = (cmds[idx + 2] >> 16) & 0xFFFF
        drag = cmds[idx + 2] & 0xFFFF
        friction = (cmds[idx + 3] >> 16) & 0xFFFF
        buoyancy = cmds[idx + 3] & 0xFFFF
        if wall_hitbox & 0x8000: wall_hitbox -= 0x10000
        if gravity & 0x8000: gravity -= 0x10000
        if bounciness & 0x8000: bounciness -= 0x10000
        if drag & 0x8000: drag -= 0x10000
        if friction & 0x8000: friction -= 0x10000
        if buoyancy & 0x8000: buoyancy -= 0x10000
        obj.oWallHitboxRadius = float(wall_hitbox)
        obj.oGravity = float(gravity) / 100.0
        obj.oBounciness = float(bounciness) / 100.0
        obj.oDragStrength = float(drag) / 100.0
        obj.oFriction = float(friction) / 100.0
        obj.oBuoyancy = float(buoyancy) / 100.0
        return idx + 5, BHV_PROC_CONTINUE

    def _bhv_cmd_animate_texture(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        rate = cmd & 0xFFFF
        if self.global_timer % rate == 0:
            obj.set_field_s32(field, obj.get_field_s32(field) + 1)
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_set_interact_subtype(self, obj, cmds, idx):
        obj.oInteractionSubtype = cmds[idx + 1]
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_set_hitbox_with_offset(self, obj, cmds, idx):
        radius = (cmds[idx + 1] >> 16) & 0xFFFF
        height = cmds[idx + 1] & 0xFFFF
        down_offset = cmds[idx + 2] & 0xFFFF
        if radius & 0x8000: radius -= 0x10000
        if height & 0x8000: height -= 0x10000
        if down_offset & 0x8000: down_offset -= 0x10000
        obj.hitboxRadius = float(radius)
        obj.hitboxHeight = float(height)
        obj.hitboxDownOffset = float(down_offset)
        return idx + 3, BHV_PROC_CONTINUE

    def _bhv_cmd_delay_var(self, obj, cmds, idx):
        field = (cmds[idx] >> 16) & 0xFF
        num = obj.get_field_s32(field)
        if obj.bhv_delay_timer < num - 1:
            obj.bhv_delay_timer += 1
        else:
            obj.bhv_delay_timer = 0
            return idx + 1, BHV_PROC_CONTINUE
        return idx, BHV_PROC_BREAK

    def _bhv_cmd_set_random_float(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        min_val = float(cmd & 0xFFFF)
        range_val = float(cmds[idx + 1] & 0xFFFF)
        obj.set_field_f32(field, range_val * random.random() + min_val)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_set_random_int(self, obj, cmds, idx):
        cmd = cmds[idx]
        field = (cmd >> 16) & 0xFF
        min_val = cmd & 0xFFFF
        range_val = cmds[idx + 1] & 0xFFFF
        obj.set_field_s32(field, int(range_val * random.random()) + min_val)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_sum_float(self, obj, cmds, idx):
        cmd = cmds[idx]
        dst = (cmd >> 16) & 0xFF
        src1 = (cmd >> 8) & 0xFF
        src2 = cmd & 0xFF
        obj.set_field_f32(dst, obj.get_field_f32(src1) + obj.get_field_f32(src2))
        return idx + 1, BHV_PROC_CONTINUE

    def _bhv_cmd_spawn_child_with_param(self, obj, cmds, idx):
        bhv_param = cmds[idx] & 0xFFFF
        model = cmds[idx + 1]
        behavior_addr = cmds[idx + 2]
        child_script = None
        for name, script in self.native_funcs.items():
            if id(script) == behavior_addr:
                child_script = script
                break
        if child_script is None:
            child_script = obj.behavior
        child = BhvObject(child_script, model)
        child.parent_obj = obj
        child.oBhvParams2ndByte = bhv_param
        child.oPosX = obj.oPosX
        child.oPosY = obj.oPosY
        child.oPosZ = obj.oPosZ
        self.add_object(child)
        return idx + 3, BHV_PROC_CONTINUE

    def _bhv_cmd_load_collision_data(self, obj, cmds, idx):
        obj.collisionData = cmds[idx + 1]
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_spawn_obj(self, obj, cmds, idx):
        model = cmds[idx + 1]
        behavior_addr = cmds[idx + 2]
        child_script = None
        for name, script in self.native_funcs.items():
            if id(script) == behavior_addr:
                child_script = script
                break
        if child_script is None:
            child_script = obj.behavior
        spawned = BhvObject(child_script, model)
        spawned.parent_obj = obj
        spawned.oPosX = obj.oPosX
        spawned.oPosY = obj.oPosY
        spawned.oPosZ = obj.oPosZ
        obj.prev_obj = spawned
        self.add_object(spawned)
        return idx + 3, BHV_PROC_CONTINUE

    def _bhv_cmd_parent_bit_clear(self, obj, cmds, idx):
        field = (cmds[idx] >> 16) & 0xFF
        value = cmds[idx + 1]
        if obj.parent_obj:
            obj.parent_obj.set_field_s32(field, obj.parent_obj.get_field_s32(field) & ~value)
        return idx + 2, BHV_PROC_CONTINUE

    def _bhv_cmd_nop(self, obj, cmds, idx):
        return idx + 1, BHV_PROC_CONTINUE

    def _find_script_idx_by_addr(self, script_words, addr):
        return self._script_addr_map.get(addr, 0) if hasattr(self, '_script_addr_map') else 0

    def _get_opcode(self, cmd):
        return (cmd >> 24) & 0xFF

    def update_object(self, obj):
        if obj.active_flags == ACTIVE_FLAG_DEACTIVATED:
            return

        script = obj.behavior
        idx = obj.cur_bhv_command

        if idx >= len(script):
            return

        if obj.oAction != obj.oPrevAction:
            obj.oTimer = 0
            obj.oSubAction = 0
            obj.oPrevAction = obj.oAction

        # Execute behavior script
        while idx < len(script):
            cmd = script[idx]
            opcode = self._get_opcode(cmd)

            if opcode == BHV_BEGIN:
                idx, result = self._bhv_cmd_begin(obj, cmd, idx)
            elif opcode == BHV_DELAY:
                idx, result = self._bhv_cmd_delay(obj, cmd, idx)
            elif opcode == BHV_CALL:
                idx, result = self._bhv_cmd_call(obj, script, idx)
            elif opcode == BHV_RETURN:
                idx, result = self._bhv_cmd_return(obj, script, idx)
            elif opcode == BHV_GOTO:
                idx, result = self._bhv_cmd_goto(obj, script, idx)
            elif opcode == BHV_BEGIN_REPEAT:
                idx, result = self._bhv_cmd_begin_repeat(obj, script, idx)
            elif opcode == BHV_END_REPEAT:
                idx, result = self._bhv_cmd_end_repeat(obj, script, idx)
            elif opcode == BHV_END_REPEAT_CONTINUE:
                idx, result = self._bhv_cmd_end_repeat_continue(obj, script, idx)
            elif opcode == BHV_BEGIN_LOOP:
                idx, result = self._bhv_cmd_begin_loop(obj, script, idx)
            elif opcode == BHV_END_LOOP:
                idx, result = self._bhv_cmd_end_loop(obj, script, idx)
            elif opcode == BHV_BREAK:
                idx, result = self._bhv_cmd_break(obj, script, idx)
            elif opcode == BHV_BREAK_UNUSED:
                idx, result = self._bhv_cmd_break_unused(obj, script, idx)
            elif opcode == BHV_CALL_NATIVE:
                idx, result = self._bhv_cmd_call_native(obj, script, idx)
            elif opcode == BHV_SET_FLOAT:
                idx, result = self._bhv_cmd_set_float(obj, script, idx)
            elif opcode == BHV_SET_INT:
                idx, result = self._bhv_cmd_set_int(obj, script, idx)
            elif opcode == BHV_ADD_FLOAT:
                idx, result = self._bhv_cmd_add_float(obj, script, idx)
            elif opcode == BHV_ADD_INT:
                idx, result = self._bhv_cmd_add_int(obj, script, idx)
            elif opcode == BHV_OR_INT:
                idx, result = self._bhv_cmd_or_int(obj, script, idx)
            elif opcode == BHV_BIT_CLEAR:
                idx, result = self._bhv_cmd_bit_clear(obj, script, idx)
            elif opcode == BHV_SET_MODEL:
                idx, result = self._bhv_cmd_set_model(obj, script, idx)
            elif opcode == BHV_SPAWN_CHILD:
                idx, result = self._bhv_cmd_spawn_child(obj, script, idx)
            elif opcode == BHV_DEACTIVATE:
                idx, result = self._bhv_cmd_deactivate(obj, script, idx)
            elif opcode == BHV_DROP_TO_FLOOR:
                idx, result = self._bhv_cmd_drop_to_floor(obj, script, idx)
            elif opcode == BHV_BILLBOARD:
                idx, result = self._bhv_cmd_billboard(obj, script, idx)
            elif opcode == BHV_HIDE:
                idx, result = self._bhv_cmd_hide(obj, script, idx)
            elif opcode == BHV_SET_HITBOX:
                idx, result = self._bhv_cmd_set_hitbox(obj, script, idx)
            elif opcode == BHV_SET_HURTBOX:
                idx, result = self._bhv_cmd_set_hurtbox(obj, script, idx)
            elif opcode == BHV_SET_HOME:
                idx, result = self._bhv_cmd_set_home(obj, script, idx)
            elif opcode == BHV_SET_INTERACT_TYPE:
                idx, result = self._bhv_cmd_set_interact_type(obj, script, idx)
            elif opcode == BHV_DISABLE_RENDERING:
                idx, result = self._bhv_cmd_disable_rendering(obj, script, idx)
            elif opcode == BHV_SCALE:
                idx, result = self._bhv_cmd_scale(obj, script, idx)
            elif opcode == BHV_SET_OBJ_PHYSICS:
                idx, result = self._bhv_cmd_set_obj_physics(obj, script, idx)
            elif opcode == BHV_ANIMATE_TEXTURE:
                idx, result = self._bhv_cmd_animate_texture(obj, script, idx)
            elif opcode == BHV_SET_INTERACT_SUBTYPE:
                idx, result = self._bhv_cmd_set_interact_subtype(obj, script, idx)
            elif opcode == BHV_SET_HITBOX_WITH_OFFSET:
                idx, result = self._bhv_cmd_set_hitbox_with_offset(obj, script, idx)
            elif opcode == BHV_DELAY_VAR:
                idx, result = self._bhv_cmd_delay_var(obj, script, idx)
            elif opcode == BHV_SET_RANDOM_FLOAT:
                idx, result = self._bhv_cmd_set_random_float(obj, script, idx)
            elif opcode == BHV_SET_RANDOM_INT:
                idx, result = self._bhv_cmd_set_random_int(obj, script, idx)
            elif opcode == BHV_SUM_FLOAT:
                idx, result = self._bhv_cmd_sum_float(obj, script, idx)
            elif opcode == BHV_SPAWN_CHILD_WITH_PARAM:
                idx, result = self._bhv_cmd_spawn_child_with_param(obj, script, idx)
            elif opcode == BHV_LOAD_COLLISION_DATA:
                idx, result = self._bhv_cmd_load_collision_data(obj, script, idx)
            elif opcode == BHV_SPAWN_OBJ:
                idx, result = self._bhv_cmd_spawn_obj(obj, script, idx)
            elif opcode == BHV_PARENT_BIT_CLEAR:
                idx, result = self._bhv_cmd_parent_bit_clear(obj, script, idx)
            elif opcode in (BHV_CMD_NOP_1, BHV_CMD_NOP_2, BHV_CMD_NOP_3, BHV_CMD_NOP_4, BHV_SET_INT_UNUSED, BHV_BEGIN_REPEAT_UNUSED):
                idx, result = self._bhv_cmd_nop(obj, script, idx)
            else:
                idx += 1
                result = BHV_PROC_CONTINUE

            if result == BHV_PROC_BREAK:
                break

        obj.cur_bhv_command = idx

        if obj.oTimer < 0x3FFFFFFF:
            obj.oTimer += 1

        if obj.oAction != obj.oPrevAction:
            obj.oTimer = 0
            obj.oSubAction = 0
            obj.oPrevAction = obj.oAction

        # Object flag processing
        flags = obj.oFlags
        if flags & OBJ_FLAG_MOVE_XZ_USING_FVEL:
            yaw_rad = math.radians((obj.oMoveAngleYaw % 65536) / 65536.0 * 360.0)
            obj.oPosX += math.sin(yaw_rad) * obj.oForwardVel * 0.05
            obj.oPosZ += math.cos(yaw_rad) * obj.oForwardVel * 0.05
        if flags & OBJ_FLAG_MOVE_Y_WITH_TERMINAL_VEL:
            obj.oVelY += obj.oGravity * 0.05
            obj.oPosY += obj.oVelY * 0.05
        if flags & OBJ_FLAG_SET_FACE_YAW_TO_MOVE_YAW:
            obj.oFaceAngleYaw = obj.oMoveAngleYaw
        if flags & OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE:
            pass

    def update_all(self):
        self.global_timer += 1
        # Update in reverse to handle removals
        for obj in self.objects[:]:
            self.update_object(obj)
        # Cleanup deactivated objects
        self.objects[:] = [o for o in self.objects if o.active_flags != ACTIVE_FLAG_DEACTIVATED]

# --- Object Manager ---
class ObjectManager:
    def __init__(self):
        self.interpreter = BhvInterpreter()
        self.models = {}  # model_id -> (verts, faces, color)

    def register_model(self, model_id, verts, faces, color=WHITE):
        self.models[model_id] = (verts, faces, color)

    def spawn(self, bhv_script, model_id=0, x=0, y=0, z=0, obj_list=OBJ_LIST_DEFAULT):
        script = self.interpreter.resolve_script(bhv_script)
        obj = BhvObject(script, model_id, obj_list)
        obj.oPosX = x
        obj.oPosY = y
        obj.oPosZ = z
        self.interpreter.add_object(obj)
        return obj

    def update_all(self):
        self.interpreter.update_all()

    def get_renderable_objects(self):
        renderable = []
        for obj in self.interpreter.objects:
            if not obj.render_enabled:
                continue
            if obj.active_flags == ACTIVE_FLAG_DEACTIVATED:
                continue
            model = self.models.get(obj.model_id)
            if model:
                verts, faces, color = model
                # Transform vertices
                if obj.billboard:
                    # Billboard objects face the camera - handled in render
                    pass
                renderable.append((obj, verts, faces, color))
        return renderable

STATE_MENU, STATE_LETTER, STATE_CASTLE, STATE_LEVEL_SEL, STATE_PLAYING, STATE_STAR_GET = range(6)

def mat_vec(m, v):
    return (m[0][0]*v[0]+m[0][1]*v[1]+m[0][2]*v[2], m[1][0]*v[0]+m[1][1]*v[1]+m[1][2]*v[2], m[2][0]*v[0]+m[2][1]*v[1]+m[2][2]*v[2])

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))

def project_point(x, y, z, cam):
    v = (x-cam.x, y-cam.y, z-cam.z)
    v = mat_vec(rot_y(cam.yaw), v)
    v = mat_vec(rot_x(cam.pitch), v)
    if v[2] <= 5:
        return None
    return (v[0]*FOV_FACTOR/v[2]+HALF_W, -v[1]*FOV_FACTOR/v[2]+HALF_H, v[2])

def shade_color(color, normal):
    d = abs(normal[0]*LIGHT_DIR[0]+normal[1]*LIGHT_DIR[1]+normal[2]*LIGHT_DIR[2])
    s = max(0.35, d)
    return (int(color[0]*s), int(color[1]*s), int(color[2]*s))

class Mario:
    """SM64 / sm64-port style moveset (FILES_OFF tribute physics)."""

    def __init__(self, x, z, y=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.vx = self.vy = self.vz = 0.0
        self.ground_accel, self.air_accel = 1.35, 0.45
        self.max_speed, self.friction = 24.0, 0.84
        self.run_speed = 30.0
        self.gravity, self.jump_force = 1.35, 24.0
        self.double_jump_force = 28.5
        self.triple_jump_force = 35.0
        self.long_jump_force = 22.0
        self.long_jump_boost = 18.0
        self.terminal_vel = -48.0
        self.grounded = True
        self.yaw = 0.0
        self.size = 25
        self.stars_collected = 0
        self.coins = 0
        self.lives = 4
        self.health = 8
        self.floor_y = 0.0
        self.jump_combo = 0
        self.combo_timer = 0
        self.space_held = False
        self.b_held = False
        self.dive = False
        self.sliding = False
        self.pounding = False
        self.swim = False
        self.wall_kick_t = 0
        self.punch_t = 0
        self.invuln = 0
        self.cap = None  # None | "wing" | "metal" | "vanish"
        self.cap_timer = 0
        self.water_y = None  # set by world if swimming course
        self.last_vy = 0.0

    def respawn(self, x, z, y=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.vx = self.vy = self.vz = 0.0
        self.grounded = True
        self.floor_y = float(y)
        self.dive = self.sliding = self.pounding = self.swim = False
        self.jump_combo = 0
        self.health = 8
        self.invuln = 60

    def hurt(self, amount=1, knock=8):
        if self.invuln > 0 or self.cap == "metal":
            return
        self.health -= amount
        self.invuln = 70
        self.vx = -math.sin(self.yaw) * knock
        self.vz = -math.cos(self.yaw) * knock
        self.vy = 12
        self.grounded = False
        play_sfx("hurt")
        if self.health <= 0:
            self.lives -= 1
            return "death"
        return None

    def give_coin(self, n=1):
        self.coins += n
        play_sfx("coin")
        while self.coins >= 100:
            self.coins -= 100
            self.lives += 1
            play_sfx("1up")

    def floor_under(self, platforms, max_top=None):
        """Highest solid top under feet; optional max_top ignores ceilings above spawn."""
        best = None
        for px, py, pz, pw, ph, pd in platforms or []:
            hw, hd = pw / 2, pd / 2
            if px - hw <= self.x <= px + hw and pz - hd <= self.z <= pz + hd:
                top = py + ph / 2
                if max_top is not None and top > max_top:
                    continue
                if best is None or top > best:
                    best = top
        return best

    def snap_to_floor(self, platforms):
        """Place Mario on the highest solid under his feet (spawn / respawn)."""
        # Prefer floors near/below current Y so ceilings are not chosen at spawn.
        best = self.floor_under(platforms, max_top=self.y + 80.0)
        if best is None:
            best = self.floor_under(platforms)
        if best is not None:
            self.y = best
            self.floor_y = best
            self.vy = 0.0
            self.grounded = True
        return best

    def update(self, keys, cam_yaw, platforms=None, walls=None):
        if self.invuln > 0:
            self.invuln -= 1
        if self.cap_timer > 0:
            self.cap_timer -= 1
            if self.cap_timer <= 0:
                self.cap = None
        if self.punch_t > 0:
            self.punch_t -= 1
        if self.wall_kick_t > 0:
            self.wall_kick_t -= 1

        mx = mz = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            mx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            mx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            mz += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            mz -= 1

        crouch = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        b_btn = keys[pygame.K_LCTRL] or keys[pygame.K_z] or keys[pygame.K_b]
        space = keys[pygame.K_SPACE]

        # Swimming — submerged and not standing on a solid top
        land = self.floor_under(platforms)
        on_solid = land is not None and self.y >= land - 4 and self.y <= land + 24
        if self.water_y is not None and self.y < self.water_y - 10 and not on_solid:
            self.swim = True
            self.dive = self.pounding = False
            self.vy *= 0.92
            self.vy -= 0.15  # buoyant sink
            if space:
                self.vy += 1.1
            if crouch:
                self.vy -= 0.8
            accel = 0.55
            if mx or mz:
                ia = math.atan2(mx, mz)
                self.yaw = cam_yaw + ia
                self.vx += math.sin(self.yaw) * accel
                self.vz += math.cos(self.yaw) * accel
            self.vx *= 0.92
            self.vz *= 0.92
            speed = math.hypot(self.vx, self.vz)
            if speed > 14:
                self.vx *= 14 / speed
                self.vz *= 14 / speed
            self.x += self.vx
            self.y += self.vy
            self.z += self.vz
            if self.y >= self.water_y - 8:
                self.y = self.water_y - 8
                self.swim = False
            if self.y < -800:
                self.lives -= 1
                return "death"
            self.space_held = space
            self.b_held = b_btn
            return None
        else:
            self.swim = False

        # Wing cap flight
        flying = self.cap == "wing" and not self.grounded

        if mx or mz:
            ia = math.atan2(mx, mz)
            ta = cam_yaw + ia
            diff = (ta - self.yaw + math.pi) % (2 * math.pi) - math.pi
            self.yaw += diff * (0.35 if self.sliding else 0.25)
            accel = self.ground_accel if self.grounded else self.air_accel
            if flying:
                accel = 0.7
            if self.sliding:
                accel *= 0.3
            self.vx += math.sin(self.yaw) * accel
            self.vz += math.cos(self.yaw) * accel

        max_spd = self.run_speed if (not crouch and self.grounded and (mx or mz)) else self.max_speed
        if self.dive:
            max_spd = 34
        if self.cap == "metal":
            max_spd *= 0.85
        speed = math.hypot(self.vx, self.vz)
        if speed > max_spd:
            s = max_spd / speed
            self.vx *= s
            self.vz *= s

        if self.grounded and not self.sliding:
            self.vx *= self.friction
            self.vz *= self.friction
        elif self.sliding:
            self.vx *= 0.97
            self.vz *= 0.97
            if speed < 4:
                self.sliding = False

        # Gravity
        g = self.gravity
        if flying:
            g *= 0.35
            if space:
                self.vy += 0.55
        if self.cap == "metal":
            g *= 1.4
        if self.pounding:
            self.vy = min(self.vy, -42)

        self.last_vy = self.vy
        self.vy -= g
        if self.vy < self.terminal_vel:
            self.vy = self.terminal_vel

        # Wall kick detect (simple: blocked horizontal move)
        old_x, old_z = self.x, self.z
        self.x += self.vx
        self.z += self.vz
        hit_wall = False
        if platforms:
            for px, py, pz, pw, ph, pd in platforms:
                hw, hh, hd = pw / 2, ph / 2, pd / 2
                # side collision when overlapping vertically
                if abs(self.y + self.size - py) < hh + self.size:
                    if abs(self.x - px) < hw + self.size * 0.6 and abs(self.z - pz) < hd + self.size * 0.6:
                        # if we were outside on XZ before, treat as wall
                        if abs(old_x - px) >= hw + self.size * 0.55 or abs(old_z - pz) >= hd + self.size * 0.55:
                            if self.y < py + hh - 5:  # not landing on top
                                hit_wall = True
                                self.x, self.z = old_x, old_z
                                self.vx *= -0.3
                                self.vz *= -0.3
                                if not self.grounded and self.last_vy > -5:
                                    self.wall_kick_t = 12
                                break

        self.y += self.vy
        prev_y = self.y - self.vy  # position before vertical step

        self.floor_y = -9999.0
        if platforms:
            for px, py, pz, pw, ph, pd in platforms:
                hw, hd = pw / 2, pd / 2
                if px - hw <= self.x <= px + hw and pz - hd <= self.z <= pz + hd:
                    top = py + ph / 2
                    # Continuous collision: catch fast falls that would tunnel past the slab.
                    tunnel = max(24.0, abs(self.vy) + 12.0)
                    crossed = prev_y >= top - 2.0 and self.y <= top + tunnel
                    near = abs(self.y - top) <= tunnel and self.y <= top + 8
                    if self.vy <= 0.5 and (crossed or near):
                        if self.floor_y < top:
                            self.floor_y = top

        if self.floor_y > -9000 and self.y <= self.floor_y + 1.0:
            was_air = not self.grounded
            self.y = self.floor_y
            if self.pounding:
                play_sfx("pound")
                self.pounding = False
            self.vy = 0
            self.grounded = True
            self.dive = False
            if was_air and self.jump_combo > 0:
                self.combo_timer = 20
        else:
            self.grounded = False
            if self.floor_y <= -9000:
                self.floor_y = 0.0

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            if self.grounded:
                self.jump_combo = 0

        # Jump / long jump / wall kick
        if space and not self.space_held:
            if self.wall_kick_t > 0 and not self.grounded:
                self.vy = 26
                self.vx = math.sin(self.yaw) * 16
                self.vz = math.cos(self.yaw) * 16
                self.wall_kick_t = 0
                self.dive = False
                play_sfx("jump")
            elif self.grounded:
                speed = math.hypot(self.vx, self.vz)
                if crouch and speed > 10:
                    # long jump
                    self.vy = self.long_jump_force
                    self.vx += math.sin(self.yaw) * self.long_jump_boost
                    self.vz += math.cos(self.yaw) * self.long_jump_boost
                    self.jump_combo = 0
                    self.sliding = False
                    play_sfx("jump")
                elif self.combo_timer > 0 and self.jump_combo == 1:
                    self.vy = self.double_jump_force
                    self.jump_combo = 2
                    play_sfx("jump")
                elif self.combo_timer > 0 and self.jump_combo == 2:
                    self.vy = self.triple_jump_force
                    self.jump_combo = 3
                    self.vx *= 1.2
                    self.vz *= 1.2
                    play_sfx("jump")
                else:
                    self.vy = self.jump_force
                    self.jump_combo = 1
                    play_sfx("jump")
                self.grounded = False
                self.combo_timer = 20
                self.dive = False
                self.pounding = False
        self.space_held = space

        # B: punch / dive / slide
        if b_btn and not self.b_held:
            if self.grounded:
                if crouch or math.hypot(self.vx, self.vz) > 12:
                    self.sliding = True
                    self.vx += math.sin(self.yaw) * 8
                    self.vz += math.cos(self.yaw) * 8
                else:
                    self.punch_t = 14
            elif not self.dive:
                self.dive = True
                self.vy = max(self.vy, 5)
                self.vx += math.sin(self.yaw) * 12
                self.vz += math.cos(self.yaw) * 12
        self.b_held = b_btn

        # Ground pound
        if crouch and not self.grounded and not self.dive:
            self.pounding = True

        if self.y < -600:
            self.lives -= 1
            return "death"
        return None

    def get_mesh(self):
        s = self.size * (0.7 if self.sliding or self.dive else 1.0)
        h = self.size * (1.1 if self.sliding or self.dive else 2.0)
        # Cap tint
        top = MARIO_RED
        if self.cap == "wing":
            top = (255, 200, 80)
        elif self.cap == "metal":
            top = METAL_GRAY
        elif self.cap == "vanish":
            top = (180, 220, 255)
        if self.invuln > 0 and (self.invuln // 3) % 2 == 0:
            top = WHITE
        v = [(self.x-s,self.y,self.z-s),(self.x+s,self.y,self.z-s),(self.x+s,self.y,self.z+s),(self.x-s,self.y,self.z+s),
             (self.x-s,self.y+h,self.z-s),(self.x+s,self.y+h,self.z-s),(self.x+s,self.y+h,self.z+s),(self.x-s,self.y+h,self.z+s)]
        f = [([0,1,2,3],MARIO_BLUE),([4,5,6,7],top),([0,4,5,1],top),
             ([2,6,7,3],top),([1,5,6,2],MARIO_BLUE),([0,4,7,3],MARIO_BLUE)]
        return v, f


class Camera:
    """Lakitu-style follow cam with mouse look (PC port)."""

    def __init__(self, target):
        self.target = target
        self.yaw = 0.0
        self.pitch = -0.18
        self.dist = 680.0
        self.height = 320.0
        self.x = self.y = self.z = 0.0
        self.mouse_look = True

    def update(self, keys):
        if keys[pygame.K_q]:
            self.yaw -= 0.045
        if keys[pygame.K_e]:
            self.yaw += 0.045
        if keys[pygame.K_r]:
            self.dist = max(320, self.dist - 8)
        if keys[pygame.K_f]:
            self.dist = min(1100, self.dist + 8)
        # mouse
        if self.mouse_look and pygame.mouse.get_focused():
            rel = pygame.mouse.get_rel()
            if pygame.mouse.get_pressed()[2] or keys[pygame.K_LALT]:
                self.yaw += rel[0] * 0.004
                self.pitch = max(-1.1, min(0.35, self.pitch - rel[1] * 0.003))
        tx = self.target.x - math.sin(self.yaw) * self.dist * math.cos(self.pitch)
        tz = self.target.z - math.cos(self.yaw) * self.dist * math.cos(self.pitch)
        ty = self.target.y + self.height - math.sin(self.pitch) * self.dist * 0.5
        lag = 0.12
        self.x += (tx - self.x) * lag
        self.y += (ty - self.y) * lag
        self.z += (tz - self.z) * lag


class Enemy:
    def __init__(self, x, y, z, kind="goomba"):
        self.x, self.y, self.z = x, y, z
        self.kind = kind
        self.alive = True
        self.yaw = 0.0
        self.timer = 0
        self.hp = 1 if kind != "whomp" else 3
        self.home = (x, z)

    def update(self, mario):
        if not self.alive:
            return
        self.timer += 1
        dx, dz = mario.x - self.x, mario.z - self.z
        dist = math.hypot(dx, dz) + 0.01
        if self.kind == "bobomb":
            if dist < 350:
                self.yaw = math.atan2(dx, dz)
                self.x += math.sin(self.yaw) * 2.2
                self.z += math.cos(self.yaw) * 2.2
        elif self.kind == "goomba":
            self.yaw += 0.02
            self.x = self.home[0] + math.sin(self.timer * 0.03) * 80
            self.z = self.home[1] + math.cos(self.timer * 0.03) * 80
        elif self.kind == "whomp":
            if dist < 280 and self.timer % 90 < 20:
                # flatten attack — hurt if close and low
                if dist < 90 and mario.y < self.y + 40:
                    return mario.hurt(2, 12)
            else:
                self.yaw = math.atan2(dx, dz)

        # stomp
        if dist < 55 and mario.last_vy < -2 and mario.y > self.y:
            self.hp -= 1
            mario.vy = 16
            play_sfx("pound")
            if self.hp <= 0:
                self.alive = False
                mario.give_coin(3)
            return None
        # touch hurt
        if dist < 40 and abs(mario.y - self.y) < 50 and not (mario.pounding):
            if mario.punch_t > 0 and self.kind != "whomp":
                self.alive = False
                mario.give_coin(1)
            else:
                return mario.hurt(1, 10)
        return None

    def get_mesh(self):
        if not self.alive:
            return [], []
        s = 28 if self.kind == "whomp" else 18
        h = 70 if self.kind == "whomp" else 28
        col = DARK_GRAY if self.kind == "bobomb" else (WOOD_BROWN if self.kind == "goomba" else STONE_GRAY)
        v = [(self.x-s,self.y,self.z-s),(self.x+s,self.y,self.z-s),(self.x+s,self.y,self.z+s),(self.x-s,self.y,self.z+s),
             (self.x-s,self.y+h,self.z-s),(self.x+s,self.y+h,self.z-s),(self.x+s,self.y+h,self.z+s),(self.x-s,self.y+h,self.z+s)]
        f = [([0,1,2,3],col),([4,5,6,7],col),([0,4,5,1],col),([2,6,7,3],col),([1,5,6,2],col),([0,4,7,3],col)]
        return v, f


class CapBlock:
    def __init__(self, x, y, z, kind="wing"):
        self.x, self.y, self.z = x, y, z
        self.kind = kind
        self.taken = False
        self.bob = 0.0

    def update(self):
        self.bob += 0.07

    def check(self, mario):
        if self.taken:
            return
        if math.hypot(mario.x - self.x, mario.z - self.z) < 50 and abs(mario.y - self.y) < 60:
            self.taken = True
            mario.cap = self.kind
            mario.cap_timer = 60 * 12  # 12 seconds
            play_sfx("1up")

    def get_mesh(self):
        if self.taken:
            return [], []
        yb = self.y + math.sin(self.bob) * 8
        colors = {"wing": (255, 200, 60), "metal": METAL_GRAY, "vanish": (160, 210, 255)}
        c = colors.get(self.kind, YELLOW)
        s = 16
        v = [(self.x-s,yb,self.z-s),(self.x+s,yb,self.z-s),(self.x+s,yb,self.z+s),(self.x-s,yb,self.z+s),
             (self.x-s,yb+s*2,self.z-s),(self.x+s,yb+s*2,self.z-s),(self.x+s,yb+s*2,self.z+s),(self.x-s,yb+s*2,self.z+s)]
        f = [([0,1,2,3],c),([4,5,6,7],c),([0,4,5,1],c),([2,6,7,3],c)]
        return v, f


class Star:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.collected = False
        self.bob = 0.0

    def update(self):
        self.bob += 0.06

    def check(self, mario):
        if self.collected: return False
        dx = mario.x - self.x
        dy = mario.y - (self.y + math.sin(self.bob)*10)
        dz = mario.z - self.z
        if math.sqrt(dx*dx+dy*dy+dz*dz) < 60:
            self.collected = True
            mario.stars_collected += 1
            return True
        return False

    def get_mesh(self):
        if self.collected: return [], []
        yb = self.y + math.sin(self.bob)*10
        s = 15
        v = [(self.x,yb+s*2,self.z),(self.x-s,yb+s*0.5,self.z-s),(self.x+s,yb+s*0.5,self.z-s),
             (self.x+s,yb+s*0.5,self.z+s),(self.x-s,yb+s*0.5,self.z+s),(self.x,yb-s,self.z)]
        f = [([0,1,2],STAR_YELLOW),([0,2,3],STAR_YELLOW),([0,3,4],STAR_YELLOW),([0,4,1],STAR_YELLOW),
             ([5,2,1],GOLD),([5,3,2],GOLD),([5,4,3],GOLD),([5,1,4],GOLD)]
        return v, f

class Coin:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.collected = False
        self.spin = 0.0

    def update(self):
        self.spin += 0.08

    def check(self, mario):
        if self.collected: return False
        if math.sqrt((mario.x-self.x)**2+(mario.y-self.y)**2+(mario.z-self.z)**2) < 45:
            self.collected = True
            return True
        return False

    def get_mesh(self):
        if self.collected: return [], []
        s, w = 8, abs(math.cos(self.spin))*8+2
        v = [(self.x-w,self.y,self.z),(self.x+w,self.y,self.z),(self.x+w,self.y+s*2,self.z),(self.x-w,self.y+s*2,self.z)]
        f = [([0,1,2,3],YELLOW)]
        return v, f

BOX_FACE_INDICES = [[0,1,2,3],[4,5,6,7],[0,4,7,3],[1,5,6,2],[3,2,6,7],[0,1,5,4]]
FACE_NORMALS_BOX = [(0,0,-1),(0,0,1),(-1,0,0),(1,0,0),(0,1,0),(0,-1,0)]

class WorldBase:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.platforms = []
        self.stars = []
        self.coins = []
        self.enemies = []
        self.caps = []
        self.spawn = (0, -400)
        self.sky_color = SKY_BLUE
        self.name = "Unknown"
        self.star_count = 0
        self.water_y = None

    def add_box(self, x, y, z, w, h, d, color, collide=None):
        # Thin walkable slabs collide by default; fluids stay pass-through.
        if collide is None:
            fluids = {WATER_BLUE, DEEP_WATER, MOAT_BLUE, LAVA_RED, LAVA_ORANGE, DOCK_BLUE}
            collide = h <= 24 and min(w, d) >= 80 and color not in fluids
        idx = len(self.verts)
        hw, hh, hd = w/2, h/2, d/2
        self.verts += [(x-hw,y-hh,z-hd),(x+hw,y-hh,z-hd),(x+hw,y+hh,z-hd),(x-hw,y+hh,z-hd),
                       (x-hw,y-hh,z+hd),(x+hw,y-hh,z+hd),(x+hw,y+hh,z+hd),(x-hw,y+hh,z+hd)]
        for i, fi in enumerate(BOX_FACE_INDICES):
            self.faces.append(([j+idx for j in fi], shade_color(color, FACE_NORMALS_BOX[i])))
        if collide:
            self.platforms.append((x, y, z, w, h, d))

    def add_roof(self, x, y, z, w, h, d, color):
        idx = len(self.verts)
        hw, hd = w/2, d/2
        self.verts += [(x-hw,y,z-hd),(x+hw,y,z-hd),(x+hw,y,z+hd),(x-hw,y,z+hd),(x,y+h,z)]
        for fi in [[0,1,4],[1,2,4],[2,3,4],[3,0,4]]:
            self.faces.append(([i+idx for i in fi], shade_color(color, (0,1,0))))
        self.faces.append(([idx,idx+1,idx+2,idx+3], shade_color(color, (0,-1,0))))

    def add_slope(self, x, y, z, w, h, d, color):
        idx = len(self.verts)
        hw, hd = w/2, d/2
        self.verts += [(x-hw,y,z-hd),(x+hw,y,z-hd),(x+hw,y,z+hd),(x-hw,y,z+hd),(x-hw,y+h,z+hd),(x+hw,y+h,z+hd)]
        for fi in [[0,1,2,3],[2,5,4,3],[0,1,5,4],[0,3,4],[1,2,5]]:
            n = (0,1,0) if fi in ([0,1,2,3],[2,5,4,3]) else (0,0,1)
            self.faces.append(([i+idx for i in fi], shade_color(color, n)))

    def add_star(self, x, y, z):
        self.stars.append(Star(x, y, z))
        self.star_count += 1

    def add_coins_line(self, x1, y1, z1, x2, y2, z2, count=5):
        for i in range(count):
            t = i/max(count-1,1)
            self.coins.append(Coin(x1+(x2-x1)*t, y1+(y2-y1)*t+30, z1+(z2-z1)*t))

    def add_enemy(self, x, y, z, kind="goomba"):
        self.enemies.append(Enemy(x, y, z, kind))

    def add_cap(self, x, y, z, kind="wing"):
        self.caps.append(CapBlock(x, y, z, kind))

    def add_coins_ring(self, cx, y, cz, r, count=8):
        for i in range(count):
            a = (2*math.pi*i)/count
            self.coins.append(Coin(cx+r*math.cos(a), y+30, cz+r*math.sin(a)))

    def add_tree(self, x, z, trunk_h=90, canopy_w=110, canopy_h=90):
        self.add_box(x, 30, z, 35, trunk_h, 35, TRUNK_BROWN)
        self.add_roof(x, trunk_h+20, z, canopy_w, canopy_h, canopy_w, TREE_GREEN)
        self.add_roof(x, trunk_h+60, z, canopy_w*0.7, canopy_h*0.6, canopy_w*0.7, TREE_GREEN)

    def build(self):
        pass

class CastleGrounds(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Peach's Castle"; self.sky_color = SKY_BLUE; self.spawn = (0, -720)
        self.build()
    def build(self):
        self.add_box(0,0,0,2000,10,2000,GRASS_GREEN)
        self.add_box(0,5,150,180,10,900,STONE_PATH)
        self.add_box(-1000,100,0,40,200,2000,STONE_GRAY)
        self.add_box(1000,100,0,40,200,2000,STONE_GRAY)
        self.add_box(0,100,1000,2000,200,40,STONE_GRAY)
        self.add_box(0,150,750,550,300,450,STONE_GRAY)
        self.add_box(0,350,750,160,220,160,STONE_GRAY)
        self.add_roof(0,470,750,200,160,200,ROOF_RED)
        self.add_box(-240,200,750,110,350,110,STONE_GRAY)
        self.add_roof(-240,420,750,130,110,130,ROOF_RED)
        self.add_box(240,200,750,110,350,110,STONE_GRAY)
        self.add_roof(240,420,750,130,110,130,ROOF_RED)
        self.add_box(0,-5,450,700,8,100,MOAT_BLUE)
        self.add_box(-350,-5,600,100,8,400,MOAT_BLUE)
        self.add_box(350,-5,600,100,8,400,MOAT_BLUE)
        self.add_box(0,5,450,180,14,110,WOOD_BROWN,collide=True)
        self.add_tree(-550,-450); self.add_tree(-700,300)
        self.add_tree(550,-450); self.add_tree(700,300)
        self.add_tree(-300,-600); self.add_tree(300,-600)
        self.add_coins_line(-400,0,-200,400,0,-200,8)
        self.add_coins_ring(0,0,-400,120,8)

class BobOmbBattlefield(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Bob-omb Battlefield"; self.sky_color = SKY_BLUE; self.spawn = (0, -800)
        self.build()
    def build(self):
        self.add_box(0,0,0,2400,10,2400,GRASS_GREEN)
        self.add_box(0,100,400,600,200,600,DARK_GREEN,collide=True)
        self.add_box(0,250,400,400,100,400,GRASS_GREEN,collide=True)
        self.add_box(0,350,400,200,100,200,DARK_GREEN,collide=True)
        self.add_roof(0,420,400,240,120,240,GRASS_GREEN)
        self.add_slope(200,5,200,150,100,300,STONE_PATH)
        self.add_box(-500,15,-300,40,80,40,WOOD_BROWN)
        self.add_box(-500,5,-300,120,12,120,DARK_GREEN)
        self.add_box(-500,80,-300,80,80,80,CHAIN_GRAY)
        self.add_box(600,0,-500,60,40,60,CANNON_BLACK)
        self.add_box(-600,0,600,60,40,60,CANNON_BLACK)
        for i in range(-6,7): self.add_box(i*80,15,-200,10,40,10,FENCE_BROWN)
        self.add_box(0,80,-100,200,12,60,WOOD_BROWN,collide=True)
        self.add_tree(-800,-600); self.add_tree(800,-600)
        self.add_tree(-700,800); self.add_tree(700,800)
        self.add_tree(-300,-700); self.add_tree(400,-500)
        self.add_box(-200,15,600,60,40,60,DARK_GRAY)
        self.add_box(300,15,700,50,35,50,DARK_GRAY)
        self.add_star(0,450,400); self.add_star(-500,100,-300); self.add_star(600,50,-500)
        self.add_coins_line(-300,0,-500,300,0,-500,8)
        self.add_coins_ring(0,200,400,100,8)
        self.add_coins_line(-700,0,0,-700,0,600,5)
        self.add_enemy(-200,0,200,"bobomb"); self.add_enemy(250,0,-100,"bobomb")
        self.add_enemy(-400,0,-400,"goomba"); self.add_enemy(100,0,500,"goomba")
        self.add_cap(0,280,400,"wing")

class WhompsFortress(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Whomp's Fortress"; self.sky_color = SKY_BLUE; self.spawn = (0, -500)
        self.build()
    def build(self):
        self.add_box(0,0,0,1400,10,1400,STONE_GRAY)
        self.add_box(0,60,200,600,120,600,STONE_GRAY,collide=True)
        self.add_box(50,180,250,400,120,400,DARK_GRAY,collide=True)
        self.add_box(0,300,300,250,120,250,STONE_GRAY,collide=True)
        self.add_box(0,420,300,200,30,200,STONE_PATH,collide=True)
        self.add_box(-350,60,0,100,20,200,STONE_PATH,collide=True)
        self.add_box(350,120,100,100,20,200,STONE_PATH,collide=True)
        self.add_box(-250,180,350,100,20,100,STONE_PATH,collide=True)
        self.add_box(100,200,100,80,80,80,DARK_GRAY)
        self.add_box(-100,320,250,80,80,80,DARK_GRAY)
        self.add_slope(-200,0,100,120,60,200,STONE_PATH)
        self.add_slope(150,120,200,100,60,150,STONE_PATH)
        self.add_box(0,400,350,80,200,80,STONE_GRAY)
        self.add_roof(0,550,350,100,60,100,ROOF_RED)
        self.add_box(-200,250,200,180,8,40,WOOD_BROWN,collide=True)
        self.add_box(350,140,350,40,60,40,CANNON_BLACK)
        self.add_star(0,460,300); self.add_star(0,580,350); self.add_star(-350,90,0)
        self.add_coins_line(-300,0,-300,300,0,-300,6)
        self.add_coins_line(-200,260,200,100,260,200,5)
        self.add_coins_ring(0,420,300,80,8)
        self.add_enemy(0,60,200,"whomp"); self.add_enemy(100,180,250,"goomba")
        self.add_cap(-250,200,350,"metal")

class JollyRogerBay(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Jolly Roger Bay"; self.sky_color = SKY_UNDERWATER; self.spawn = (0, -600); self.water_y = 40
        self.build()
    def build(self):
        self.add_box(0,0,-400,1200,10,500,SAND_YELLOW)
        self.add_box(0,-10,300,1800,8,1400,WATER_BLUE)
        self.add_box(0,-200,300,1800,10,1400,DEEP_WATER)
        self.add_box(300,-150,500,250,60,80,WOOD_BROWN)
        self.add_box(300,-120,500,200,30,60,DARK_BROWN)
        self.add_box(300,-90,500,20,100,10,WOOD_BROWN)
        self.add_box(-400,-100,700,200,120,200,CAVE_BROWN)
        self.add_box(-400,-50,700,160,60,160,CAVE_DARK)
        self.add_box(-200,-30,200,100,30,100,DARK_GRAY,collide=True)
        self.add_box(100,-20,350,80,30,80,DARK_GRAY,collide=True)
        self.add_box(0,-40,600,120,30,120,DARK_GRAY,collide=True)
        self.add_box(0,80,-650,1200,180,40,CAVE_BROWN)
        self.add_box(500,10,-300,200,14,80,WOOD_BROWN,collide=True)
        self.add_box(-300,-180,400,40,30,30,DARK_BROWN)
        self.add_box(200,-180,600,40,30,30,DARK_BROWN)
        self.add_box(500,-160,800,150,100,150,CAVE_DARK)
        self.add_star(300,-80,500); self.add_star(-400,-40,700); self.add_star(0,-30,600)
        self.add_coins_line(-400,0,-400,400,0,-400,8)
        self.add_coins_ring(0,-150,400,150,8)

class CoolCoolMountain(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Cool, Cool Mountain"; self.sky_color = SKY_SNOW; self.spawn = (0, -300)
        self.build()
    def build(self):
        self.add_box(0,0,0,2000,10,2000,SNOW_WHITE)
        self.add_box(0,80,300,900,160,900,SNOW_WHITE,collide=True)
        self.add_box(0,220,350,600,120,600,ICE_BLUE,collide=True)
        self.add_box(0,360,400,350,100,350,SNOW_WHITE,collide=True)
        self.add_box(0,470,400,180,80,180,SNOW_WHITE,collide=True)
        self.add_roof(0,540,400,220,140,220,SNOW_WHITE)
        self.add_box(60,540,400,50,80,50,BRICK_RED)
        self.add_box(-500,30,-500,150,100,120,WOOD_BROWN)
        self.add_roof(-500,100,-500,180,70,150,SNOW_WHITE)
        self.add_box(-200,150,100,250,10,60,ICE_BLUE,collide=True)
        self.add_box(400,25,-300,80,60,80,SNOW_WHITE)
        self.add_box(400,65,-300,60,50,60,SNOW_WHITE)
        self.add_box(400,100,-300,40,40,40,SNOW_WHITE)
        self.add_slope(-100,160,0,200,-100,400,ICE_BLUE)
        self.add_box(300,-5,-600,500,8,400,ICE_BLUE)
        for pos in [(-700,-700),(-600,-400),(700,-600),(600,-300),(-800,500),(800,400)]:
            self.add_box(pos[0],25,pos[1],25,80,25,TRUNK_BROWN)
            self.add_roof(pos[0],80,pos[1],80,100,80,DARK_GREEN)
            self.add_roof(pos[0],140,pos[1],60,70,60,DARK_GREEN)
        self.add_star(0,560,400); self.add_star(-500,100,-500); self.add_star(400,140,-300)
        self.add_coins_line(-400,0,-200,400,0,-200,8)
        self.add_coins_ring(0,350,400,100,8)

class BigBoosHaunt(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Big Boo's Haunt"; self.sky_color = SKY_MANSION; self.spawn = (0, -500)
        self.build()
    def build(self):
        self.add_box(0,0,0,2000,10,2000,MANSION_GREEN)
        self.add_box(0,150,300,500,300,400,MANSION_PURPLE)
        self.add_roof(0,350,300,550,200,450,DARK_GRAY)
        self.add_box(0,20,50,300,40,100,STONE_GRAY,collide=True)
        self.add_box(-120,60,50,20,100,20,STONE_GRAY)
        self.add_box(120,60,50,20,100,20,STONE_GRAY)
        self.add_box(0,80,100,60,100,10,DARK_BROWN)
        self.add_box(-150,200,100,60,60,10,BLACK)
        self.add_box(150,200,100,60,60,10,BLACK)
        self.add_box(-150,350,100,50,50,10,BLACK)
        self.add_box(150,350,100,50,50,10,BLACK)
        self.add_box(-350,100,300,200,200,250,MANSION_PURPLE)
        self.add_roof(-350,230,300,230,120,280,DARK_GRAY)
        self.add_box(350,100,300,200,200,250,MANSION_PURPLE)
        self.add_roof(350,230,300,230,120,280,DARK_GRAY)
        for gx,gz in [(-600,-200),(-500,-300),(-700,-100),(-550,-400),(600,-200),(500,-300),(700,-100),(550,-400)]:
            self.add_box(gx,20,gz,30,50,10,STONE_GRAY)
        self.add_box(-800,30,-500,25,120,25,DARK_BROWN)
        self.add_box(-780,100,-500,60,8,8,DARK_BROWN)
        self.add_box(800,30,-500,25,120,25,DARK_BROWN)
        self.add_box(810,90,-500,50,8,8,DARK_BROWN)
        for i in range(-4,5): self.add_box(i*120,15,-600,8,40,8,FENCE_BROWN)
        self.add_box(0,280,100,200,10,60,STONE_GRAY,collide=True)
        self.add_star(0,400,300); self.add_star(-350,220,300); self.add_star(350,220,300)
        self.add_coins_ring(0,0,-300,200,8)
        self.add_coins_line(-400,0,-200,400,0,-200,6)

class HazyMazeCave(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Hazy Maze Cave"; self.sky_color = SKY_CAVE; self.spawn = (0, -400)
        self.build()
    def build(self):
        self.add_box(0,0,0,2400,10,2400,CAVE_BROWN)
        # Ceiling — visual only (must not become a spawn floor)
        self.add_box(0,400,0,2400,10,2400,CAVE_DARK,collide=False)
        for px,pz in [(-400,-400),(400,-400),(-400,400),(400,400),(0,0)]:
            self.add_box(px,200,pz,80,400,80,CAVE_BROWN)
        self.add_box(-600,50,0,40,100,800,CAVE_DARK)
        self.add_box(600,50,0,40,100,800,CAVE_DARK)
        self.add_box(0,50,-800,1200,100,40,CAVE_DARK)
        self.add_box(-300,50,400,600,100,40,CAVE_DARK)
        self.add_box(300,50,-400,40,100,400,CAVE_DARK)
        self.add_box(-200,50,-200,40,100,400,CAVE_DARK)
        self.add_box(-700,-10,600,600,8,600,DEEP_WATER)
        self.add_box(-700,0,600,150,20,150,CAVE_BROWN,collide=True)
        self.add_box(700,0,700,200,20,200,METAL_GRAY,collide=True)
        self.add_box(700,30,700,40,60,40,METAL_GRAY)
        self.add_box(0,50,800,100,10,100,STONE_PATH,collide=True)
        self.add_box(-400,30,-600,200,15,60,STONE_PATH,collide=True)
        self.add_box(400,60,-600,200,15,60,STONE_PATH,collide=True)
        self.add_box(0,90,-600,200,15,60,STONE_PATH,collide=True)
        self.add_box(800,20,-400,60,50,60,DARK_GRAY)
        self.add_box(850,20,-500,50,40,50,DARK_GRAY)
        self.add_star(-700,40,600); self.add_star(700,50,700); self.add_star(0,110,-600)
        self.add_coins_line(-500,0,-300,500,0,-300,8)
        self.add_coins_ring(0,0,0,200,8)

class LethalLavaLand(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Lethal Lava Land"; self.sky_color = SKY_LAVA; self.spawn = (0, -600)
        self.build()
    def build(self):
        self.add_box(0,-20,0,3000,10,3000,LAVA_RED)
        self.add_box(0,-15,0,3000,6,3000,LAVA_ORANGE)
        self.add_box(0,10,-600,300,40,300,DARK_GRAY,collide=True)
        for i,(px,pz) in enumerate([(-200,-300),(0,-200),(200,-100),(300,100),(100,300)]):
            self.add_box(px,20+i*10,pz,120,30,120,STONE_GRAY,collide=True)
        self.add_box(0,80,600,500,160,500,VOLCANO_GRAY,collide=True)
        self.add_box(0,200,600,300,120,300,VOLCANO_GRAY,collide=True)
        self.add_box(0,300,600,150,80,150,VOLCANO_RED,collide=True)
        self.add_roof(0,370,600,180,100,180,VOLCANO_RED)
        self.add_box(0,310,600,100,5,100,LAVA_ORANGE)
        self.add_box(-500,30,300,200,50,200,DARK_GRAY,collide=True)
        self.add_box(500,20,-300,100,20,100,METAL_GRAY,collide=True)
        self.add_box(500,20,0,100,20,100,METAL_GRAY,collide=True)
        self.add_box(-300,15,0,200,12,40,WOOD_BROWN,collide=True)
        self.add_box(600,50,300,40,40,40,YELLOW)
        self.add_star(0,400,600); self.add_star(-500,80,300); self.add_star(100,80,300)
        self.add_coins_line(-200,30,-300,300,60,100,6)
        self.add_coins_ring(0,250,600,100,8)

class ShiftingSandLand(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Shifting Sand Land"; self.sky_color = SKY_DESERT; self.spawn = (0, -700)
        self.build()
    def build(self):
        self.add_box(0,0,0,3000,10,3000,SAND_YELLOW)
        self.add_box(-400,-8,0,400,6,400,DARK_BROWN)
        self.add_box(0,40,400,500,80,500,PYRAMID_TAN,collide=True)
        self.add_box(0,100,400,380,60,380,PYRAMID_TAN,collide=True)
        self.add_roof(0,160,400,420,250,420,PYRAMID_DARK)
        self.add_box(0,50,150,80,60,10,BLACK)
        self.add_box(600,-3,-500,250,8,250,WATER_BLUE)
        self.add_tree(600,-500,60,80,60); self.add_tree(650,-450,60,80,60)
        for px,pz in [(-600,400),(-700,200),(600,400),(700,200)]:
            self.add_box(px,50,pz,50,100,50,SAND_YELLOW)
        self.add_box(-600,5,-300,600,10,80,STONE_PATH)
        self.add_box(-600,20,-300,80,80,80,METAL_GRAY)
        self.add_box(700,60,700,150,120,150,SAND_YELLOW,collide=True)
        self.add_box(-200,40,-500,30,80,30,PYRAMID_DARK)
        self.add_box(200,40,-500,30,80,30,PYRAMID_DARK)
        self.add_box(0,90,-500,440,20,30,PYRAMID_DARK)
        self.add_star(0,420,400); self.add_star(700,180,700); self.add_star(-600,30,-300)
        self.add_coins_line(-400,0,-600,400,0,-600,8)
        self.add_coins_ring(0,100,400,150,8)

class DireDireDocks(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Dire, Dire Docks"; self.sky_color = SKY_UNDERWATER; self.spawn = (0, -400); self.water_y = 30
        self.build()
    def build(self):
        self.add_box(0,0,-400,600,10,300,STONE_GRAY)
        self.add_box(0,-15,300,2000,8,1500,DOCK_BLUE)
        self.add_box(0,-300,300,2000,10,1500,DEEP_WATER)
        self.add_box(-200,10,-200,80,14,300,WOOD_BROWN,collide=True)
        self.add_box(200,10,-200,80,14,300,WOOD_BROWN,collide=True)
        self.add_box(0,-10,500,300,60,120,METAL_GRAY)
        self.add_box(0,20,500,250,40,80,DARK_GRAY)
        self.add_box(0,50,450,30,60,10,METAL_GRAY)
        for i in range(5):
            z = 200+i*150
            self.add_box(300*(1 if i%2==0 else -1),-100,z,80,8,80,YELLOW)
        self.add_box(-600,-200,600,100,20,200,DEEP_WATER)
        self.add_box(0,-280,800,100,10,100,BLACK)
        self.add_box(500,-250,700,60,50,60,METAL_GRAY)
        self.add_box(-500,-200,800,60,60,60,DARK_GREEN)
        self.add_box(-400,-20,200,120,30,120,STONE_GRAY,collide=True)
        self.add_box(400,-30,400,100,30,100,STONE_GRAY,collide=True)
        self.add_star(0,60,500); self.add_star(-600,-160,600); self.add_star(500,-200,700)
        self.add_coins_line(-200,0,-400,200,0,-400,6)
        self.add_coins_ring(0,-100,400,200,8)

class SnowmansLand(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Snowman's Land"; self.sky_color = SKY_SNOW; self.spawn = (0, -600)
        self.build()
    def build(self):
        self.add_box(0,0,0,2400,10,2400,SNOW_WHITE)
        self.add_box(0,60,500,300,120,300,SNOW_WHITE,collide=True)
        self.add_box(0,170,500,220,100,220,SNOW_WHITE,collide=True)
        self.add_box(0,270,500,140,80,140,SNOW_WHITE,collide=True)
        self.add_box(0,330,500,160,15,160,BLACK)
        self.add_box(0,350,500,100,40,100,BLACK)
        self.add_box(-30,290,428,20,20,5,BLACK)
        self.add_box(30,290,428,20,20,5,BLACK)
        self.add_box(0,270,425,10,10,30,LAVA_ORANGE)
        self.add_box(-500,-5,-300,500,8,500,ICE_BLUE)
        self.add_box(500,30,-400,160,80,160,SNOW_WHITE)
        self.add_roof(500,90,-400,180,60,180,SNOW_WHITE)
        self.add_box(500,30,-320,50,50,10,DARK_BROWN)
        self.add_box(-300,30,200,100,15,100,ICE_BLUE,collide=True)
        self.add_box(-500,60,300,100,15,100,ICE_BLUE,collide=True)
        self.add_box(-700,90,200,100,15,100,ICE_BLUE,collide=True)
        self.add_box(600,30,500,200,15,200,ICE_BLUE,collide=True)
        for tx,tz in [(-800,-600),(-700,700),(800,-500),(700,600),(-400,-700),(400,-600)]:
            self.add_box(tx,25,tz,22,70,22,TRUNK_BROWN)
            self.add_roof(tx,70,tz,70,90,70,SNOW_WHITE)
        self.add_star(0,380,500); self.add_star(500,80,-400); self.add_star(-700,120,200)
        self.add_coins_line(-400,0,-500,400,0,-500,8)
        self.add_coins_ring(0,100,500,120,8)

class WetDryWorld(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Wet-Dry World"; self.sky_color = SKY_BLUE; self.spawn = (0, -400); self.water_y = 50
        self.build()
    def build(self):
        self.add_box(0,0,0,1800,10,1800,STONE_GRAY)
        self.add_box(0,30,0,1800,5,1800,WATER_BLUE)
        self.add_box(-400,100,300,200,200,200,STONE_GRAY,collide=True)
        self.add_box(-400,230,300,160,60,160,DARK_GRAY,collide=True)
        self.add_box(400,80,300,180,160,180,STONE_GRAY,collide=True)
        self.add_box(400,190,300,140,50,140,DARK_GRAY,collide=True)
        self.add_box(0,120,500,150,240,150,STONE_GRAY,collide=True)
        self.add_box(0,280,500,110,60,110,DARK_GRAY,collide=True)
        self.add_box(-200,40,-200,30,30,30,PURPLE)
        self.add_box(300,120,-100,30,30,30,PURPLE)
        self.add_box(0,250,500,30,30,30,PURPLE)
        self.add_box(-600,80,-300,250,160,250,METAL_GRAY)
        self.add_box(-600,170,-300,200,10,200,METAL_GRAY,collide=True)
        self.add_box(-200,60,0,150,8,60,WOOD_BROWN,collide=True)
        self.add_box(100,90,100,150,8,60,WOOD_BROWN,collide=True)
        self.add_box(-100,120,200,150,8,60,WOOD_BROWN,collide=True)
        self.add_box(600,50,0,80,8,80,YELLOW,collide=True)
        self.add_box(600,120,200,80,8,80,YELLOW,collide=True)
        self.add_box(0,50,-900,1800,100,30,STONE_GRAY)
        self.add_box(-900,50,0,30,100,1800,STONE_GRAY)
        self.add_box(900,50,0,30,100,1800,STONE_GRAY)
        self.add_star(0,340,500); self.add_star(-600,190,-300); self.add_star(600,140,200)
        self.add_coins_line(-500,0,-600,500,0,-600,8)
        self.add_coins_ring(0,60,0,150,8)

class TallTallMountain(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Tall, Tall Mountain"; self.sky_color = SKY_BLUE; self.spawn = (0, -400)
        self.build()
    def build(self):
        self.add_box(0,0,0,1600,10,1600,GRASS_GREEN)
        self.add_box(0,50,300,700,100,700,DARK_GREEN,collide=True)
        self.add_box(50,140,350,550,80,550,GRASS_GREEN,collide=True)
        self.add_box(0,220,400,400,80,400,DARK_GREEN,collide=True)
        self.add_box(-30,300,400,300,60,300,GRASS_GREEN,collide=True)
        self.add_box(0,370,400,200,50,200,DARK_GREEN,collide=True)
        self.add_box(0,430,400,120,40,120,GRASS_GREEN,collide=True)
        self.add_box(0,150,700,700,300,30,CAVE_BROWN)
        self.add_box(250,200,695,60,300,10,WATER_BLUE)
        self.add_box(-300,80,-200,30,80,30,STONE_GRAY)
        self.add_box(-300,110,-200,80,10,80,MARIO_RED,collide=True)
        self.add_box(-100,130,-100,30,120,30,STONE_GRAY)
        self.add_box(-100,170,-100,80,10,80,MARIO_RED,collide=True)
        self.add_box(40,460,400,50,60,50,DARK_BROWN)
        self.add_box(200,180,200,250,8,40,WOOD_BROWN,collide=True)
        self.add_box(-200,100,200,180,12,30,WOOD_BROWN,collide=True)
        self.add_box(-400,350,0,100,15,100,WHITE,collide=True)
        self.add_box(-200,400,100,100,15,100,WHITE,collide=True)
        self.add_tree(-600,-500); self.add_tree(600,-500)
        self.add_tree(-500,-300); self.add_tree(500,-200)
        self.add_star(0,480,400); self.add_star(-200,420,100); self.add_star(-300,130,-200)
        self.add_coins_line(-400,0,-400,400,0,-400,8)
        self.add_coins_ring(0,300,400,100,8)

class TinyHugeIsland(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Tiny-Huge Island"; self.sky_color = SKY_BLUE; self.spawn = (0, -600)
        self.build()
    def build(self):
        self.add_box(0,0,0,2200,10,2200,GRASS_GREEN)
        self.add_box(0,80,300,500,160,500,DARK_GREEN,collide=True)
        self.add_box(0,200,300,300,100,300,GRASS_GREEN,collide=True)
        self.add_roof(0,300,300,350,150,350,DARK_GREEN)
        self.add_box(0,-3,-700,800,8,300,SAND_YELLOW)
        self.add_box(0,-8,-900,800,6,200,WATER_BLUE)
        self.add_box(-400,10,-300,20,15,20,DARK_BROWN)
        self.add_box(-400,20,-300,25,8,25,MARIO_RED)
        self.add_box(-600,10,400,60,50,60,DARK_GREEN)
        self.add_box(600,10,-400,60,50,60,DARK_GREEN)
        self.add_box(300,150,500,120,80,120,CAVE_BROWN)
        self.add_box(300,150,500,80,60,80,CAVE_DARK)
        self.add_box(-500,5,-500,250,10,250,STONE_PATH)
        self.add_box(400,20,-200,80,40,80,STONE_GRAY)
        self.add_roof(400,50,-200,100,30,100,ROOF_RED)
        self.add_box(500,15,-100,60,30,60,STONE_GRAY)
        self.add_roof(500,35,-100,80,25,80,ROOF_RED)
        for px,pz in [(-200,200),(-100,350),(200,150)]:
            self.add_box(px,15,pz,15,40,15,DARK_GREEN)
            self.add_box(px,40,pz,30,15,30,MARIO_RED)
        self.add_box(-700,-5,700,300,6,300,WATER_BLUE)
        self.add_tree(-800,-200); self.add_tree(800,-300)
        self.add_tree(-300,700); self.add_tree(500,700)
        self.add_star(0,400,300); self.add_star(300,200,500); self.add_star(-600,60,400)
        self.add_coins_line(-600,0,-300,600,0,-300,10)
        self.add_coins_ring(0,100,300,120,8)

class TickTockClock(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Tick Tock Clock"; self.sky_color = SKY_CAVE; self.spawn = (0, -200)
        self.build()
    def build(self):
        self.add_box(0,0,0,600,10,600,CLOCK_BEIGE)
        self.add_box(-300,400,0,20,800,600,CLOCK_BEIGE)
        self.add_box(300,400,0,20,800,600,CLOCK_BEIGE)
        self.add_box(0,400,-300,600,800,20,CLOCK_BEIGE)
        self.add_box(0,400,300,600,800,20,CLOCK_BEIGE)
        platforms_data = [
            (0,40,0,200,12,200),(-100,100,50,150,10,60),(100,170,-50,150,10,60),
            (0,240,100,120,10,120),(-80,310,-80,100,10,100),(80,380,80,100,10,100),
            (0,450,0,150,10,80),(-100,520,100,100,10,100),(100,590,-100,100,10,100),
            (0,660,0,180,10,180),(0,740,0,250,10,250),
        ]
        for px,py,pz,pw,ph,pd in platforms_data:
            self.add_box(px,py,pz,pw,ph,pd,METAL_GRAY,collide=True)
        for gy in [150,350,550]:
            self.add_box(-280,gy,0,15,80,80,GOLD)
            self.add_box(280,gy,0,15,80,80,GOLD)
        self.add_box(0,300,-280,10,200,10,METAL_GRAY)
        self.add_box(0,200,-280,40,40,10,GOLD)
        self.add_box(0,780,0,280,10,280,WHITE)
        self.add_box(0,790,0,120,4,12,BLACK)
        self.add_box(0,790,0,8,4,80,BLACK)
        for i in range(12):
            a = (2*math.pi*i)/12
            self.add_box(math.sin(a)*120,790,math.cos(a)*120,15,6,15,BLACK)
        self.add_star(0,800,0); self.add_star(0,470,0); self.add_star(-100,530,100)
        self.add_coins_line(-100,100,0,100,100,0,4)
        self.add_coins_ring(0,450,0,60,6)
        self.add_coins_ring(0,740,0,100,8)

class RainbowRide(WorldBase):
    def __init__(self):
        super().__init__()
        self.name = "Rainbow Ride"; self.sky_color = SKY_RAINBOW; self.spawn = (0, -300)
        self.build()
    def build(self):
        self.add_box(0,0,-300,250,15,250,STONE_GRAY,collide=True)
        rcolors = [MARIO_RED,LAVA_ORANGE,YELLOW,GRASS_GREEN,SKY_BLUE,PURPLE,RAINBOW_PINK]
        for i in range(14):
            c = rcolors[i%len(rcolors)]
            self.add_box(math.sin(i*0.5)*150,i*15,i*100,80,8,80,c,collide=True)
        self.add_box(-300,200,800,250,50,100,WOOD_BROWN,collide=True)
        self.add_box(-300,230,800,200,30,70,DARK_BROWN)
        self.add_box(-300,270,800,10,100,10,WOOD_BROWN)
        self.add_box(-300,340,800,80,5,40,WHITE)
        self.add_box(400,250,600,180,120,150,STONE_GRAY,collide=True)
        self.add_roof(400,340,600,220,80,180,ROOF_RED)
        self.add_box(400,270,525,40,60,5,DARK_BROWN)
        self.add_box(-500,100,300,150,20,150,GRASS_GREEN,collide=True)
        self.add_box(500,150,400,120,20,120,GRASS_GREEN,collide=True)
        self.add_box(-200,300,1000,100,20,100,GRASS_GREEN,collide=True)
        self.add_box(200,80,200,80,8,80,RAINBOW_CYAN,collide=True)
        self.add_box(300,120,300,80,8,80,RAINBOW_LIME,collide=True)
        self.add_box(200,160,400,80,8,80,RAINBOW_PINK,collide=True)
        self.add_box(-400,150,500,100,8,60,WOOD_BROWN,collide=True)
        self.add_box(-100,200,700,100,8,60,WOOD_BROWN,collide=True)
        self.add_box(-600,80,100,50,40,50,CANNON_BLACK)
        for cx,cy,cz in [(300,400,300),(-200,350,600),(0,450,900)]:
            self.add_box(cx,cy,cz,120,20,80,WHITE)
        self.add_star(-300,320,800); self.add_star(400,380,600); self.add_star(-200,330,1000)
        for i in range(7):
            self.coins.append(Coin(math.sin(i*0.5)*150,i*15+30,i*100))
        self.add_coins_ring(-300,250,800,80,8)

COURSE_LIST = [
    ("Castle Grounds",CastleGrounds,"(Hub World)",STONE_GRAY),
    ("Bob-omb Battlefield",BobOmbBattlefield,"Course 1",GRASS_GREEN),
    ("Whomp's Fortress",WhompsFortress,"Course 2",STONE_GRAY),
    ("Jolly Roger Bay",JollyRogerBay,"Course 3",WATER_BLUE),
    ("Cool, Cool Mountain",CoolCoolMountain,"Course 4",SNOW_WHITE),
    ("Big Boo's Haunt",BigBoosHaunt,"Course 5",MANSION_PURPLE),
    ("Hazy Maze Cave",HazyMazeCave,"Course 6",CAVE_BROWN),
    ("Lethal Lava Land",LethalLavaLand,"Course 7",LAVA_RED),
    ("Shifting Sand Land",ShiftingSandLand,"Course 8",SAND_YELLOW),
    ("Dire, Dire Docks",DireDireDocks,"Course 9",DOCK_BLUE),
    ("Snowman's Land",SnowmansLand,"Course 10",SNOW_WHITE),
    ("Wet-Dry World",WetDryWorld,"Course 11",WATER_BLUE),
    ("Tall, Tall Mountain",TallTallMountain,"Course 12",DARK_GREEN),
    ("Tiny-Huge Island",TinyHugeIsland,"Course 13",GRASS_GREEN),
    ("Tick Tock Clock",TickTockClock,"Course 14",CLOCK_BEIGE),
    ("Rainbow Ride",RainbowRide,"Course 15",RAINBOW_PINK),
]

def render_world(surf, world, mario, cam):
    surf.fill(world.sky_color)
    rlist = []
    for indices, color in world.faces:
        pts = []; zs = 0; ok = True
        for i in indices:
            r = project_point(*world.verts[i], cam)
            if not r: ok = False; break
            pts.append((r[0], r[1])); zs += r[2]
        if ok and len(pts) >= 3:
            rlist.append((zs/len(indices), pts, color))
    for star in world.stars:
        star.update()
        sv, sf = star.get_mesh()
        for indices, color in sf:
            pts = []; zs = 0; ok = True
            for i in indices:
                r = project_point(*sv[i], cam)
                if not r: ok = False; break
                pts.append((r[0], r[1])); zs += r[2]
            if ok and len(pts) >= 3:
                rlist.append((zs/len(indices), pts, color))
    for coin in world.coins:
        coin.update()
        cv, cf = coin.get_mesh()
        for indices, color in cf:
            pts = []; zs = 0; ok = True
            for i in indices:
                r = project_point(*cv[i], cam)
                if not r: ok = False; break
                pts.append((r[0], r[1])); zs += r[2]
            if ok and len(pts) >= 3:
                rlist.append((zs/len(indices), pts, color))
    mv, mf = mario.get_mesh()
    for indices, color in mf:
        pts = []; zs = 0; ok = True
        for i in indices:
            r = project_point(*mv[i], cam)
            if not r: ok = False; break
            pts.append((r[0], r[1])); zs += r[2]
        if ok and len(pts) >= 3:
            rlist.append((zs/len(indices), pts, color))
    rlist.sort(key=lambda x: -x[0])
    for _, pts, color in rlist:
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, BLACK, pts, 1)

def draw_hud(surf, mario, world_name):
    total = getattr(draw_hud, "total_stars", 0)
    pygame.draw.rect(surf, (0, 0, 0), (0, 0, WIDTH, 48))
    line = hud_font.render(
        f"★{total}   COIN {mario.coins:03d}   ❤️{mario.lives}   HP {getattr(mario,'health',8)}/8",
        True, WHITE,
    )
    surf.blit(line, (12, 8))
    surf.blit(hud_font.render(world_name, True, YELLOW), (12, 28))
    if getattr(mario, "cap", None):
        surf.blit(
            hud_font.render(f"CAP {mario.cap.upper()} {max(0,mario.cap_timer)//60}s", True, (255, 210, 120)),
            (WIDTH - 240, 8),
        )
    if getattr(mario, "swim", False):
        surf.blit(hud_font.render("SWIM", True, WATER_BLUE), (WIDTH - 80, 28))
    tip = small_font.render(
        "WASD | SPACE JUMP/CHAIN | SHIFT+SPACE LONGJUMP | AIR SHIFT POUND | CTRL DIVE/PUNCH | Q/E CAM | ESC",
        True, WHITE,
    )
    surf.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT - 22))


class MenuScene:
    def __init__(self):
        self.ticks = 0; self.yaw = 0.0
    def update(self):
        self.ticks += 1; self.yaw += 0.03
    def draw(self, surf):
        surf.fill(NES_BLUE)
        cx, cy = WIDTH//2, HEIGHT//2+50
        pts = []
        raw = [(-50,-50,-50),(50,-50,-50),(50,50,-50),(-50,50,-50),(-50,-50,50),(50,-50,50),(50,50,50),(-50,50,50)]
        for v in raw:
            rx, rz = v[0]*math.cos(self.yaw)-v[2]*math.sin(self.yaw), v[0]*math.sin(self.yaw)+v[2]*math.cos(self.yaw)
            s = 400/(rz+300)
            pts.append((rx*s+cx, v[1]*s+cy))
        for fi in [[0,1,2,3],[4,5,6,7],[0,4,7,3],[1,5,6,2]]:
            col = MARIO_RED if fi[0]<4 else MARIO_BLUE
            pygame.draw.polygon(surf, col, [pts[i] for i in fi])
            pygame.draw.polygon(surf, BLACK, [pts[i] for i in fi], 2)
        logo = "acs's sm64 py port 0.1"
        try:
            logo_font = pygame.font.SysFont("Arial Black", 42, bold=True)
        except Exception:
            logo_font = pygame.font.Font(None, 52)
        sh = logo_font.render(logo, True, BLACK)
        ti = logo_font.render(logo, True, YELLOW)
        sr = ti.get_rect(center=(WIDTH//2, 130))
        surf.blit(sh, (sr.x+4, sr.y+4)); surf.blit(ti, sr)
        sb = menu_font.render("~ FILES_OFF engine ~", True, WHITE)
        surf.blit(sb, sb.get_rect(center=(WIDTH//2, 195)))
        if (self.ticks//30)%2==0:
            pr = menu_font.render("PRESS SPACE TO START", True, WHITE)
            surf.blit(pr, pr.get_rect(center=(WIDTH//2, HEIGHT-80)))

class LetterScene:
    def __init__(self):
        self.lines = ["Dear Mario,","","Please come to the castle.","I've baked a cake for you.","","Yours truly,","Princess Toadstool","  ~ Peach"]
        self.timer = 0
    def update(self):
        self.timer += 1
    def draw(self, surf):
        surf.fill(BLACK)
        paper = pygame.Rect(0,0,450,400)
        paper.center = (WIDTH//2, HEIGHT//2)
        pygame.draw.rect(surf, PARCHMENT, paper)
        pygame.draw.rect(surf, INK_COLOR, paper, 4)
        y = paper.top+50
        for line in self.lines:
            t = letter_font.render(line, True, INK_COLOR)
            surf.blit(t, t.get_rect(center=(WIDTH//2, y)))
            y += 40
        if self.timer > 60:
            pr = hud_font.render("Press SPACE to Continue", True, WHITE)
            surf.blit(pr, (WIDTH-280, HEIGHT-40))

class LevelSelectScene:
    def __init__(self, total_stars=0):
        self.cursor = 0; self.scroll = 0; self.total_stars = total_stars
    def update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w): self.cursor = max(0, self.cursor-1)
                elif e.key in (pygame.K_DOWN, pygame.K_s): self.cursor = min(len(COURSE_LIST)-1, self.cursor+1)
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN): return self.cursor
        if self.cursor < self.scroll: self.scroll = self.cursor
        if self.cursor >= self.scroll+8: self.scroll = self.cursor-7
        return None
    def draw(self, surf):
        surf.fill((20,15,40))
        ti = title_font.render("SELECT COURSE", True, STAR_YELLOW)
        surf.blit(ti, ti.get_rect(center=(WIDTH//2, 55)))
        st = menu_font.render(f"Total Stars: \u2605 {self.total_stars}", True, YELLOW)
        surf.blit(st, st.get_rect(center=(WIDTH//2, 105)))
        y0 = 145; rh = 52
        for i in range(self.scroll, min(self.scroll+8, len(COURSE_LIST))):
            name, _, label, color = COURSE_LIST[i]
            y = y0+(i-self.scroll)*rh
            if i == self.cursor:
                pygame.draw.rect(surf, (50,45,80), (60, y-4, WIDTH-120, rh-4))
                pygame.draw.rect(surf, STAR_YELLOW, (60, y-4, WIDTH-120, rh-4), 2)
            need = STAR_GATES.get(name, 0)
            locked = self.total_stars < need
            pygame.draw.rect(surf, color if not locked else DARK_GRAY, (80, y+4, 30, 30))
            pygame.draw.rect(surf, WHITE, (80, y+4, 30, 30), 1)
            lb = small_font.render(label, True, (180,180,180))
            surf.blit(lb, (125, y+2))
            lock_txt = f"  [need {need}★]" if locked else ""
            ncol = (110, 110, 110) if locked else (WHITE if i == self.cursor else (200, 200, 200))
            n = select_font.render(name + lock_txt, True, ncol)
            surf.blit(n, (125, y+18))
        if self.scroll > 0:
            a = menu_font.render("\u25b2", True, WHITE)
            surf.blit(a, a.get_rect(center=(WIDTH//2, y0-15)))
        if self.scroll+8 < len(COURSE_LIST):
            a = menu_font.render("\u25bc", True, WHITE)
            surf.blit(a, a.get_rect(center=(WIDTH//2, y0+8*rh+5)))
        cl = small_font.render("UP/DOWN: Navigate | SPACE/ENTER: Select | ESC: Menu", True, (150,150,150))
        surf.blit(cl, cl.get_rect(center=(WIDTH//2, HEIGHT-20)))

class StarGetScene:
    def __init__(self):
        self.timer = 0
    def update(self):
        self.timer += 1
    def draw(self, surf, total_stars):
        o = pygame.Surface((WIDTH, HEIGHT))
        o.fill(BLACK); o.set_alpha(min(self.timer*4, 180))
        surf.blit(o, (0,0))
        if self.timer > 20:
            bob = math.sin(self.timer*0.1)*5
            for angle in range(0, 360, 72):
                a = math.radians(angle+self.timer*2)
                sx = WIDTH//2+math.cos(a)*(30*2+20)
                sy = HEIGHT//2-30+math.sin(a)*(30*2+20)+bob
                pygame.draw.circle(surf, STAR_YELLOW, (int(sx), int(sy)), max(3, 10))
            tx = star_font.render("\u2605 STAR GET! \u2605", True, STAR_YELLOW)
            surf.blit(tx, tx.get_rect(center=(WIDTH//2, HEIGHT//2-30)))
            c = menu_font.render(f"Total: {total_stars}", True, WHITE)
            surf.blit(c, c.get_rect(center=(WIDTH//2, HEIGHT//2+30)))
        if self.timer > 120:
            pr = small_font.render("Press SPACE to continue", True, WHITE)
            surf.blit(pr, pr.get_rect(center=(WIDTH//2, HEIGHT//2+80)))

# ============================================================
# Example Behavior Scripts
# ============================================================

obj_mgr = None

# Floating platform script: bobs up and down
def _bhv_float_platform_loop(obj):
    obj.oPosY = obj.oHomeY + math.sin(obj.oTimer * 0.03) * 50.0

script_floating_platform = [
    _BC_BB(BHV_BEGIN, OBJ_LIST_SURFACE),
] + bhv_or_int(OFFLAGS, OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE) + [
] + bhv_set_home() + [
] + bhv_set_float(OCOLLISIONDISTANCE, 500) + [
] + bhv_begin_loop() + [
] + bhv_call_native(_bhv_float_platform_loop) + [
] + bhv_end_loop()

# Rotating platform script
def _bhv_rot_platform_loop(obj):
    obj.oFaceAngleYaw = (obj.oFaceAngleYaw + 100) % 65536

script_rotating_platform = [
    _BC_BB(BHV_BEGIN, OBJ_LIST_SURFACE),
] + bhv_or_int(OFFLAGS, OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE) + [
] + bhv_set_home() + [
] + bhv_begin_loop() + [
] + bhv_call_native(_bhv_rot_platform_loop) + [
] + bhv_end_loop()

# Simple bouncing coin-like object
def _bhv_bounce_coin_loop(obj):
    obj.oPosY = obj.oHomeY + abs(math.sin(obj.oTimer * 0.08)) * 40.0
    obj.oFaceAngleYaw = (obj.oTimer * 500) % 65536

script_bouncing_coin = [
    _BC_BB(BHV_BEGIN, OBJ_LIST_LEVEL),
] + bhv_billboard() + [
] + bhv_or_int(OFFLAGS, OBJ_FLAG_UPDATE_GFX_POS_AND_ANGLE) + [
] + bhv_set_home() + [
] + bhv_set_int(OINTANGIBLETIMER, 0) + [
] + bhv_begin_loop() + [
] + bhv_call_native(_bhv_bounce_coin_loop) + [
] + bhv_end_loop()

def init_obj_manager():
    global obj_mgr
    obj_mgr = ObjectManager()

    # Register native behavior functions
    obj_mgr.interpreter.native_funcs[id(_bhv_float_platform_loop)] = _bhv_float_platform_loop
    obj_mgr.interpreter.native_funcs[id(_bhv_rot_platform_loop)] = _bhv_rot_platform_loop
    obj_mgr.interpreter.native_funcs[id(_bhv_bounce_coin_loop)] = _bhv_bounce_coin_loop

    # Register models
    # Model 1: Gold coin (a flat rectangle)
    coin_verts = [(0,0,0),(20,0,0),(20,20,0),(0,20,0)]
    coin_faces = [([0,1,2,3], GOLD)]
    obj_mgr.register_model(1, coin_verts, coin_faces, GOLD)

    # Model 2: Star-shaped indicator (small diamond)
    star_verts = [(0,15,0),(10,0,0),(0,-15,0),(-10,0,0)]
    star_faces = [([0,1,3], STAR_YELLOW), ([1,2,3], STAR_YELLOW)]
    obj_mgr.register_model(2, star_verts, star_faces, STAR_YELLOW)

    # Model 3: Floating platform
    plat_verts = [(-50,0,-50),(50,0,-50),(50,0,50),(-50,0,50),(-50,10,-50),(50,10,-50),(50,10,50),(-50,10,50)]
    plat_faces = [
        ([0,1,2,3], STONE_GRAY), ([4,5,6,7], DARK_GRAY),
        ([0,4,5,1], STONE_GRAY), ([1,5,6,2], STONE_GRAY),
        ([2,6,7,3], STONE_GRAY), ([0,4,7,3], STONE_GRAY)
    ]
    obj_mgr.register_model(3, plat_verts, plat_faces, STONE_GRAY)

    # Model 4: Box (for rotating platform demo)
    box_verts = [(-30,-30,-30),(30,-30,-30),(30,30,-30),(-30,30,-30),(-30,-30,30),(30,-30,30),(30,30,30),(-30,30,30)]
    box_faces = [
        ([0,1,2,3], MARIO_RED), ([4,5,6,7], MARIO_BLUE),
        ([0,4,5,1], MARIO_RED), ([1,5,6,2], MARIO_RED),
        ([2,6,7,3], MARIO_RED), ([0,4,7,3], MARIO_RED)
    ]
    obj_mgr.register_model(4, box_verts, box_faces, MARIO_RED)

    # Spawn demo objects (will be usable from level selector or optionally in every level)
    # These are spawned but their rendering is optional

def spawn_demo_objects(world=None):
    """Spawn behavior-driven objects in the current level."""
    global obj_mgr
    if world is None:
        return
    # Spawn floating platforms near interesting locations
    obj_mgr.spawn(script_floating_platform, 3, 300, 50, -400)
    obj_mgr.spawn(script_floating_platform, 3, -300, 50, 400)

def render_bhv_objects(surf, cam, mario):
    """Render behavior-driven objects."""
    global obj_mgr
    if obj_mgr is None:
        return
    for obj, verts, faces, color in obj_mgr.get_renderable_objects():
        rlist = []
        for indices, face_color in faces:
            pts = []; zs = 0; ok = True
            for i in indices:
                v = verts[i]
                wx = obj.oPosX + v[0]
                wy = obj.oPosY + v[1] + obj.oGraphYOffset
                wz = obj.oPosZ + v[2]
                r = project_point(wx, wy, wz, cam)
                if not r: ok = False; break
                pts.append((r[0], r[1])); zs += r[2]
            if ok and len(pts) >= 3:
                rlist.append((zs/len(indices), pts, face_color))
        rlist.sort(key=lambda x: -x[0])
        for _, pts, fc in rlist:
            pygame.draw.polygon(surf, fc, pts)
            pygame.draw.polygon(surf, BLACK, pts, 1)

def main():
    state = STATE_MENU
    menu_scene = MenuScene()
    letter_scene = LetterScene()
    level_sel = LevelSelectScene()
    star_scene = StarGetScene()
    mario = None
    cam = None
    world = None
    total_stars = 0
    running = True

    # Initialize ObjectManager with behavior scripts
    init_obj_manager()

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False

        if state == STATE_MENU:
            menu_scene.update()
            menu_scene.draw(screen)
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    letter_scene = LetterScene()
                    state = STATE_LETTER

        elif state == STATE_LETTER:
            letter_scene.update()
            letter_scene.draw(screen)
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    level_sel = LevelSelectScene(total_stars)
                    state = STATE_LEVEL_SEL

        elif state == STATE_LEVEL_SEL:
            level_sel.total_stars = total_stars
            choice = level_sel.update(events)
            level_sel.draw(screen)
            if choice is not None:
                cname, WorldClass, _, _ = COURSE_LIST[choice]
                need = STAR_GATES.get(cname, 0)
                if total_stars >= need:
                    world = WorldClass()
                    mario = Mario(*world.spawn)
                    mario.snap_to_floor(world.platforms)
                    mario.water_y = getattr(world, "water_y", None)
                    cam = Camera(mario)
                    pygame.mouse.get_rel()
                    obj_mgr.interpreter.objects.clear()
                    spawn_demo_objects(world)
                    state = STATE_PLAYING
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    state = STATE_MENU

        elif state == STATE_PLAYING:
            mario.water_y = getattr(world, "water_y", None)
            result = mario.update(keys, cam.yaw, world.platforms)
            cam.update(keys)
            got_star = False
            for star in world.stars:
                if star.check(mario):
                    total_stars += 1
                    got_star = True
                    play_sfx("star")
            for coin in world.coins:
                if coin.check(mario):
                    mario.give_coin(1)
            for cap in getattr(world, "caps", []):
                cap.update()
                cap.check(mario)
            for enemy in getattr(world, "enemies", []):
                er = enemy.update(mario)
                if er == "death":
                    result = "death"
            obj_mgr.update_all()
            render_world(screen, world, mario, cam)
            render_bhv_objects(screen, cam, mario)
            # render enemies + caps
            for enemy in getattr(world, "enemies", []):
                ev, ef = enemy.get_mesh()
                # fold into simple draw
                for indices, color in ef:
                    pts = []; ok = True
                    for i in indices:
                        r = project_point(*ev[i], cam)
                        if not r: ok = False; break
                        pts.append((r[0], r[1]))
                    if ok and len(pts) >= 3:
                        pygame.draw.polygon(screen, color, pts)
                        pygame.draw.polygon(screen, BLACK, pts, 1)
            for cap in getattr(world, "caps", []):
                cv, cf = cap.get_mesh()
                for indices, color in cf:
                    pts = []; ok = True
                    for i in indices:
                        r = project_point(*cv[i], cam)
                        if not r: ok = False; break
                        pts.append((r[0], r[1]))
                    if ok and len(pts) >= 3:
                        pygame.draw.polygon(screen, color, pts)
            draw_hud.total_stars = total_stars
            draw_hud(screen, mario, world.name)
            if got_star:
                star_scene = StarGetScene()
                state = STATE_STAR_GET
            if result == "death":
                if mario.lives <= 0:
                    state = STATE_MENU
                    total_stars = 0
                else:
                    mario.respawn(*world.spawn)
                    mario.snap_to_floor(world.platforms)
                    mario.water_y = getattr(world, "water_y", None)
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    level_sel = LevelSelectScene(total_stars)
                    state = STATE_LEVEL_SEL

        elif state == STATE_STAR_GET:
            render_world(screen, world, mario, cam)
            render_bhv_objects(screen, cam, mario)
            draw_hud.total_stars = total_stars
            draw_hud(screen, mario, world.name)
            star_scene.update()
            star_scene.draw(screen, total_stars)
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and star_scene.timer > 60:
                    state = STATE_PLAYING

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
