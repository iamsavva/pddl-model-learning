from sim.viewer.Object import Object, Square, Arm
import pandas as pd
from sim.viewer.Object import MOVABLE_COLORS, IMMOVABLE_COLORS, TEXT_COLOR, BLACK, BACKGROUND, TABLE_BACKGROUND, TABLE_COLOR, ARM_NOT_EMPTY_COLOR
HYPOTHESIZED_MOVABLE = '#C3DFE0'
HYPOTHESIZED_IMMOVABLE = '#843B62'

import sys

class ModelViewer:
  def __init__(self, rows, cols, num_objects, offset, width=500, height=250, side=40, block_buffer=3, slippery = False):

    # ----------------------------
    # -----------  drawing related
    assert (rows <= 3)
    assert (cols <= 9)

    self.rows = rows
    self.cols = cols

    self.width = width # window width
    self.height = height # window height
    self.side = side # size of an object 
    self.block_buffer = block_buffer # buffer between two blocks - discrete world, remember
    self.table_width = self.cols * (self.side + 2 * self.block_buffer) + 2 * self.block_buffer
    self.table_height = self.rows * (self.side + 2 * self.block_buffer) + 2 * self.block_buffer
    self.border_buffer = 50 # buffer to the borders
    self.table_thickness = 20 
    self.pose_radius = 2

    self.table_x1 = self.width/2 - self.table_width/2 # starting x location on the table
    self.table_y1 = offset + self.height - self.table_height - self.border_buffer  # starting y location on the table

    self.slippery = slippery

    self.objects = []
    self.num_objects = num_objects
    for i in range(self.num_objects):
      self.objects.append( Square( [i,0], self.transform_cr([i,0]), i, side, 'grey' ) )
    
    self.arm = Arm( [0,2], self.transform_cr([0,2]), side, False, block_buffer, offset )

    # -----------  drawing related
    # ----------------------------


  def resetViewer(self):
    self.arm.armEmpty = None
    self.arm.objectHeld = None
    self.arm.movable = None
    self.arm.c = -1
    self.arm.r = 3
    self.arm.infill_color = 'grey'
    self.arm.color = 'grey'
    for obj in self.objects:
      # obj.isHeld = None
      obj.movable = None
      obj.r = -1
      obj.color = 'grey'
      obj.slippery = None

  def updateViewerCorePreds(self, core):
    self.resetViewer()

    for (predName, value) in core:
      sep = predName.find('.')
      obj = int(predName[:sep])
      pred = predName[sep+1:]

      if obj == -1:
        if pred == 'armEmpty':
          self.arm.armEmpty = value
        elif pred == 'objectHeld':
          self.arm.objectHeld = value
        elif pred == 'pos':
          (self.arm.c, self.arm.r) = value
        elif pred == 'movable':
          self.arm.movable = value
      else:
        # if pred == 'isHeld':
          # self.objects[ obj ].isHeld = value
        if pred == 'movable':
          self.objects[ obj ].movable = value
        elif pred == 'slippery':
          self.objects[ obj ].slippery = value
        elif pred == 'pos':
          (self.objects[obj].c, self.objects[obj].r) = value

    # set colors
    if not pd.isnull(self.arm.movable):
      self.arm.infill_color = MOVABLE_COLORS[0] if self.arm.movable else IMMOVABLE_COLORS[0]  
    if not pd.isnull(self.arm.armEmpty):
      self.arm.color = self.arm.infill_color if self.arm.armEmpty else ARM_NOT_EMPTY_COLOR

    for obj in self.objects:
      if not pd.isnull(obj.movable):
        obj.color = MOVABLE_COLORS[0] if obj.movable else IMMOVABLE_COLORS[0]

    # move places; note that we are doing this regardless of whether we acquired positions - 
    # - because c and r are always inited, just sometimes reset
    self.arm.move( [self.arm.c, self.arm.r], self.transform_cr( [self.arm.c, self.arm.r] ) )
    for obj in self.objects:
      obj.move( [obj.c,obj.r], self.transform_cr( [obj.c,obj.r] ) )
        

# -----------------------------------
# transformations from row//column to x/y

  def transform_r(self, r):
    """
    tranform row number into y location
    """
    return self.table_y1 + (self.rows-r-1) * (self.side + 2 * self.block_buffer) + 2 * self.block_buffer + self.side / 2

  def transform_c(self, c):
    """
    tranform column number into x location
    """
    return self.table_x1 + c * (self.side + 2 * self.block_buffer) + 2 * self.block_buffer + self.side / 2

  def transform_cr(self, cr):
    """
    tranform a [col, row] array into [x,y]
    """
    return [ self.transform_c(cr[0]), self.transform_r(cr[1]) ]



# -----------------------------------
# drawing

  def drawObjects(self, canvas, cells):
    """
    draw all the objects in the environment
    """
    for i in range(self.num_objects):
      self.objects[i].draw(cells, canvas, self.slippery, self.objects[i].slippery)

  # def drawBackground(self, table_color='lightgrey', bin_color='grey'):
  def drawBackground(self, canvas, environment, table_color=TABLE_BACKGROUND, bin_color=TABLE_COLOR):
    """
    draw the background of the ennvironment
    """
    environment = [
        canvas.create_rectangle(self.table_x1, self.table_y1,
                                      self.table_x1 + self.table_width, self.table_y1 + self.table_height,
                                      fill=table_color, outline='black', width=2),
        canvas.create_rectangle(self.table_x1 - self.table_thickness, self.table_y1,
                                      self.table_x1, self.table_y1 + self.table_height,
                                      fill=bin_color, outline='black', width=2),
        canvas.create_rectangle(self.table_x1 + self.table_width, self.table_y1,
                                      self.table_x1 + self.table_width + self.table_thickness, self.table_y1 + self.table_height,
                                      fill=bin_color, outline='black', width=2),
        canvas.create_rectangle(self.table_x1, self.table_y1 + self.table_height,
                                      self.table_x1 + self.table_width, self.table_y1 + self.table_height + self.table_thickness,
                                      fill=bin_color, outline='black', width=2),
        canvas.create_rectangle(self.table_x1 - self.table_thickness, self.table_y1 + self.table_height,
                                      self.table_x1 + self.table_width + self.table_thickness,
                                      self.table_y1 + self.table_height + self.table_thickness,
                                      fill=bin_color, outline='black', width=2),
    ]

    for r in range(self.rows):
      for c in range(self.cols):
        x = self.transform_c(c)
        y = self.transform_r(r)
        environment.append(canvas.create_oval(x - self.pose_radius, y - self.pose_radius,
                                                        x + self.pose_radius, y + self.pose_radius, fill='black', width=0))

  def drawNumbers(self, canvas):
    for r in range(self.rows):
      for c in range(self.cols):
        x = self.transform_c(c)
        y = self.transform_r(r)
        canvas.create_text(x, y-10, text=str(c)+""+str(r), fill="black")

  def clear(self):
    """
    clear the canvas
    """
    self.canvas.delete('all')