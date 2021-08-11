import copy
from termcolor import colored
import numpy as np
import pandas as pd 
import math
from sim.util.utils import ERROR, WARN, GOOD
# https://pandas.pydata.org/pandas-docs/stable/user_guide/boolean.html

class ActionRuleBased:
  def __init__(self, name, rules):
    self.name = name # string
    self.rules = rules  # a list of rules


class EvalPredicate:
  def __init__(self, predSpec, precondOrEffect):
    self.type = precondOrEffect
    self.predType = predSpec[0]

    if self.type == 'precond':
      if self.predType == 'fromPred':
        self.obj = predSpec[1]
        self.pred = predSpec[2]
        self.val = predSpec[3]
      elif self.predType == 'fromFunc':
        self.func = predSpec[1]
        self.val = predSpec[2]
      elif self.predType == 'fromParam':
        self.obj = predSpec[1]
        self.pred = predSpec[2]
        self.param_val = predSpec[3]
      else:
        ERROR("ERROR: wrong predType for precond predicate")

    elif self.type == 'effect':
      self.obj = predSpec[1]
      self.pred = predSpec[2]
      if self.predType == 'fromPred':
        self.otherObj = predSpec[3]
        self.otherPred = predSpec[4]
      elif self.predType == 'fromVal':
        self.val = predSpec[3]
      elif self.predType == 'fromParam':
        self.param_val = predSpec[3]
      else:
        ERROR("ERROR: wrong predType for effect predicate")

  def __repr__(self):
    res = self.type + ", " + self.predType + ", "
    if self.type == 'precond':
      if self.predType == 'fromPred':
        res += self.obj + "." + self.pred + " = " + str(self.val)
      elif self.predType == 'fromParam':
        res += self.obj + "." + self.pred + " = " + self.param_val
    elif self.type == 'effect':
      res += self.obj + "." + self.pred
      if self.predType == 'fromPred':
        res += " = " + self.otherObj + "." + self.otherPred
      elif self.predType == 'fromVal':
        res += " = " + str(self.val)
      elif self.predType == 'fromParam':
        res += " = " + self.param_val 
    return res

  def apply(self, param, hyp):
    # return predicate name and value
    
    if self.type == "effect":
      predName = str(param[self.obj]) + "." + self.pred
      if self.predType == 'fromPred':
        otherPredName = str(param[self.otherObj]) + "." + self.otherPred
        value = hyp[ otherPredName ]
      
      elif self.predType == "fromVal":
        value = self.val
        
      elif self.predType == "fromParam":
        value = param[ self.param_val ]

      return (predName, value)

    else:
      ERROR("ERROR: calling apply of precond predicate")
  
    
  def isActivated(self, param, hyp):
    # param is a dict
    # hyp is a pd.Series
    if self.type == "precond":
      if self.predType == 'fromPred':
        predName = str(param[self.obj]) + "." + self.pred
        if hyp[predName] == self.val:
          return True
        return False
      elif self.predType == "fromFunc":
        if self.func(param, hyp) == self.val:
          return True
        return False
      elif self.predType == "fromParam":
        predName = str(param[self.obj]) + "." + self.pred
        if hyp[predName] == param[self.param_val]:
          return True
        return False

    else:
      ERROR("ERROR: calling eval of effect predicate")


  def isSufficient(self, param, hyp):
    # param is a dict
    # hyp is a pd.Series
    if self.type == "precond":

      if self.predType == 'fromPred':
        predName = str(param[self.obj]) + "." + self.pred
        if pd.isnull( hyp[predName] ):
          return (False, [self.name(param)] )
        return (True, [])

      if self.predType == 'fromParam':
        predName = str(param[self.obj]) + "." + self.pred
        if pd.isnull( hyp[predName] ):
          return (False, [self.name(param) ] )
        return (True, [])

      elif self.predType == "fromFunc":
        return self.func(param, hyp, True)

    else:
      ERROR("ERROR: calling isSufficient of effect predicate")
  

  def name(self, param):
    if self.type == "precond":
      if self.predType == 'fromPred' or self.predType == 'fromParam':
        return str(param[self.obj]) + "." + self.pred
    ERROR("ERROR: attempting to get name of non-precond predicate: " + self.__repr__())
    return None




class Rule:
  def __init__(self, preconds, effects):
    self.precondPreds = []
    for precond in preconds:
      self.precondPreds += [ EvalPredicate( precond, 'precond' ) ]

    self.effectPreds = []
    for effect in effects:
      self.effectPreds += [ EvalPredicate( effect, 'effect' ) ]

  def isActivated(self, param, hyp, verbose = True):
    for pred in self.precondPreds:
      if not pred.isActivated(param, hyp):
        if verbose:
          print("\tNOT ACTIVATED BC: " + pred.__repr__())
        return False
    return True

  def apply(self, param, hyp):
    changes = []
    for pred in self.effectPreds:
      changes += [ pred.apply(param, hyp) ]
    return changes


class StateEstimator:
  def __init__(self, bool_pred_names, cat_pred_names, verbose = True, runEstimator = True):
    self.run = runEstimator
    self.bool_preds = bool_pred_names
    self.cat_preds = cat_pred_names
    self.preds = self.bool_preds + self.cat_preds

    self.hyp = pd.DataFrame(columns = self.preds)
    self.addEmptyRow()
    self.verbose = verbose
    

  def addEmptyRow(self):
    self.hyp = self.hyp.append({}, ignore_index=True)

  def numHyp(self):
    return self.hyp.shape[0]

  def observe(self, observations, forceObserve=False):
    if not self.run:
      if not forceObserve:
        return
    # observations is a dictionary
    toBeRemoved = []
    for index, row in self.hyp.iterrows():
      for pred in observations:
        # case 1: value not inited; just init it then
        if pd.isnull(row[pred]):
          self.hyp[pred].iat[index] = observations[pred]
          if pred in self.bool_preds: # count
            self.hyp[pred].iat[index] = observations[pred]
        # case 2: value inited, but not the same; throw an error, should remove this row
        elif row[pred] != observations[pred]:
          if self.verbose:
            WARN("OBSERVING MISMATCH in hypothesis %i: predicate %s didn't match observations"%(index,pred))
          toBeRemoved += [index]
          break

    # remove some hypothesis
    self.hyp.drop(toBeRemoved, inplace=True)
    self.hyp.reset_index(drop=True, inplace=True)

    # we want to have at least 1 hypothesis
    if self.numHyp() == 0:
      ERROR("------------------------------------------------------------------")
      ERROR("No hypothesis describes the observations - the model is incomplete!")
      ERROR("------------------------------------------------------------------")
      self.addEmptyRow()

  def applyAction(self, action, param):
    if not self.run:
      return
    insufficient = []
    # -----------------------------------------
    # FIRST: find rows with an insufficient hypothesis
    for index, row in self.hyp.iterrows():
      missing = []
      for rule in action.rules:
        for pred in rule.precondPreds:
          (isSuff, insuffPreds) = pred.isSufficient(param, row)
          if not isSuff:
            for inPred in insuffPreds:
              if inPred in self.bool_preds:
                missing += [ inPred ]
              else:
                ERROR("ERROR: a categorial predicate %s is necessary but insufficient for the action %s" %(inPred, action.name))

      if len(missing) > 0:
        insufficient += [(index, np.unique(missing) )]  

    # -----------------------------------------
    # SECOND: add more hypothesi
    toBeRemoved = []
    for (index, missing) in insufficient:
      if self.verbose:
        WARN("For hypothesis %i adding %s preds" %(index, str(missing)))
      # all predicates in missing are bool
      hypCopy = copy.deepcopy(self.hyp.iloc[index])

      for m in missing:
        hypCopy[m] = False
      self.hyp = self.hyp.append(hypCopy, ignore_index=True)
      # one by one add the hypothesi by iteratively changing boolean values of the hyp in a binary fashion
      for i in range(1,2**len(missing)):
        temp = 0
        while hypCopy[ missing[temp] ]:
          hypCopy[ missing[temp] ] = False
          temp += 1
        hypCopy[ missing[temp] ] = True
        self.hyp = self.hyp.append(hypCopy, ignore_index=True)
      toBeRemoved += [index]
    # drop the original hypothesi
    self.hyp.drop(toBeRemoved, inplace=True)
    self.hyp.reset_index(drop=True,inplace=True)

    # -----------------------------------------
    # THIRD: evaluate which rules are processed, process immediately
    for index, row in self.hyp.iterrows():
      activatedRules = []
      for i in range(len(action.rules)):
        if self.verbose:
          print("RULE " + str(i))
        if action.rules[i].isActivated(param, row, self.verbose):
          if self.verbose:
            GOOD("\tRULE ACTIVATED")
          activatedRules += [i]
      
      # activate the rules
      for i in activatedRules:
        changes = action.rules[i].apply(param, row)
        for (pred, value) in changes:
          self.hyp[pred].iat[index] = value

  def hypothesisRemoval(self):
    if not self.run:
      return
    while self.hypothesisRemovalSingleIteration() != 0:
      continue

  def hypothesisRemovalSingleIteration(self):
    toBeRemoved = []
    toBeAdded = pd.DataFrame(columns = self.preds)
    tempHyp = copy.deepcopy(self.hyp)

    # fix NA into xorable NA
    self.hyp.fillna(pd.NA, inplace = True)

    for index1, row1 in self.hyp.iterrows():
      for index2, row2 in self.hyp.iterrows():
        if index1 < index2: # and row1[self.bool_preds].isna().sum() == row2[self.bool_preds].isna().sum() :
          xored = pd.array( np.array(row1[self.bool_preds])^np.array(row2[self.bool_preds]), dtype='boolean')
          if pd.isnull( row1[self.bool_preds] ).sum() == pd.isnull( row2[self.bool_preds] ).sum():
            # number of nulls in the xor is the same as in the original
            # hence the two rows have identical values in identical rows
            if pd.Series(xored).sum() == 1:
              # difference is only in one element - that means we can remove these rows and this element
              toBeRemoved += [index1, index2]
              xored = xored.fillna(False)
              xored = ~xored
              
              addMe = row1[self.bool_preds][xored]

              for pred in self.cat_preds:
                addMe[pred] = row1[pred]
              
              for pred in self.bool_preds:
                if pred not in addMe:
                  addMe[pred] = math.nan
              
              toBeAdded = toBeAdded.append(addMe)

    # remove duplicates
    toBeAdded.drop_duplicates(inplace=True)
                      
    # remove old hypothsis
    toBeRemoved = np.unique( np.array(toBeRemoved) )
    self.hyp.drop(toBeRemoved, inplace=True)
    if len(toBeRemoved) != 0 and self.verbose:
      WARN("Removed %i hypotheses, added %i!"%(len(toBeRemoved), len(toBeAdded)))

    # combine
    self.hyp = self.hyp.append(toBeAdded)
    self.hyp.reset_index(drop=True,inplace=True)
    return len(toBeRemoved)


  def findCore(self):
    core_preds = []
    for col in self.hyp.columns:
      if (self.hyp[col][0] == self.hyp[col]).all():
        core_preds += [col]
    return core_preds

  def getCore(self):
    preds = self.findCore()
    values = list(self.hyp.iloc[0][ preds ])
    return [ (pred, value) for pred,value in zip(preds,values) ]
  
  def __repr__(self):
    if not self.run:
      return ""
    self.findCore()
    if self.verbose:
      return "Estimator with %i hypotheses, and the core of %s\n%s" % (\
              self.numHyp(), self.findCore(), self.hyp.__repr__() )
    else:
      return "\n"+self.hyp.__repr__()
      

                    






        
        

      
    





