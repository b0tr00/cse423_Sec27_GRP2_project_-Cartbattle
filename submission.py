from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time

# --- GLOBAL VARIABLES ---
# Player State

game_over = False
shake_duration = 0
shake_intensity = 40.0

cheat_mode = Falsew
player_bullets = []
bullets_remaining = 0
PLAYER_BULLET_SPEED = 80

score = 0
player_pos = [0, 0, 0]
player_angle = 0
is_first_person = False

invincible_active = False
invincible_start_time = 0
INVINCIBLE_DURATION = 5.0 # seconds

# --- CAMERAS ---
cam_yaw = 0.0
cam_pitch = 45.0
cam_dist = 3000.0

speed = 50
default_speed = 50
boost_speed = 250
boost_active = False
boost_start_time = 0

# Enemy State
enemies = []
enemy_bullets = []
NUM_ENEMIES = 5
ENEMY_SPEED = 8
AGGRO_RANGE = 1500
BULLET_SPEED = 40
BULLET_SIZE = 30

# Map Boundaries
MAP_LIMIT_X = 3000
MAP_LIMIT_Y = 5000

# Map Scales (Used for drawing and collision calc)
MAP_SCALE_X = 4.5
MAP_SCALE_Y = 12.0

# Obstacles List [{'type': 'rect', 'x_min':, 'x_max':, 'y_min':, 'y_max':}, {'type': 'circle', 'x':, 'y':, 'r':}]
OBSTACLES = []

# Zoom Constraints
MIN_DIST = 300
MAX_DIST = 6000
ZOOM_SPEED = 100
ROTATION_SPEED = 2.0
hp = 100

wpn_lst = ['missile',"speed",'invincible','bullet','mine']
wpn = 'bullet'
wpn_active = False
box_rotation = 0

missile_pos = [0, 0, 0]
missile_angle = 0
missile_active = False
MISSILE_SPEED = 50

active_mines = []

width, height = 1600, 1000

xrange = (2800,-2800)
yrange = (2800,-2800)

#colors
road = (0.75, 0.75, 0.75)
grass = (0.2, 0.9, 0.2)
border = (0.6, 0.0, 0.8)
lava   = (0.6, 0.1, 0.1)
water  = (0.25, 0.6, 0.9)
white  = (1, 1, 1)

def generate_points(count, x_range, y_range):
    points = []
    for _ in range(count):
        points.append(random.uniform(x_range[0], x_range[1]))
    for _ in range(count):
        points.append(random.uniform(y_range[0], y_range[1]))
    return points

x1,x2,x3,x4,x5,y1,y2,y3,y4,y5 = generate_points(5,xrange,yrange)

# --- COLLISION LOGIC FOR MAP OBSTACLES ---
def init_obstacles():
    """ Calculates the world-space bounding boxes of the walls and spheres """
    global OBSTACLES
    OBSTACLES = []
    
    # Dimensions from draw_map (Before scaling)
    open_gap = 140
    half_w = 450
    half_h = 250
    thick = 25
    
    # We need to apply the Global Scale (4.5, 12) to these logic coordinates
    SX = MAP_SCALE_X
    SY = MAP_SCALE_Y
    
    # Helper to add a wall rect
    def add_wall(cx, cy, sx, sy):
        # Convert center/size to min/max bounds in world space
        # Center in world space
        wx = cx * SX
        wy = cy * SY
        # Half-width/height in world space
        wh = (sx / 2) * SX
        hh = (sy / 2) * SY
        
        OBSTACLES.append({
            'type': 'rect',
            'x_min': wx - wh,
            'x_max': wx + wh,
            'y_min': wy - hh,
            'y_max': wy + hh
        })

    # 1. Top Walls (Horizontal)
    # Left part: box(-half_w + open//2,  half_h, 0, half_w - open, thick, ...)
    add_wall(-half_w + open_gap//2, half_h, half_w - open_gap, thick)
    # Right part: box( half_w - open//2,  half_h, 0, half_w - open, thick, ...)
    add_wall(half_w - open_gap//2, half_h, half_w - open_gap, thick)

    # 2. Bottom Walls (Horizontal)
    add_wall(-half_w + open_gap//2, -half_h, half_w - open_gap, thick)
    add_wall(half_w - open_gap//2, -half_h, half_w - open_gap, thick)

    # 3. Left Walls (Vertical)
    # Top part: box(-half_w,  half_h - open//2, 0, thick, half_h - open, ...)
    add_wall(-half_w, half_h - open_gap//2, thick, half_h - open_gap)
    # Bottom part
    add_wall(-half_w, -half_h + open_gap//2, thick, half_h - open_gap)

    # 4. Right Walls (Vertical)
    add_wall(half_w, half_h - open_gap//2, thick, half_h - open_gap)
    add_wall(half_w, -half_h + open_gap//2, thick, half_h - open_gap)

    # 5. Spheres
    # sphere(-200, 150, 25, ...)
    # Radius roughly 25 * 4.5 (using X scale as approximation) = ~110
    sphere_locs = [(-200, 150), (200, 150), (-200, -150), (200, -150)]
    for (sx, sy) in sphere_locs:
        OBSTACLES.append({
            'type': 'circle',
            'x': sx * SX,
            'y': sy * SY,
            'r': 25 * SX # Scaled radius
        })

init_obstacles()

def check_obstacle_collision(x, y, radius=50):
    """ Returns True if the point (x,y) with radius hits any static obstacle """
    for obs in OBSTACLES:
        if obs['type'] == 'rect':
            # AABB Collision (Box vs Point/Box)
            # Add radius buffer to the wall bounds
            if (x + radius > obs['x_min'] and x - radius < obs['x_max'] and
                y + radius > obs['y_min'] and y - radius < obs['y_max']):
                return True
        elif obs['type'] == 'circle':
            # Circle Collision
            dist = math.sqrt((x - obs['x'])**2 + (y - obs['y'])**2)
            if dist < (obs['r'] + radius):
                return True
    return False

def init_enemies():
    global enemies
    enemies = []
    for _ in range(NUM_ENEMIES):
        e = {
            'x': random.uniform(-MAP_LIMIT_X, MAP_LIMIT_X),
            'y': random.uniform(-MAP_LIMIT_Y, MAP_LIMIT_Y),
            'z': 0,
            'angle': random.uniform(0, 360),
            'last_shot_time': 0,
            'hp': 5  
        }
        # Don't spawn inside a wall
        while check_obstacle_collision(e['x'], e['y'], 150):
             e['x'] = random.uniform(-MAP_LIMIT_X, MAP_LIMIT_X)
             e['y'] = random.uniform(-MAP_LIMIT_Y, MAP_LIMIT_Y)
        enemies.append(e)

init_enemies()

fovY = 120
GRID_LENGTH = 600
rand_var = 423
quad = gluNewQuadric()


def get_shake_offset():
    global shake_duration, shake_intensity
    if shake_duration > 0:
        shake_duration -= 1
        ox = random.uniform(-shake_intensity, shake_intensity)
        oy = random.uniform(-shake_intensity, shake_intensity)
        oz = random.uniform(-shake_intensity, shake_intensity)
        return ox, oy, oz
    return 0, 0, 0

def box_collision():
    global x1,x2,x3,x4,x5,y1,y2,y3,y4,y5, wpn,hp

    if  player_pos[0]-100<=x1<=player_pos[0]+100 and player_pos[1]-100<=y1<=player_pos[1]+100:
        wpn = random.choice(wpn_lst)
        x1,y1 = random.uniform(xrange[0], xrange[1]) , random.uniform(yrange[0], yrange[1])
        hp+=20

    elif  player_pos[0]-100<=x2<=player_pos[0]+100 and player_pos[1]-100<=y2<=player_pos[1]+100:
        wpn = random.choice(wpn_lst)
        x2,y2 = random.uniform(xrange[0], xrange[1]) , random.uniform(yrange[0], yrange[1])
        hp+=20

    elif  player_pos[0]-100<=x3<=player_pos[0]+100 and player_pos[1]-100<=y3<=player_pos[1]+100:
        wpn = random.choice(wpn_lst)
        x3,y3 = random.uniform(xrange[0], xrange[1]) , random.uniform(yrange[0], yrange[1])
        hp+=20

    elif  player_pos[0]-100<=x4<=player_pos[0]+100 and player_pos[1]-100<=y4<=player_pos[1]+100:
        wpn = random.choice(wpn_lst)
        x4,y4 = random.uniform(xrange[0], xrange[1]) , random.uniform(yrange[0], yrange[1])
        hp+=20

    elif  player_pos[0]-100<=x5<=player_pos[0]+100 and player_pos[1]-100<=y5<=player_pos[1]+100:
        wpn = random.choice(wpn_lst)
        x5,y5 = random.uniform(xrange[0], xrange[1]) , random.uniform(yrange[0], yrange[1])
        hp+=20

def update_missile():
    global missile_active, missile_pos, missile_angle, enemies,score
    if missile_active:
        # Movement logic
        if missile_angle == 0:      missile_pos[0] -= MISSILE_SPEED
        elif missile_angle == 180:  missile_pos[0] += MISSILE_SPEED
        elif missile_angle == -90:  missile_pos[1] += MISSILE_SPEED
        elif missile_angle == 90:   missile_pos[1] -= MISSILE_SPEED

        # Check collision with Obstacles (Wall/Spheres)
        if check_obstacle_collision(missile_pos[0], missile_pos[1], 50):
            missile_active = False
            print("Missile hit a wall!")
            return

        # Check collision with enemies
        for e in enemies:
            dist = math.sqrt((missile_pos[0] - e['x'])**2 + (missile_pos[1] - e['y'])**2)
            if dist < 300: # Hitbox radius
                e['hp'] -= 5
                score+=1
                missile_active = False # Missile explodes on hit
                print(f"Missile Hit! Enemy HP: {e['hp']}")
                break

        # Bounds check
        if abs(missile_pos[0]) > MAP_LIMIT_X*2 or abs(missile_pos[1]) > MAP_LIMIT_Y*2:
            missile_active = False

def update_player_bullets():
    global player_bullets, enemies, score
    bullets_to_remove = []

    for b in player_bullets:
        b['x'] += b['dx']
        b['y'] += b['dy']

        # Check collision with Obstacles
        if check_obstacle_collision(b['x'], b['y'], 20):
            if b not in bullets_to_remove:
                bullets_to_remove.append(b)
            continue

        # Check collision with each enemy
        for e in enemies:
            dist = math.sqrt((b['x'] - e['x'])**2 + (b['y'] - e['y'])**2)
            if dist < 250: # Enemy Hitbox
                e['hp'] -= 2  # Deal 2 damage
                score+= 1
                print(f"Enemy Hit! HP: {e['hp']}")
                if b not in bullets_to_remove:
                    bullets_to_remove.append(b)
                break

        # Remove if off map
        if abs(b['x']) > MAP_LIMIT_X*2 or abs(b['y']) > MAP_LIMIT_Y*2:
            if b not in bullets_to_remove:
                bullets_to_remove.append(b)

    for b in bullets_to_remove:
        if b in player_bullets:
            player_bullets.remove(b)


def update_enemy_bullets():
    global hp, enemy_bullets, invincible_active, shake_duration
    bullets_to_remove = []

    for b in enemy_bullets:
        b['x'] += b['dx']
        b['y'] += b['dy']

        # Check collision with Obstacles
        if check_obstacle_collision(b['x'], b['y'], 20):
            if b not in bullets_to_remove:
                bullets_to_remove.append(b)
            continue

        dist_to_player = math.sqrt((b['x'] - player_pos[0])**2 + (b['y'] - player_pos[1])**2)

        if dist_to_player < 100:
            # ONLY take damage if NOT invincible
            if not invincible_active:
                hp -= 5
                shake_duration = 10
                print(f"Hit! HP: {hp}")
            else:
                print("Blocked! Invincible!")

            bullets_to_remove.append(b)

        # Remove if out of bounds
        elif abs(b['x']) > MAP_LIMIT_X or abs(b['y']) > MAP_LIMIT_Y:
            bullets_to_remove.append(b)

    # Clean up bullets
    for b in bullets_to_remove:
        if b in enemy_bullets:
            enemy_bullets.remove(b)

def check_invincible():
    global invincible_active, cheat_mode
    if cheat_mode:
        invincible_active = True
        return
    if invincible_active:
        if time.time() - invincible_start_time > INVINCIBLE_DURATION:
            invincible_active = False
            print("Invincibility Expired")

def check_mine_collisions():
    global active_mines, enemies,score

    remaining_mines = []

    for m in active_mines:
        mine_exploded = False
        for e in enemies:
            dist = math.sqrt((m['x'] - e['x'])**2 + (m['y'] - e['y'])**2)
            if dist < 300:
                e['hp'] -= 5  # Apply 5 damage
                score+= 1
                mine_exploded = True
                print(f"BOOM! Mine Hit! Enemy HP: {e['hp']}")
                break

        if not mine_exploded:
            remaining_mines.append(m)

    active_mines = remaining_mines

    # Filter out dead enemies and respawn them
    enemies = [e for e in enemies if e['hp'] > 0]

    while len(enemies) < NUM_ENEMIES:
        e = {
            'x': random.uniform(-MAP_LIMIT_X, MAP_LIMIT_X),
            'y': random.uniform(-MAP_LIMIT_Y, MAP_LIMIT_Y),
            'z': 0,
            'angle': random.uniform(0, 360),
            'last_shot_time': 0,
            'hp': 5
        }
        # Respawn safely away from walls
        while check_obstacle_collision(e['x'], e['y'], 150):
             e['x'] = random.uniform(-MAP_LIMIT_X, MAP_LIMIT_X)
             e['y'] = random.uniform(-MAP_LIMIT_Y, MAP_LIMIT_Y)
        enemies.append(e)


def check_boost():
    global boost_active, speed, default_speed, cheat_mode
    if cheat_mode: return

    if boost_active:
        current_time = time.time()
        # If the difference between current time and start time is > 5 seconds
        if current_time - boost_start_time > 5:
            speed = default_speed
            boost_active = False


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_bullet(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(1, 0, 0)
    glutSolidSphere(BULLET_SIZE, 10, 10)
    glPopMatrix()

def draw_missile(x, y, z, yaw=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(yaw, 0, 0, 1)
    glScalef(1, 1, 1)
    # BODY
    glPushMatrix()
    glColor3f(0.7, 0.7, 0.7)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, 30, 30, 300, 16, 4)
    glPopMatrix()
    # NOSE
    glPushMatrix()
    glColor3f(1, 0, 0)
    glTranslatef(300, 0, 0)
    glScalef(1.2, 1, 1)
    gluSphere(quad, 30, 16, 16)
    glPopMatrix()
    # ENGINE + FINS
    glPushMatrix()
    glColor3f(0.3, 0.3, 0.3)
    gluSphere(quad, 28, 12, 12)
    glColor3f(0.2, 0.2, 1)
    fins = [(0,40,0,0), (0,-40,0,0), (0,0,40,90), (0,0,-40,90)]
    for fx, fy, fz, rot in fins:
        glPushMatrix()
        glTranslatef(fx, fy, fz)
        glRotatef(rot, 1, 0, 0)
        glScalef(0.1, 1.5, 0.5)
        glutSolidCube(40)
        glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def draw_wpn_box(x,y,z=20):
        glPushMatrix()
        glColor3f(1,0,0.5)
        glTranslate(x,y,z)
        glRotatef(box_rotation,0,0,1)
        glutSolidCube(50)
        glPopMatrix()

def draw_mine(x, y, z):
    glPushMatrix()
    glScalef(0.5,0.5,0.5)
    glTranslatef(x, y, z)
    glPushMatrix()
    glColor3f(1.0, 0.4, 0.7)
    glScalef(1.0, 1.0, 0.4)
    gluSphere(quad, 80, 20, 20)
    glPopMatrix()
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.0)
    glTranslatef(0, 0, 25)
    gluSphere(quad, 30, 16, 16)
    glPopMatrix()
    glColor3f(0.2, 0.2, 0.2)
    for i in range(4):
        glPushMatrix()
        glRotatef(i * 90, 0, 0, 1)
        glTranslatef(70, 0, 0)
        glutSolidCube(20)
        glPopMatrix()
    glPopMatrix()


def draw_car_model(is_enemy=False):
    """
    Draws the car geometry.
    If is_enemy is True, draws it in black.
    """

    # Define colors based on role
    if is_enemy:
        c_wheel = (0.1, 0.1, 0.1)
        c_chassis = (0.05, 0.05, 0.05)
        c_bar = (0.2, 0.2, 0.2)
        c_back = (0.1, 0.1, 0.1)
        c_cyl = (0.15, 0.15, 0.15)
        c_legs = (0.1, 0.1, 0.1)
        c_hands = (0.2, 0.2, 0.2)
        c_body = (0.0, 0.0, 0.0)
        c_head = (0.3, 0.0, 0.0) # Red eyes for enemy
    else:
        if invincible_active:
                    # GOLD/YELLOW TINT
                    c_wheel = (0.5, 0.5, 0)
                    c_chassis = (1.0, 1.0, 0.0)
                    c_bar = (1.0, 0.8, 0.0)
                    c_back = (1.0, 1.0, 0.5)
                    c_cyl = (1.0, 1.0, 0.8)
                    c_legs = (1.0, 0.9, 0.0)
                    c_hands = (1.0, 0.9, 0.5)
                    c_body = (1.0, 1.0, 0.0)
                    c_head = (1.0, 1.0, 0.0)
        else:
                    # NORMAL PLAYER COLORS
                    c_wheel = (0, 0, 0)
                    c_chassis = (0, 0, 1)
                    c_bar = (1, 0, 0)
                    c_back = (1, 0, 0)
                    c_cyl = (1, 1, 0.8)
                    c_legs = (0, 0.5, 1)
                    c_hands = (1.0, 0.8588, 0.6745)
                    c_body = (0, 1, 0)
                    c_head = (0, 0, 0)

    #wheels
    glPushMatrix()
    glTranslatef(0,0,100)
    glColor3f(*c_wheel)
    glTranslatef(180,270-10,0)
    gluSphere(quad,80,10,10)
    glTranslatef(-180,-270+10,0)
    glTranslatef(-180,-270+10,0)
    gluSphere(quad,80,10,10)
    glTranslatef(180,270-10,0)
    glTranslatef(180,-270-10,0)
    gluSphere(quad,80,10,10)
    glTranslatef(-180,270+10,0)
    glTranslatef(-180,270+10,0)
    gluSphere(quad,80,10,10)
    glTranslatef(180,-270-10,0)
    glTranslatef(0,0,-100)
    glPopMatrix()

    #chasis
    glPushMatrix()
    glColor3f(*c_chassis)
    glTranslatef(0,0,100)
    glScalef(1,0.8,0.1)
    glutSolidCube(600)
    glScalef(1,1/0.8,1/0.1) # Reset scale

    glColor3f(*c_bar)
    glTranslatef(-120,0,100)
    glScalef(0.1,1.7,0.8)
    glutSolidCube(300)
    glScalef(1/0.1,1/1.7,1/0.8)

    glColor3f(*c_back)
    glTranslatef(340,0,0)
    glScalef(1,2.8,1)
    glutSolidCube(150)
    glScalef(1,1/2.8,1)
    glTranslatef(-340,0,0)

    # Front Cylinder
    glScalef(1,1,0.8)
    glRotatef(-90,0,1,0)
    if not is_enemy: glColor3f(1,1,1) # Keep cylinder white-ish for player, or passed color
    else: glColor3f(*c_cyl)
    gluCylinder(quad,180,120,155,10,10)
    glRotatef(90,0,1,0)
    glScalef(1,1,1/0.8) # Reset
    glPopMatrix()

    #legs
    glPushMatrix()
    glColor3f(*c_legs)
    glTranslate(100,0,250)
    glRotatef(180,0,1,0)
    glTranslate(0,50,0)
    gluCylinder(quad,50,10,150,10,10)
    glTranslate(0,-100,0)
    gluCylinder(quad,50,10,150,10,10)
    glPopMatrix()

    #hands
    glPushMatrix()
    h = 150
    z = 400
    glTranslatef(100,50,z)
    glRotatef(-90,0,1,0)
    glColor3f(*c_hands)
    gluCylinder(quad,50,10,h,10,10)
    glTranslatef(0,-100,0)
    gluCylinder(quad,50,10,h,10,10)
    glPopMatrix()

    #body
    glPushMatrix()
    glColor3f(*c_body)
    glTranslate(100,0,350)
    glScalef(1/2,2,2)
    glutSolidCube(100)
    glPopMatrix()

    #head
    glPushMatrix()
    glColor3f(*c_head)
    glTranslate(100,0,500)
    gluSphere(quad,50,10,10)
    glPopMatrix()

def draw_shapes():
    global game_over, hp
    if hp <= 0:
        hp = 0
        game_over = True

    draw_wpn_box(x1,y1)
    draw_wpn_box(x2,y2)
    draw_wpn_box(x3,y3)
    draw_wpn_box(x4,y4)
    draw_wpn_box(x5,y5)


    for b in player_bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], 100)
        glColor3f(0, 0, 0)
        glutSolidSphere(20, 10, 10)
        glPopMatrix()

    for b in enemy_bullets:
        draw_bullet(b['x'], b['y'], 100)

    if missile_active:
        # Drawing at z=100 ensures it is visible above the road
        draw_missile(missile_pos[0], missile_pos[1], 100, missile_angle+180)

    for m in active_mines:
            draw_mine(m['x'], m['y'], 0)

    # --- DRAW PLAYER ---
# Inside draw_shapes where you draw the player:
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_angle, 0, 0, 1)
    glScalef(0.45, 0.45, 0.45)

    if game_over:
        glRotatef(180, 1, 0, 0) # Flip upside down on X-axis
        glTranslatef(0, 0, -100) # Sink it slightly so wheels are up

    if invincible_active:
        # Make the player yellow/gold when invincible
        # This overrules the default colors in draw_car_model
        glColor3f(1.0, 1.0, 0.0)

    draw_car_model(is_enemy=False)
    glPopMatrix()

    # --- DRAW ENEMIES ---
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['x'], e['y'], e['z'])
        # Rotate to face movement direction
        # Enemy angles are usually math standard (0=Right), but our car 0 is Left?
        # Let's align visual rotation with the stored angle.
        # For simplicity, let's assume 'angle' is in degrees compatible with glRotatef
        glRotatef(e['angle'], 0, 0, 1)

        # UPDATED: Enemy is 80% of Player size (0.45 * 0.8 = 0.36)
        glScalef(0.36, 0.36, 0.36)
        draw_car_model(is_enemy=True)
        glPopMatrix()

def box(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(*color)
    glutSolidCube(1)
    glPopMatrix()

def sphere(x, y, z, r, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    glutSolidSphere(r, 20, 20)
    glPopMatrix()

def draw_map():
    box(0, 0, 0, 1400, 900, 20, road)
    box(0, 550, 0, 1400, 200, 20, grass)
    box(0, -550, 0, 1400, 200, 20, grass)
    box(-800, 0, 0, 200, 900, 20, grass)
    box(800, 0, 0, 200, 900, 20, grass)
    box(0, 450, 0, 1400, 30, 80, border)
    box(0, -450, 0, 1400, 30, 80, border)
    box(700, 0, 0, 30, 900, 80, border)
    box(-700, 0, 0, 30, 900, 80, border)
    box(0, 0, 1, 900, 500, 20, road)

    open = 140
    half_w = 450
    half_h = 250
    thick = 25
    height = 60

    box(-half_w + open//2,  half_h, 0, half_w - open, thick, height, border)
    box( half_w - open//2,  half_h, 0, half_w - open, thick, height, border)
    box(-half_w + open//2, -half_h, 0, half_w - open, thick, height, border)
    box( half_w - open//2, -half_h, 0, half_w - open, thick, height, border)
    box(-half_w,  half_h - open//2, 0, thick, half_h - open, height, border)
    box(-half_w, -half_h + open//2, 0, thick, half_h - open, height, border)
    box( half_w,  half_h - open//2, 0, thick, half_h - open, height, border)
    box( half_w, -half_h + open//2, 0, thick, half_h - open, height, border)

    sphere(-200, 150, 25, 25, border)
    sphere(200, 150, 25, 25, border)
    sphere(-200,-150, 25, 25, border)
    sphere(200,-150, 25, 25, border)

def keyboardListener(key, x, y):
    global player_pos, player_angle, wpn, missile_active, missile_pos, missile_angle, \
           speed, boost_active, boost_start_time, cam_dist, invincible_active, \
           invincible_start_time, cheat_mode, game_over, hp, score, enemies, active_mines, bullets_remaining,player_bullets

    next_x = player_pos[0]
    next_y = player_pos[1]
    #restart game
    if key == b'r':
        hp = 100
        score = 0
        player_pos = [0, 0, 0]
        player_angle = 0
        game_over = False
        active_mines = []
        player_bullets = []
        bullets_remaining = 0
        wpn = ''
        init_enemies() # Reset enemy positions
        print("Game Restarted!")
        glutPostRedisplay()
        return



    if game_over:
        return

    if key == b'w':
        next_x -= speed
        player_angle = 0
    if key == b's':
        next_x += speed
        player_angle = 180
    if key == b'a':
        next_y -= speed
        player_angle =  90
    if key == b'd':
        next_y += speed
        player_angle = -90

    # Only update player_pos if NO WALL COLLISION and INSIDE MAP
    if (-MAP_LIMIT_X < next_x < MAP_LIMIT_X and 
        -MAP_LIMIT_Y < next_y < MAP_LIMIT_Y and 
        not check_obstacle_collision(next_x, next_y, 80)): # Radius 80 for player
        
        player_pos[0] = next_x
        player_pos[1] = next_y


    # Zoom Controls
    if key == b'j': # Zoom In
        cam_dist -= ZOOM_SPEED
        if cam_dist < MIN_DIST: cam_dist = MIN_DIST
    if key == b'k': # Zoom Out
        cam_dist += ZOOM_SPEED
        if cam_dist > MAX_DIST: cam_dist = MAX_DIST

    if key == b'c':
        cheat_mode = not cheat_mode
        if cheat_mode:
            speed = boost_speed
            invincible_active = True
            print("CHEAT MODE: ON")
        else:
            speed = default_speed
            invincible_active = False
            print("CHEAT MODE: OFF")

    if key == b' ':
     if cheat_mode:
            # In cheat mode, we bypass the "wpn == 'missile'" check
            # and we can fire even if another missile is active (multi-missile)
            new_missile_pos = list(player_pos)
            # To handle infinite missiles, we'd ideally use a list like mines
            # But for your current structure, we just reset the current one instantly
            missile_active = True
            missile_pos = list(player_pos)
            missile_angle = player_angle
     else:
        if wpn == 'missile' and not missile_active:
            missile_active = True
            missile_pos = list(player_pos)
            missile_angle = player_angle
            wpn = ''


        elif wpn == 'mine':
            new_mine = {'x': player_pos[0], 'y': player_pos[1]}
            active_mines.append(new_mine)
            wpn = ''
        elif wpn == 'speed':
            boost_active = True
            boost_start_time = time.time() # Record the exact current time
            speed = boost_speed
            wpn = '' # Remove weapon from inventory
            print("Speed Boost Activated!")


        elif wpn == 'invincible':
            invincible_active = True
            invincible_start_time = time.time()
            wpn = ''
            print("Invincibility Activated!")
        elif wpn == 'bullet':
            bullets_remaining = 5  # Give 5 shots
            wpn = '' # Remove the "weapon box" icon as it's now "loaded"
            print("Ammo Loaded: 5 Bullets")

        # If they already have ammo loaded, fire a bullet
        elif bullets_remaining > 0:
            bullets_remaining -= 1
            # Create a bullet traveling in the direction the player is facing
            # Using your current player_angle logic: 0=-X, 180=+X, 90=-Y, -90=+Y
            dx, dy = 0, 0
            if player_angle == 0:    dx = -PLAYER_BULLET_SPEED
            elif player_angle == 180: dx = PLAYER_BULLET_SPEED
            elif player_angle == 90:  dy = -PLAYER_BULLET_SPEED
            elif player_angle == -90: dy = PLAYER_BULLET_SPEED

            new_bullet = {
                'x': player_pos[0],
                'y': player_pos[1],
                'dx': dx,
                'dy': dy
            }
            player_bullets.append(new_bullet)
            print(f"Fire! Bullets left: {bullets_remaining}")

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global cam_yaw, cam_pitch

    if not is_first_person:
        if key == GLUT_KEY_LEFT:
            cam_yaw -= ROTATION_SPEED
        if key == GLUT_KEY_RIGHT:
            cam_yaw += ROTATION_SPEED

        if key == GLUT_KEY_UP:
            cam_pitch += ROTATION_SPEED
            if cam_pitch < 10: cam_pitch = 10
        if key == GLUT_KEY_DOWN:
            cam_pitch -= ROTATION_SPEED
            if cam_pitch > 89: cam_pitch = 89

        glutPostRedisplay()

def mouseListener(button, state, x, y):
    global is_first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        is_first_person = not is_first_person
        glutPostRedisplay()

def setupCamera():
    global camX,camY,camZ
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, width/height, 0.1, 25000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    sx, sy, sz = get_shake_offset()

    if is_first_person:
        angle_rad = math.radians(player_angle)

        # --- FIXED: Move camera higher (Z+255) so it's ABOVE the head ---
        # The head center is at Z=225. Radius is ~22.5.
        # Z=255 is safe.
        head_offset_x = 45 * math.cos(angle_rad)
        head_offset_y = 45 * math.sin(angle_rad)

        camX = player_pos[0] + head_offset_x
        camY = player_pos[1] + head_offset_y
        camZ = player_pos[2] + 255 # MOVED UP to avoid being inside the head

        # Look target
        lookX = camX - 1000 * math.cos(angle_rad)
        lookY = camY - 1000 * math.sin(angle_rad)

        gluLookAt(camX + sx, camY + sy, camZ + sz,
                  lookX + sx, lookY + sy, camZ - 50 + sz,
                  0, 0, 1)
    else:
        rad_yaw = math.radians(cam_yaw)
        rad_pitch = math.radians(cam_pitch)

        offset_z = cam_dist * math.sin(rad_pitch)
        proj_dist_xy = cam_dist * math.cos(rad_pitch)
        offset_x = proj_dist_xy * math.cos(rad_yaw)
        offset_y = proj_dist_xy * math.sin(rad_yaw)

        camX = player_pos[0] + offset_x
        camY = player_pos[1] + offset_y
        camZ = player_pos[2] + offset_z

        gluLookAt(camX + sx, camY + sy, camZ + sz,
                  player_pos[0] + sx, player_pos[1] + sy, player_pos[2] + sz,
                  0, 0, 1)

def update_enemies():
    current_time = time.time()

    for e in enemies:
        rad = math.radians(e['angle'])
        dx = -math.cos(rad) * ENEMY_SPEED
        dy = -math.sin(rad) * ENEMY_SPEED
        
        next_x = e['x'] + dx
        next_y = e['y'] + dy

        # Wall Collision Check
        if check_obstacle_collision(next_x, next_y, 60): # 60 is enemy size buffer
            e['angle'] += random.randint(110, 250) # Bounce back
        else:
            e['x'] = next_x
            e['y'] = next_y

        # Map Boundary Check
        if e['x'] < -MAP_LIMIT_X or e['x'] > MAP_LIMIT_X:
            e['angle'] = 180 - e['angle']
        if e['y'] < -MAP_LIMIT_Y or e['y'] > MAP_LIMIT_Y:
            e['angle'] = -e['angle']

        dist_x = player_pos[0] - e['x']
        dist_y = player_pos[1] - e['y']
        distance = math.sqrt(dist_x**2 + dist_y**2)

        if distance < AGGRO_RANGE:
            if current_time - e['last_shot_time'] >= 1.0:
                e['last_shot_time'] = current_time
                norm_x = dist_x / distance
                norm_y = dist_y / distance
                new_bullet = {
                    'x': e['x'],
                    'y': e['y'],
                    'dx': norm_x * BULLET_SPEED,
                    'dy': norm_y * BULLET_SPEED
                }
                enemy_bullets.append(new_bullet)

def idle():
    global box_rotation
    if game_over:
        glutPostRedisplay()
        return
    box_rotation = box_rotation + 1 if box_rotation<=360 else 0
    update_enemies()
    update_missile()
    update_enemy_bullets()
    box_collision()
    check_mine_collisions()
    check_invincible()
    update_player_bullets()
    check_boost()


    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, width, height)
    setupCamera()

    glPushMatrix()
    glScalef(4.5, 12, 6)
    draw_map()
    glPopMatrix()

    if not game_over:
        draw_text(10, height - 60, f"Enemies: {len(enemies)}")
        draw_text(10, height - 90, f"Current Weapons: {wpn}")

        draw_text(10, height - 30, f"Player HP: {hp}")
        current_time = time.time()
        draw_text(10, height - 150, f"Ammo: {bullets_remaining}")
        draw_text(750, height - 30, f"Score: {score}")
        if boost_active:
            draw_text(10,height-180,f"Boost ends in: {int(5 -(current_time - boost_start_time))}")

            current_time = time.time()
        if invincible_active==True and cheat_mode==False:
            draw_text(10,height-180,f"Invincibility ends in: {int(5 -(current_time - invincible_start_time))}")
        if not is_first_person:
            draw_text(10, height - 120, f"Zoom: {int(cam_dist)} | Pitch: {int(cam_pitch)}")

    else:

        draw_text(700, height - 300, f"Game Over. Press r To Restart The Game")
        draw_text(790, height - 330, f"Your Score Was:{score}")

    draw_shapes()
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"3D OpenGL Intro")

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()