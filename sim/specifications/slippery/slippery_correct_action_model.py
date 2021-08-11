from sim.state_estimator import Rule, ActionRuleBased
from termcolor import colored
import pandas as pd 
from sim.util.action_model_util import negate, sum

# for predicates, specify: 
# cause actions are parametrized, remember

# preconditions: 
#   fromPred
#   fromFunc
#   fromParam

# effects:
#   fromVal
#   fromPred
#   fromParam

# -----------------------------

def KinPick(param, hyp, sufficiencyCheck = False):
  if sufficiencyCheck:
    return (True, [])
  else:
    if sum( param['q'], negate(param['p']) ) == (0,1):
      return True
    return False

# rule 1: if arm is empty and kinematically possible to pick up an object - pick it up; ph and for slippery, the object can't be slippery either
pick_rule1_precond = [ ( 'fromPred', 'arm', 'armEmpty', True ), ( 'fromPred', 'b', 'slippery', False ), ( 'fromParam', 'arm', 'pos', 'q' ), ( 'fromParam', 'b', 'pos', 'p' ), ('fromFunc', KinPick, True ) ]
pick_rule1_effect = [ ('fromVal', 'arm', 'armEmpty', False), ('fromParam','arm', 'objectHeld', 'b') ]

# rule 2: if the picked up object was not movable - the arm is no longer movable either
pick_rule2_precond = [ ( 'fromPred', 'arm', 'armEmpty', True ), ( 'fromPred', 'b', 'slippery', False ), ( 'fromParam', 'arm', 'pos', 'q' ), ( 'fromParam', 'b', 'pos', 'p' ), ('fromFunc', KinPick, True ), ('fromPred', 'b', 'movable', False ) ]
pick_rule2_effect = [ ('fromVal', 'arm', 'movable', False) ]

pick_rule1 = Rule( pick_rule1_precond, pick_rule1_effect )
pick_rule2 = Rule( pick_rule2_precond, pick_rule2_effect )
pick_actionrb = ActionRuleBased( "pick", [pick_rule1, pick_rule2])


# -----------------------------
# there are two move actions: relational and absolute. relational is parametrized by direction. absolute is parametrized by two values.

def KinMove(param, hyp, sufficiencyCheck = False):
  # there are no obstacles in the way
  if sufficiencyCheck:
    suff = True
    insuffPreds = []
    for pred in hyp.index:
      if 'pos' in pred:
        if pd.isnull( hyp[pred] ):
          suff = False
          insuffPreds += [pred]

    # sort of a strong requirement too
    for pred in [ str(param['arm']) + ".armEmpty", str(param['arm']) + ".objectHeld" ]:
      if pd.isnull(hyp[pred]):
        suff = False
        insuffPreds += [pred]
    return (suff, insuffPreds)
  
  # checking translatory kinematic feasibility
  if not ( sum( param['q2'], negate(param['q1']) ) in ( (0,1), (0,-1), (1,0), (-1,0) ) ):
    return False

  desPos = [param['q2']]
  if not hyp[ str(param['arm']) + ".armEmpty" ]:
    desPos += [ (param['q2'][0], param['q2'][1]-1) ]
    param['obj_held'] = hyp[ str(param['arm']) + ".objectHeld" ]
    param['obj_held_p2'] = (param['q2'][0], param['q2'][1]-1)

  # no collisions
  for pred in hyp.index: 
    if 'pos' in pred and pred != str(param['arm']) + ".pos":
      if hyp[ str(param['arm']) + ".armEmpty" ] or pred != str( hyp[ str(param['arm']) + ".objectHeld" ] ) + ".pos": # uhhm shady
        for pos in desPos:
          if hyp[pred] == pos:
            return False

  # within walls
  for pos in desPos:
    if not ( 0 <= pos[0] < 9 and 0 <= pos[1] <= 3 ):
      return False

  return True

# rule 1: if arm is movable and collision free in the direction of motion - move the arm
move_rule1_precond = [ ( 'fromPred', 'arm', 'movable', True), ( 'fromParam', 'arm', 'pos', 'q1' ), ('fromFunc', KinMove, True) ]
move_rule1_effect = [ ('fromParam', 'arm', 'pos', 'q2') ]

# rule 2: if arm is movable and holding an object - move the object as well
move_rule2_precond = [ ( 'fromPred', 'arm', 'movable', True), ( 'fromParam', 'arm', 'pos', 'q1' ), ('fromFunc', KinMove, True), ( 'fromPred', 'arm', 'armEmpty', False) ]
move_rule2_effect = [ ('fromParam', 'obj_held', 'pos', 'obj_held_p2') ] 

move_rule1 = Rule( move_rule1_precond, move_rule1_effect )
move_rule2 = Rule( move_rule2_precond, move_rule2_effect )
move_actionrb = ActionRuleBased( "move_rel", [move_rule1, move_rule2])
    

# -----------------------------

def Safe(param, hyp, sufficiencyCheck = False):
  # there is an obstacle underneath the held object
  if sufficiencyCheck:
    suff = True
    insuffPreds = []
    # all positions should be identified
    for pred in hyp.index:
      if 'pos' in pred:
        if pd.isnull( hyp[pred] ):
          suff = False
          insuffPreds += [pred]
    return (suff, insuffPreds)

  
  # within bounds
  if not ( 0 <= param['p'][0] < 9 ):
    return False
  # on the floor
  if param['p'][1] == 0:
    return True
  # there exists an object such that i am on top of it
  objExists = False
  for pred in hyp.index:
    if 'pos' in pred:
      # check for a collision - to be honest, that's useless
      if hyp[pred] == param['p'] and int(pred[0]) != param['b']:
        return False
      if hyp[pred][0] == param['p'][0] and  hyp[pred][1] == param['p'][1] - 1:
        objExists = True
  if objExists:
    return True

  return False


# rule 1: if arm is not empty and there is an object under neath - place it
place_rule1_precond = [ ( 'fromPred', 'arm', 'armEmpty', False), ('fromParam', 'arm', 'objectHeld', 'b'), ( 'fromParam', 'arm', 'pos', 'q' ), ( 'fromParam', 'b', 'pos', 'p' ), ('fromFunc', Safe, True) ]
place_rule1_effect = [ ( 'fromVal', 'arm', 'armEmpty', True), ('fromVal', 'arm', 'objectHeld', -1) ]

# rule 2: if the held object was immovable - make the arm movable (reconsider this rule for the future)
place_rule2_precond = [ ( 'fromPred', 'arm', 'armEmpty', False), ('fromParam', 'arm', 'objectHeld', 'b'), ( 'fromParam', 'arm', 'pos', 'q' ), ( 'fromParam', 'b', 'pos', 'p' ), ('fromFunc', Safe, True), ( 'fromPred', 'b', 'movable', False) ]
place_rule2_effect = [ ('fromVal', 'arm', 'movable', True) ]

place_rule1 = Rule( place_rule1_precond, place_rule1_effect )
place_rule2 = Rule( place_rule2_precond, place_rule2_effect )
place_actionrb = ActionRuleBased( "place", [place_rule1, place_rule2])

actions = {'move': move_actionrb, 'pick':pick_actionrb, 'place': place_actionrb }