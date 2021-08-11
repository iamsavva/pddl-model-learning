try:
  from tkinter import Tk, Canvas, Toplevel
except ImportError:
  from Tkinter import Tk, Canvas, Toplevel

import colorsys

import sys
import copy
from sim.util.utils import user_input, ERROR, WARN, GOOD
import numpy as np
from sim.viewer.model_viewer import ModelViewer
from sim.state_estimator import StateEstimator
from sim.viewer.Object import MOVABLE_COLORS, IMMOVABLE_COLORS, TEXT_COLOR, BLACK, BACKGROUND, TABLE_BACKGROUND, TABLE_COLOR, ARM_NOT_EMPTY_COLOR

from sim.ilp import ActionLearner
from sim.specifications.simple.simple_correct_action_model import KinMovePred, KinPickPred, SafePred, UnderPred


# ------------------------------------------
simpleComplete = True
simpleIncomplete = False
slipperyComplete = False
# ------------------------------------------
runEstimator = False


if np.array( [simpleComplete, simpleIncomplete, slipperyComplete] ).sum() != 1:
  ERROR("MUST SPECIFY ONE FILE INPUT SOURCE")
  sys.exit()
# ------------------------------------------
# LOADING SIMPLE MODEL: 
# ------------------------------------------
if simpleComplete or simpleIncomplete:
  # grouth truth action model:
  from sim.specifications.simple.simple_correct_action_model import actions as gt_actions
  # state estimator action model:
  if simpleComplete:
    from sim.specifications.simple.simple_correct_action_model import actions as se_actions
  if simpleIncomplete:
    from sim.specifications.simple.simple_incomplete_action_model import actions as se_actions
  # initial conditions:
  from sim.specifications.simple.simple_initial_conditions import initial_conditions
  from sim.specifications.simple.simple_observations import observed_predicates
  from sim.specifications.simple.simple_first_observations import observed_predicates_first
# ------------------------------------------

# ------------------------------------------
# LOADING SLIPPERY MODEL: 
# ------------------------------------------
if slipperyComplete:
  # grouth truth action model:
  from sim.specifications.slippery.slippery_correct_action_model import actions as gt_actions
  # state estimator action model:
  from sim.specifications.slippery.slippery_correct_action_model import actions as se_actions
  # initial conditions:
  from sim.specifications.slippery.slippery_initial_conditions import initial_conditions
  from sim.specifications.slippery.slippery_observations import observed_predicates
  from sim.specifications.slippery.slippery_first_observations import observed_predicates_first
# ------------------------------------------


class Environment:
  def __init__(self, rows, cols, width=500, height=250, side=40,
                 block_buffer=3, title='Grid', background_color='tan', draw_fingers=False):
    assert (rows <= 3)
    assert (cols <= 9)

    # ------------------
    # initializing tk inter
    tk = Tk()
    tk.withdraw()
    top = Toplevel(tk)
    top.wm_title('Grid')
    top.protocol('WM_DELETE_WINDOW', top.destroy)

    # ------------------
    # canvas parameters
    self.width = width # window width
    self.height = height # window height
    self.rows = rows # number of row in the environment
    self.cols = cols # number of cols in the environment

    self.side = side # size of an object 
    self.block_buffer = block_buffer # buffer between two blocks - discrete world, remember
    
    # ------------------
    # start the canvas
    if runEstimator:
      self.canvas = Canvas(top, width=self.width, height=2*self.height, background=BACKGROUND)
    else:
      self.canvas = Canvas(top, width=self.width, height=self.height, background=BACKGROUND)
    self.canvas.pack()
    self.cells = {}
    self.environment = []

    # ------------------
    # process the input files
    ( bool_preds, cat_preds, init_conds, observed_preds, observed_preds_first, num_objects ) = self.processInputs()
    self.gtActions = gt_actions
    self.seActions = se_actions
    self.observedPreds = observed_preds

    # ------------------
    # start the state estimators
    self.gt = StateEstimator(bool_preds, cat_preds, False)
    self.gt.observe(init_conds)

    self.se = StateEstimator(bool_preds, cat_preds, True, runEstimator)
    self.se.observe( self.gtObserver(observed_preds_first), not runEstimator ) 

    # ------------------
    # start the model viewer + draw initial conditions
    slippery = slipperyComplete
    self.gtViewer = ModelViewer(self.rows, self.cols, num_objects, 0, self.width, self.height, self.side, self.block_buffer, slippery)
    if runEstimator:
      self.seViewer = ModelViewer(self.rows, self.cols, num_objects, self.height, self.width, self.height, self.side, self.block_buffer, slippery)

    # ------------------
    # viewing
    self.draw()

    # self.aaa = ActionLearner()
    # self.aaa.translateExample( self.gtObserver() )
    self.actionLearners = { 'move': ActionLearner( "move", [KinMovePred, UnderPred] ), 
                            'pick': ActionLearner( "pick", [KinPickPred] ), 
                            'place': ActionLearner( "place", [SafePred] ) }

  def processInputs(self):
    bool_preds = []
    cat_preds = []
    init_conds = {}
    observed_preds = []
    observed_preds_first = []
    diff_objects = []
    for pred in initial_conditions:
      if pred[0] != -1 and pred[0] not in diff_objects:
        diff_objects += [pred[0]]
      pred_name = str(pred[0]) + "." + pred[1]
      if pred[2] == 'bool':
        bool_preds += [pred_name]
      elif pred[2] == 'cat':
        cat_preds += [pred_name]
      init_conds[pred_name] = pred[3]

    for pred in observed_predicates:
      pred_name = str(pred[0]) + "." + pred[1]
      observed_preds += [pred_name]
    for pred in observed_predicates_first:
      pred_name = str(pred[0]) + "." + pred[1]
      observed_preds_first += [pred_name]

    return ( bool_preds, cat_preds, init_conds, observed_preds, observed_preds_first, len(diff_objects) )

  def gtObserver(self, preds = []):
    obs = {}
    if len(preds) == 0:
      for pred in self.observedPreds:
        obs[pred] = self.gt.hyp[pred][0]
    else:
      for pred in preds:
        obs[pred] = self.gt.hyp[pred][0]
    return obs


# -----------------------------------
# manual testing
  def inTestMode(self):

    prevState = self.gtObserver()
    newState = None

    while(True):
      cmd = user_input("CMD: ")
      cmd_valid = True

      if cmd == "move":
        cmd2 = user_input("q1q2:")
        if len(cmd2) == 4:
          q1 = ( int(cmd2[0]), int(cmd2[1]) )
          q2 = ( int(cmd2[2]), int(cmd2[3]) )
          param = {'arm':-1, 'q1':q1, 'q2':q2}
          learnerParam = {'arm':-1, 'q1':q1, 'q2':q2}
          learnerParamTypes = {'arm':'obj', 'q1':'conf', 'q2':'conf'}

          self.gt.applyAction( self.gtActions['move'], param )
          self.se.applyAction( self.seActions['move'], param )
        else:
          print("ERROR")
          cmd_valid = False

      elif cmd == "pick":
        cmd2 = user_input("bpq: ")
        if len(cmd2) == 5:
          b = int(cmd2[0])
          p = ( int(cmd2[1]), int(cmd2[2]) )
          q = ( int(cmd2[3]), int(cmd2[4]) )
          param = {'arm':-1, 'b':b, 'p':p, 'q':q}
          learnerParam = {'arm':-1, 'b':b, 'p':p, 'q':q}
          learnerParamTypes = {'arm':'obj', 'b':'obj', 'p':'pos', 'q':'conf'}
          self.gt.applyAction( self.gtActions['pick'], param )
          self.se.applyAction( self.seActions['pick'], param )
        else:
          print("ERROR")
          cmd_valid = False

      elif cmd == "place":
        cmd2 = user_input("bpq: ")
        if len(cmd2) == 5:
          b = int(cmd2[0])
          p = ( int(cmd2[1]), int(cmd2[2]) )
          q = ( int(cmd2[3]), int(cmd2[4]) )
          param = {'arm':-1, 'b':b, 'p':p, 'q':q}
          learnerParam = {'arm':-1, 'b':b, 'p':p, 'q':q}
          learnerParamTypes = {'arm':'obj', 'b':'obj', 'p':'pos', 'q':'conf'}

          self.gt.applyAction( self.gtActions['place'], param )
          self.se.applyAction( self.seActions['place'], param )
        else:
          print("ERROR")
          cmd_valid = False

      elif cmd == "done":
        print("Exitting")
        sys.exit()
      else:
        print("\tCommand invalid")
        cmd_valid = False
      
      if cmd_valid:
        newState = self.gtObserver()
        self.actionLearners[cmd].addExample( (prevState, learnerParam, learnerParamTypes, newState) )
        # self.aaa.addExample( (prevState, param, newState) )
        prevState = self.gtObserver()

        # GOOD(self.gt)
        if self.gt.numHyp() > 1:
          ERROR("--------------------------------------------------------")
          ERROR("GROUND TRUTH has more than one hypothesis, this is wrong")
          ERROR("--------------------------------------------------------")

        
        if runEstimator:
          print("\nafter action")
          print(self.se)

          self.se.observe( self.gtObserver() ) 
          print("\nafter observation")
          print(self.se)

          self.se.hypothesisRemoval()
          print("\nafter hypremoval")
          print(self.se)

        self.draw()

# -----------------------------------
# drawing

  def draw(self):
    self.clear()
    self.gtViewer.updateViewerCorePreds( self.gt.getCore() )
    if runEstimator:
      self.seViewer.updateViewerCorePreds( self.se.getCore() )
      self.drawModel(self.seViewer)
    self.drawModel(self.gtViewer)
    self.drawOther()

  def clear(self):
    """
    clear the canvas
    """
    self.canvas.delete('all')

  def drawModel(self, model):
    model.drawBackground(self.canvas, self.environment)
    model.drawObjects(self.canvas, self.cells)
    model.arm.draw(self.cells, self.canvas)
    model.drawNumbers(self.canvas)

  def drawOther(self):
    self.environment.append( self.canvas.create_line(0, self.height, self.width + 100, self.height,
                                      fill='black',  width=2), )
    self.environment.append( self.canvas.create_text(self.width-40, 10, text="world view", fill=TEXT_COLOR) )
    self.environment.append( self.canvas.create_text(self.width-40, self.height+10, text="model view", fill=TEXT_COLOR) )











      
      
      

  