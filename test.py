from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

# --- UPDATED: Camera zoomed out significantly (Z moved from 400 to 2000) ---
camera_pos = (200, 0, 2000)

wpn_lst = ['missile',"speed",'invincible','bullet','mine']
wpn = 'mine'
box_rotation = 0

# --- UPDATED: Window made bigger ---
width, height = 1600, 1000

#colors
road = (0.75, 0.75, 0.75)
grass = (0.2, 0.9, 0.2)
border = (0.6, 0.0, 0.8)
lava   = (0.6, 0.1, 0.1)
water  = (0.25, 0.6, 0.9)
white  = (1, 1, 1)


def generate_points(count, x_range, y_range):
    # x_range and y_range should be tuples like (min, max)
    #first 5 points are x, last 5 points are y
    points = []
    for _ in range(count):
        points.append(random.uniform(x_range[0], x_range[1]))
    for _ in range(count):
        points.append(random.uniform(y_range[0], y_range[1]))
    return points

box_spawn = generate_points(5,(500,-500),(500,-500))

fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines
rand_var = 423


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, width, 0, height)  # Updated to match new width/height


    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


quad = gluNewQuadric()   # create once, outside draw loop

def draw_missile(x, y, z, yaw=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(yaw, 0, 0, 1)


    glScalef(0.2, 0.2, 0.2)

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
    fins = [
        (0,  40, 0,   0),
        (0, -40, 0,   0),
        (0,  0, 40,  90),
        (0,  0,-40,  90)
    ]

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
    glScalef(0.3,0.3,0.3)
    glTranslatef(x, y, z)

    # --- PINK FLATTENED BASE ---
    glPushMatrix()
    glColor3f(1.0, 0.4, 0.7)
    glScalef(1.0, 1.0, 0.4)  # Flatten the sphere into a disc

    gluSphere(quad, 80, 20, 20)
    glPopMatrix()

    # --- TRIGGER BUTTON (Top Center) ---
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.0)
    glTranslatef(0, 0, 25)
    gluSphere(quad, 30, 16, 16)
    glPopMatrix()


    glColor3f(0.2, 0.2, 0.2) # Dark Grey
    for i in range(4):
        glPushMatrix()
        glRotatef(i * 90, 0, 0, 1)
        glTranslatef(70, 0, 0)
        glutSolidCube(20)
        glPopMatrix()

    glPopMatrix()


def draw_shapes():
    global box_spawn
    #wpn box
    x1,x2,x3,x4,x5,y1,y2,y3,y4,y5 = box_spawn
    draw_wpn_box(x1,y1)
    draw_wpn_box(x2,y2)
    draw_wpn_box(x3,y3)
    draw_wpn_box(x4,y4)
    draw_wpn_box(x5,y5)

    #missile
    draw_missile(0,-500,200)

    if wpn=="mine":
        draw_mine(400,400,0)

    glPushMatrix()

    glScalef(0.3,0.3,0.3)
    #wheels
    glTranslatef(0,0,100)

    glColor3f(0,0,0)
    glTranslatef(180,270-10,0)
    gluSphere(gluNewQuadric(),80,10,10)
    glTranslatef(-180,-270+10,0)

    glTranslatef(-180,-270+10,0)
    gluSphere(gluNewQuadric(),80,10,10)
    glTranslatef(180,270-10,0)

    glTranslatef(180,-270-10,0)
    gluSphere(gluNewQuadric(),80,10,10)
    glTranslatef(-180,270+10,0)

    glTranslatef(-180,270+10,0)
    gluSphere(gluNewQuadric(),80,10,10)
    glTranslatef(180,-270-10,0)

    glTranslatef(0,0,-100)



    #chasis
    glColor3f(0,0,1)
    glTranslatef(0,0,100)
    glScalef(1,0.8,0.1)

    glutSolidCube(600)

    glScalef(1,1/0.8,1/0.1)

    glColor3f(1,0,0)
    glTranslatef(-120,0,100)
    glScalef(0.1,1.7,0.8)
    glutSolidCube(300) #front bar
    glScalef(1/0.1,1/1.7,1/0.8)


    glColor3f(1,0,0)
    glTranslatef(340,0,0)
    glScalef(1,2.8,1)
    glutSolidCube(150) #back cube
    glScalef(1,1/2.8,1)
    glTranslatef(-340,0,0)

    glScalef(1,1,0.8)
    glRotatef(-90,0,1,0)

    gluCylinder(gluNewQuadric(),180,120,155,10,10) #front cylinder
    glRotatef(90,0,1,0)
    glTranslatef(120,0,-100) #back to 000

    glTranslatef(0,0,-100)


    #legs
    glColor3f(0,0.5,1)
    glTranslate(100,0,250)
    glRotatef(180,0,1,0)
    glTranslate(0,50,0)
    gluCylinder(gluNewQuadric(),50,10,150,10,10)
    glTranslate(0,-100,0)
    gluCylinder(gluNewQuadric(),50,10,150,10,10)

    glRotatef(180,0,1,0)
    glTranslate(-100,50,-250)

    #hands
    h = 150
    z = 400
    glTranslatef(100,50,z)
    glRotatef(-90,0,1,0)
    glColor3f(1.0, 0.8588, 0.6745)
    gluCylinder(gluNewQuadric(),50,10,h,10,10)

    glTranslatef(0,-100,0)
    gluCylinder(gluNewQuadric(),50,10,h,10,10)
    glRotatef(90,0,1,0)

    glTranslatef(-100,50,-z)

    #body
    glColor3f(0,1,0)
    glTranslate(100,0,350)
    glScalef(1/2,2,2)
    glutSolidCube(100)
    glScalef(2,1/2,1/2)
    glTranslate(-100,0,-350)


    #head
    glColor3f(0,0,0)
    glTranslate(100,0,500)
    gluSphere(gluNewQuadric(),50,10,10)
    glTranslate(-100,0,-500)

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
    box(0, 700, 0, 1400, 400, 20, grass)
    box(0, -700, 0, 1400, 400, 20, grass)
    box(-900, 0, 0, 400, 900, 20, grass)
    box(900, 0, 0, 400, 900, 20, grass)

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
    """
    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    # ... (No changes here)
    if key == " ":
        if wpn == '':
            pass
        elif wpn=="missile":
            pass
        elif wpn=="bullet":
            pass
        elif wpn=="speed":
            pass
        elif wpn=="invincible":
            pass

def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_pos
    x, y, z = camera_pos
    if key == GLUT_KEY_LEFT:
        x -= 50  # Increased speed for larger map
    if key == GLUT_KEY_RIGHT:
        x += 50  # Increased speed for larger map

    camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
   pass


def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # --- UPDATED: Adjusted far clip plane to 10000 to see full map ---
    # --- UPDATED: Aspect ratio set to width/height to avoid stretching ---
    gluPerspective(fovY, width/height, 0.1, 10000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos
    gluLookAt(x, y, z,  # Camera position
              0, 0, 0,  # Look-at target
              0, 0, 1)  # Up vector (z-axis)


def idle():
    global box_rotation
    box_rotation=box_rotation + 1 if box_rotation<=360  else  0
    glutPostRedisplay()


def showScreen():
    """
    Display function to render the game scene
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, width, height)

    setupCamera()

    glPushMatrix()
    # --- UPDATED: Doubled the scale of the map (3 -> 6) ---
    glScalef(6, 6, 6) 
    draw_map()
    glPopMatrix()
    
    # Display game info text
    draw_text(10, height - 30, f"A Random Fixed Position Text")
    draw_text(10, height - 60, f"Current Weapon :{wpn}")

    draw_shapes()

    glutSwapBuffers()


# Main function to set up OpenGL window and loop
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