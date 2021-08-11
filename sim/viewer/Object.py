try:
  from tkinter import Tk, Canvas, Toplevel
except ImportError:
  from Tkinter import Tk, Canvas, Toplevel

import colorsys
from sim.util.utils import user_input
import sys

# COLORS = ['#0b032d', '#621940', '#843b62', '#f67e7d', '#ffb997']
MOVABLE_COLORS = ['#E3B5A4', '#E8D6CB', '#C3DFE0', '#F6E4F6', '#F4F4F4']
IMMOVABLE_COLORS = ['#621940', '#843B62', '#5E3886']
TEXT_COLOR = '#0B032D'
BLACK = '#0B032D'
BACKGROUND = '#F5E9E2'
TABLE_BACKGROUND = '#F5F8E8'
TABLE_COLOR = '#8789C0'
# ARM_NOT_EMPTY_COLOR = '#843b62'
ARM_NOT_EMPTY_COLOR = '#000000'


# -----------------------------------


class Object:
  def __init__(self, col_row, xy, obj_id, color = 'grey', size = 25):
    self.volume = []
    self.move(col_row, xy)
    self.type = 'object'
    self.id = obj_id
    self.color = color
    self.size = size
    self.movable = True
    

  def move(self, col_row, xy):
    self.c = col_row[0]
    self.r = col_row[1]
    self.x = xy[0]
    self.y = xy[1]
    self.volume = [col_row]





# -----------------------------------




class Square(Object):
  def __init__(self, col_row, xy, obj_id, side, color = 'grey', movable=True):
    # self.isHeld = False
    super().__init__(col_row, xy, obj_id, color, side)
    self.type = 'square'
    self.side = side
    self.movable = movable
    self.slippery = False


  def draw(self, cells, canvas, slippery=False, isSlippery = None):
    cells[(self.x, self.y)] = [
      canvas.create_rectangle(self.x - self.side / 2., self.y - self.side / 2.,
                                    self.x + self.side / 2., self.y + self.side / 2.,
                                    fill=self.color, outline='black', width=2),
      canvas.create_text(self.x, self.y, text=self.id, fill=TEXT_COLOR),
    ]
    if slippery:
      if isSlippery == None:
        cells[(self.x, self.y)] += [ 
          canvas.create_rectangle(self.x - self.side / 2., self.y - self.side / 2.-2,
                                      self.x + self.side / 2., self.y - self.side / 2. + 3,
                                      fill="grey", outline="grey", width=2) ]
      elif isSlippery == True:
        cells[(self.x, self.y)] += [ 
          canvas.create_rectangle(self.x - self.side / 2., self.y - self.side / 2.-2,
                                      self.x + self.side / 2., self.y - self.side / 2. + 3,
                                      fill="#80cbc4", outline="#80cbc4", width=2) ]


    


  def grasp(self):
    # self.isHeld = True
    self.volume = [] # object has been grasped - remove its volume
    
  def ungrasp(self):
    # self.isHeld = False
    self.volume = [[self.c, self.r]] # add volume back

  def move(self, col_row, xy):
    self.c = col_row[0]
    self.r = col_row[1]
    self.x = xy[0]
    self.y = xy[1]
    if len(self.volume) != 0:
      self.volume = [col_row]
    # an object that is held has no volume - it's volume is part of the arm
    # if self.isHeld:
    #   self.volume = []




# -----------------------------------




class Arm(Object):
  def __init__(self, col_row, xy, side=25, draw_fingers=False, block_buffer=10, stemStart = 0):
    self.volume = [col_row]
    self.armEmpty = True
    super().__init__(col_row, xy, -1)
    
    self.type = 'arm'
    self.side = side
    self.draw_fingers = draw_fingers
    self.block_buffer = block_buffer
    self.robot = []
    self.objectHeld = -1
    self.stemStart = stemStart
    self.move(col_row, xy)
    self.infill_color = MOVABLE_COLORS[0] if self.movable else IMMOVABLE_COLORS[0]  
    self.color = self.infill_color if self.armEmpty else ARM_NOT_EMPTY_COLOR

  def move(self, col_row, xy):
    self.c = col_row[0]
    self.r = col_row[1]
    self.x = xy[0]
    self.y = xy[1]
    if len(self.volume) != 0:
      self.volume[0] = col_row
    else:
      self.volume = col_row

    # adjust volume of the arm if holding an object
    if not self.armEmpty:
      if len(self.volume) == 1:
        self.volume.append([self.c, self.r-1])
      else:
        self.volume[1] = [self.c, self.r-1]

  def grasp(self, obj):
    self.objectHeld = obj.id
    self.armEmpty = False
    self.volume.append( [self.c, self.r-1] ) # grasping an object now - volume of the arm is larger
    self.movable = self.movable and obj.movable

    self.infill_color = MOVABLE_COLORS[0] if self.movable else IMMOVABLE_COLORS[0]  
    self.color = self.infill_color if self.armEmpty else ARM_NOT_EMPTY_COLOR
    
  
  def ungrasp(self, obj):
    self.objectHeld = -1
    self.armEmpty = True
    self.volume = self.volume[0:1] # adjust the volume: no longer grasping an object
    self.movable = self.movable or not obj.movable

    self.infill_color = MOVABLE_COLORS[0] if self.movable else IMMOVABLE_COLORS[0]  
    self.color = self.infill_color if self.armEmpty else ARM_NOT_EMPTY_COLOR

  def draw(self, cells, canvas):
    grasp_buffer = 3 # 0 | 3 | 5
    finger_length = self.side + grasp_buffer 
    finger_width = 10
    gripper_length = 20
    if self.draw_fingers:
      gripper_width = self.side + 2 * self.block_buffer + finger_width
    else:
      gripper_width = self.side

    # stem_length = 300
    stem_width = 20

    x = self.x
    y = self.y - self.side / 2 - gripper_length / 2 - grasp_buffer + self.side + 2 * self.block_buffer
    finger_x = gripper_width / 2 - finger_width / 2

    self.robot = [
      canvas.create_rectangle(x - stem_width / 2., self.stemStart,
                                    x + stem_width / 2., y,
                                    fill=self.infill_color, outline='black', width=2),
      canvas.create_rectangle(x - gripper_width / 2., y - gripper_length / 2.,
                                    x + gripper_width / 2., y + gripper_length / 2.,
                                    fill=self.color, outline='black', width=2),
    ]
    if self.draw_fingers:
      self.robot += [
        canvas.create_rectangle(x + finger_x - finger_width / 2., y,
                                      x + finger_x + finger_width / 2., y + finger_length,
                                      fill=self.color, outline='black', width=2),
        canvas.create_rectangle(x - finger_x - finger_width / 2., y,
                                      x - finger_x + finger_width / 2., y + finger_length,
                                      fill=self.color, outline='black', width=2),
      ]