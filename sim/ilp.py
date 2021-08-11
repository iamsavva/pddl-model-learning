import copy
from termcolor import colored
import numpy as np
import pandas as pd 
import math
from sim.util.utils import ERROR, WARN, GOOD, INFO

class ActionLearner:
  def __init__(self, name, extraPreds):
    self.name = name # action name
    self.extraPreds = extraPreds
    self.rules = []

    self.exampleTuples = [] # tuples (s, a, s'); 
    self.exampleClauses = []
    
  def addExtraPreds(self, state, actionParam):
    # state here is a dictionary
    for functionPred in self.extraPreds:
      preds = functionPred(actionParam, state)
      for (predName, value) in preds:
        state[predName] = value
    return state

  def maintainRelevantPreds(self, state, actionParam):
    # TO DO: this is hacky, put more thought
    # relevant predicates are: all predicats that are somehow conncted through a graph to our objects
    relevantObjs = []
    relevantPredInds = []
    relevantPreds = []
    i = 0
    needAnotherRun = False

    for predName in actionParam:
      relevantObjs += [actionParam[predName]]

    while i < len(state):
      if i not in relevantPredInds:
        objs = state[i].getAllObjs()
        # check if it's in
        isIn = False
        for obj in objs:
          if obj in relevantObjs:
            isIn = True
            break
        if isIn:
          relevantPredInds += [i]
          for obj in objs:
            if obj not in relevantObjs:
              relevantObjs += [obj]
              needAnotherRun = True
      i+=1
      if i == len(state) and needAnotherRun:
        i = 0
        needAnotherRun = False
    for j in relevantPredInds:
      relevantPreds += [ state[j] ]

    return relevantPreds

  def translateExample( self, state, actionParam ):
    # these are actually literals
    preds = []
    for predName in state:
      sep = predName.find('.')
      if sep != -1:
        objName = int(predName[:sep])
      pred = predName[sep+1:]
      value = state[predName]

      if pred in ('armEmpty', 'movable'):
        # arity 1 predicates
        term = Term( termType = 'obj', value = objName ) # generate the term
        preds += [ Literal( positive = value, name = pred, arity = 1, terms = [ term ] ) ] 
      elif pred == 'safe':
        # arity 1 predicate
        term = Term( termType = 'pos', value = actionParam['p'] ) # generate the term
        preds += [ Literal( positive = value, name = pred, arity = 1, terms = [ term ] ) ] 

      elif pred in ('pos', 'objectHeld', 'kinMove', 'kinPick', 'under'):
        # arity 2 predicates
        if pred == 'pos':
          if objName == -1:
            pred = 'conf'
          term1 = Term( termType = 'obj', value = objName ) 
          term2 = Term( termType = pred, value = value )
          preds += [ Literal( positive = True, name = pred, arity = 2, terms = [ term1, term2 ] ) ]  
        elif pred == 'objectHeld':
          term1 = Term( termType = 'obj', value = objName )
          if value == -1:
            term2 = Term( termType = 'obj', value = None )
          else:
            term2 = Term( termType = 'obj', value = value )
          preds += [ Literal( positive = True, name = pred, arity = 2, terms = [ term1, term2 ] ) ]  
        elif pred == 'kinMove':
          term1 = Term( termType = 'conf', value = actionParam['q1']) # generate the term
          term2 = Term( termType = 'conf', value = actionParam['q2']) # generate the term
          preds += [ Literal( positive = value, name = pred, arity = 2, terms = [ term1, term2 ] ) ]  
        elif pred == 'kinPick':
          term1 = Term( termType = 'conf', value = actionParam['q']) # generate the term
          term2 = Term( termType = 'pos', value = actionParam['p']) # generate the term
          preds += [ Literal( positive = value, name = pred, arity = 2, terms = [ term1, term2 ] ) ]  
        elif pred == 'under':
          # TO DO: current implementation of under is a hack
          term1 = Term( termType = 'conf', value = value[0]) # generate the term
          term2 = Term( termType = 'pos', value = value[1]) # generate the term
          preds += [ Literal( positive = True, name = pred, arity = 2, terms = [ term1, term2 ] ) ]  

    
    # for pred in preds:
      # print(pred)
    # print("----------")
    return preds

  def removeUnlessChanged(self, prevS, newS):
    res = []
    for pred in newS:
      isNew = True
      for oldPred in prevS:
        if pred.sameAs(oldPred):
          isNew = False
          break
      if isNew:
        res += [pred]
    return res

  def saveDataPoint(self, exampleTuple, exampleClause):
    self.exampleTuples += [exampleTuple]
    self.exampleClauses += [exampleClause]
    return len(self.exampleTuples)-1

  def findCompatibleRule( self, effectLiteral ):
    res = None
    for i, rule in enumerate(self.rules):
      for literal in rule.effects:
        if effectLiteral.isCompatibleWith( literal ):
          # type matched!
          if res == None:
            res = i
          elif res == i:
            ERROR( "SAME RULE, TWO PREDICATES, SAME TYPE: %s, %s\n%s" %( effectLiteral.name, str(effectLiteral.positive), rule.__repr__() ) )
          else:
            ERROR( "I HAVE TWO RULES WITH SAME LITERAL TYPE: %s, %s\n%s" %( effectLiteral.name, str(effectLiteral.positive), rule.__repr__() ) )
    return res

  def checkIfClauseIsCoveredByTheRule(self, clauseEffectLiteral, clause, ruleIndex):
    rule = self.rules[ruleIndex]
    # first, check the effects. Assumption is that clauses / rules have a single effect
    # rule literal is supposed to be more general than the clause literal
    if not rule.effects[0].isMoreGeneralThan( clauseEffectLiteral ):
      return False

    #next check the preconditions.
    # TO DO: when checking the match, i need to consider the predicates not individually, but as a group.
    for ruleLiteral in rule.preconds:
      existsMatchingPrecond = False
      for clauseLiteral in clause.preconds:
        if ruleLiteral.isCompatibleWith(clauseLiteral):
          if ruleLiteral.isMoreGeneralThan(clauseLiteral):
            if existsMatchingPrecond == True:
              # TO DO: fix this
              WARN( "RULE GENERALITY: MUST CONSIDER TOGETHER, NOT SEPARATELY" )
            existsMatchingPrecond = True
      if not existsMatchingPrecond:
        return False
      # if loop is over - we found a matching precondition, we're good
    
    return True
          
  def nextVarName(self, varName):
    if len(varName) == 1:
      if ord(varName) == 90:
        return 'A'
      else:
        return chr(ord(varName)+1)
    else:
      ERROR("NEXT VAR NAME BAD INPUT")
      return

    
  def generalizeRule( self, clauseEffectLiteral, clause, ruleIndex ):
    
    ruleVarRenaming = {}
    clauseVarRenaming = {}

    rule = self.rules[ruleIndex]
    varName = 'X'
    while varName in rule.listOfVars:
      varName = self.nextVarName(varName)

    # handle effects first
    ruleLiteral = rule.effects[0]
    
    if ruleLiteral.isCompatibleWith( clauseEffectLiteral ):
      # if rule's literal is more general - we dont care; is rule's literal is not more general, we need fixing!
      if not ruleLiteral.sameAs( clauseEffectLiteral ):
        t1 = ruleLiteral.terms
        t2 = clauseEffectLiteral.terms
        for i in range(ruleLiteral.arity):
          # not the same - replace
          if not t1[i].sameAs(t2[i]):
            if not( t1[i].value in ruleVarRenaming and t2[i].value in clauseVarRenaming ):
              if (t1[i].value in ruleVarRenaming and t2[i].value not in clauseVarRenaming) or \
                (t1[i].value not in ruleVarRenaming and t2[i].value in clauseVarRenaming):
                # error handling / unknown case
                ERROR("ONE VALUE IN VAR RENAMING, ANOTHER NOT %s %s %s %s %s %s" %(t1[i].__repr__(), t2[i].__repr__(), ruleLiteral.__repr__(), clauseLiteral.__repr__(), rule.__repr__(), clause.__repr__() ) )
              else:
                # introducing new variable
                ruleVarRenaming[ t1[i].value ] = varName
                clauseVarRenaming[ t2[i].value ] = varName
                varName = self.nextVarName(varName)
    else:
      ERROR( "INCOMPATIBLE EFFECTS IN GENERALIZATION\nCLAUSE %sRULE %s" %(clause, rule) )
      return

    # TO DO: so the issue here is the problem of predicate association.
    # association should be done based on relevance - action-object-predicate locality
    # cluster predicates by objects / parameters, then connect them
    # the hack i am about to implement should also work

    # TO DO: need to handle a case where clause length is smaller than the length of the rule
    # in other words, object locality, predicate irrelevance actually make things really difficult
    # some sort of persistance? aftr pick, predicate b persists?

    # TO DO: this is a hack

    ruleI = 0
    clauseI = 0
    toBeRemoved = []
    while ruleI < len(rule.preconds):
      if clauseI >= len(clause.preconds):
        ERROR("iteration of clause screw up")
        return
      ruleLiteral = rule.preconds[ruleI]
      clauseLiteral = clause.preconds[clauseI]
      # same type - great!
      if ruleLiteral.isSameType( clauseLiteral ):
        if ruleLiteral.isCompatibleWith( clauseLiteral ):
          if ruleLiteral.sameAs(clauseLiteral):
            # beautiful, this is good, they are the same, go on
            ruleI += 1
            clauseI += 1
          else:
            # i = 0
            t1 = ruleLiteral.terms
            t2 = clauseLiteral.terms
            for i in range(ruleLiteral.arity):
              # not the same - replace
              if not t1[i].sameAs(t2[i]):
                if not (t1[i].value in ruleVarRenaming and t2[i].value in clauseVarRenaming):
                  if (t1[i].value in ruleVarRenaming and t2[i].value not in clauseVarRenaming) or \
                    (t1[i].value not in ruleVarRenaming and t2[i].value in clauseVarRenaming):
                    # error handling / unknown case
                    ERROR("ONE VALUE IN VAR RENAMING, ANOTHER NOT %s %s %s %s %s %s" %(t1[i].__repr__(), t2[i].__repr__(), ruleLiteral.__repr__(), clauseLiteral.__repr__(), rule.__repr__(), clause.__repr__() ) )
                  else:
                    # introducing new variable
                    ruleVarRenaming[ t1[i].value ] = varName
                    clauseVarRenaming[ t2[i].value ] = varName
                    rule.listOfVars += [varName]
                    varName = self.nextVarName(varName)
            ruleI += 1
            clauseI += 1

        else:
          # same type, not compatible - removal
          toBeRemoved += [ruleI]
          ruleI += 1
          clauseI += 1
      else:
        clauseI += 1

    # remove predicates that needed to be removed:
    newPrecond = []
    for i in range(len(rule.preconds)):
      if i not in toBeRemoved:
        newPrecond += [ rule.preconds[i] ]
    rule.preconds = newPrecond

    # rename preconds
    for pred in rule.preconds:
      for term in pred.terms:
        if term.value in ruleVarRenaming:
          term.makeVariable( ruleVarRenaming[term.value] )
    # rename effects
    for pred in rule.effects:
      for term in pred.terms:
        if term.value in ruleVarRenaming:
          term.makeVariable( ruleVarRenaming[term.value] )

    # print("----------------------------")
    # GOOD(rule)


  def addExample(self, exampleTuple):
    # ------------------------------------------------------------
    # FIRST: input processing
    (prevS_untr, actionParam, actionParamTypes, newS_untr) = exampleTuple
    # add more predicates
    prevS_untr = self.addExtraPreds(prevS_untr, actionParam)
    # translate prevS and newS into predicate form
    prevS = self.translateExample(prevS_untr, actionParam)
    newS = self.translateExample(newS_untr, actionParam)
    # only relevant preds are maintained

    prevS = self.maintainRelevantPreds(prevS, actionParam)
    newS = self.maintainRelevantPreds(newS, actionParam)
    
    # remove predicates that hasn't changed
    # TO DO: should first remove unless changed, than remove unrelated?
    newS = self.removeUnlessChanged(prevS, newS)
    # generate a horn clause out of it; 
    # this assumes that all predicates in the first state are preconds, all changes in the second state are effects
    exClause = Clause( prevS, newS )

    # print(exClause)
    # insert parameters as variables into the clause
    exClause.insertParamsIntoPreds(actionParam, actionParamTypes)
    # print(exClause)
    # save this example
    exampleIndex = self.saveDataPoint(exampleTuple, exClause)

    # return


    # ------------------------------------------------------------
    # SECOND: update existing rules
    print("------------------------")
    for effectPred in exClause.effects:
      # per effect predicate: check if effect if there is a rule with an effect of the same type (positivity+name)
      index = self.findCompatibleRule( effectPred )

      # there isn't one - let's create one
      if index == None:
        self.createNewRule( effectPred, exClause )
        GOOD( "ADDED A NEW CLAUSE RULE %s" %(self.rules[-1].effects[0].__repr__() ))
      else:
        # check if the clause is covered by this rule
        # this entails, for each each predicate of the rule - both in effect and precondition - 
        # checking that there is a compatible literal in the clause of same or higher specificity than that of the rule
        isCovered = self.checkIfClauseIsCoveredByTheRule(effectPred, exClause, index)
        if isCovered:
          # if covered - we don't have to do anything
          GOOD("THIS IS A POSITIVE EXAMPLE FOR RULE %s!"%( self.rules[index].effects[0].__repr__() ))
          # TO DO: mark it as a positive example

        else:
          WARN( "RULE %s MUST BE GENERALIZED" %(self.rules[index].effects[0].__repr__() ) )
          self.generalizeRule( effectPred, exClause, index )


          # we want to run lgg 
          # compatible literals = same name, same negation status

          # for each predicate in the rule: check to find if there is a compatible predicate in the clause
          # if there is not - remove predicate from the rule
          # if there is:
          # if the two predicates are straight up the same - store them
          # if the two predicates are not the same: find where they are not the same, save what is the same as is, what is not - make into variable.
          # params can be made into variables; constants can be made into variables
    INFO("------------------------")
    INFO("ACTION %s" %(self.name))
    INFO("------------------------")
    for rule in self.rules:
      print(rule)
      print("------------------------")
    INFO("------------------------")




    

    # if there isn't a rule that covers this effect predicate - create a new one, using just the clause that i have - cause that's the most specific example

    # if there is one:
    
    # if yes - we don't have to do anything
    # if no, let's work on this
    

    


    # for rule in self.rules:
    #   # should generate new rules per effect; one rule per effect, unless effects are coupled; there are no coupled effects though
    #   # TO DO: checkIfExampleIsPositive must account for variable assignment; i.e., if the rule contains a variable, 
    #   # the clause value may not be the same, but it should be of same type + should match assignment generalization-wise
    #   positive = rule.checkIfExampleIsPositive( exClause )

    #   # example is positive = rule covers one or multiple of the effects of the clause
    #   if positive:
    #     rule.addPosExample(exampleIndex)
    #     GOOD("THIS IS A POSITIVE EXAMPLE for rule with effect %s!"%( rule.effects[0].__repr__() ))
    #     # if the clause contains all the preconditions - the clause satisfied the rule,
    #     # it'd just be a positive example that just matches the rule; we're good

    #     # a more interesting example is the one where the clause doesn't satisfy all the preconditions:
    #     # TO DO: same as with checkIfExampleIsPositive: must account for variable assignment within the rule
    #     # TO DO: introduce param as not a variable, but a type of a constant?
    #     if not rule.checkIfClauseSatisfiesPreconds( exClause ):
    #       WARN( "EXAMPLE DIDN'T SATISFY RULE PRECONDS - RULE %s MUST BE GENERALIZED" %(rule.effects[0].__repr__() ) )
    #       print("RULE")
    #       print(rule)
    #       print("CLAUSE")
    #       print(exClause)
    #       continue
    #       # we have a problem: the clause satisfies the effect, but not the precondition.
    #       # the rule needs fixing
    #       rule.runILP( exClause )
    #       # after that - add the rule to the clause
    #       # at this point, we have an interesting situation.
    #       # all E+ still remains E+ for a more general rule. 
    #       # the same doesn't have to be true for the negative rule!
    #       # so in theory here i should run a check over all the negative rules
    #       # however, i don't really have a way to handle negative examples yet
    #       # TO DO: checking all the negative examples are still negative
    #       rule.checkNegativeExamplesStillNegative()

    #   else:
    #     GOOD("THIS IS A NEGATIVE EXAMPLE for %s!" %(rule.effects[0].__repr__()) )
    #     # example is negative - rule covers none of the effects of the clause
    #     rule.addNegExample(exampleIndex)
  
    #     if rule.checkIfClauseSatisfiesPreconds( exClause ):
    #       # throw an error! this is bad, cause it's a negative example that satisfies preconditons
    #       # i don't really know how to handle this
    #       ERROR("NEGATIVE EXAMPLE SATISFIES PRECONDITIONS")
    #       ERROR("DUNNO HOW TO HANDLE NEGATIVE EXAMPLES...")

          # but this shouldn't happen with the conjunctive rules on boolean predicates / parameterized, i should be good

    # ------------------------------------------------------------
    # THIRD: create some new rules

    # check if all effects are covered
    # notCoveredEffects = self.findNotCoveredEffects( exClause )

    # if len( notCoveredEffects ) != 0:
    #   # need to insert new rules! adding a rule per effect
    #   self.createNewRules( notCoveredEffects, exClause )

  def findNotCoveredEffects(self, clause):
    notCovered = []
    for pred in clause.effects:
      isCovered = False
      for rule in self.rules:
        for effectPred in rule.effects:
          if pred.sameAs(effectPred):
            isCovered = True
            break
        if isCovered:
          break
      if not isCovered:
        notCovered += [pred]
    return notCovered

  def createNewRules(self, notCovered, exClause):
    for pred in notCovered:
      self.createNewRule( pred, exClause )

  def createNewRule(self, effectLiteral, exClause):
    # create a new rule
    self.rules += [ Rule( copy.deepcopy(exClause.preconds), [effectLiteral] ) ]
    # set positive examples for the new rule
    self.rules[-1].setPosExamples( [ len( self.exampleTuples )-1 ], len( self.exampleTuples) )
    # GOOD( "ADDED A NEW CLAUSE RULE: \n%s------------------\n"%self.rules[-1].__repr__() )






class Clause:
  def __init__(self, preconds, effects):
    self.preconds = preconds
    self.effects = effects
    self.listOfVars = []

  def __repr__(self):
    res = "CLAUSE, %i effects, %i preconds\nEFFECTS:\n"%(len(self.effects), len(self.preconds)) 
    for pred in self.effects:
      res += "\t" + pred.__repr__() + "\n"
    res += "PRECONDS:\n"
    for pred in self.preconds:
      res += "\t" + pred.__repr__() + "\n"
    # res += "\n"
    return res

  def insertParamsIntoPreds(self, actionParam, actionParamTypes):
    # action param is a dictionary
    for predName in actionParam:
      predVal = actionParam[predName]
      predType = actionParamTypes[predName]
      for pred in self.preconds:
        for term in pred.terms:
          if term.isConstant() and term.type == predType and term.value == predVal:
            term.makeParam(predName)
      for pred in self.effects:
        for term in pred.terms:
          if term.isConstant() and term.type == predType and term.value == predVal:
            term.makeParam(predName)

class Rule(Clause):
  def __init__(self, preconds, effects):
    super().__init__( preconds, effects )
    self.E_plus = []
    self.E_minus = []

  def setPosExamples( self, Eplus, totalLen ):
    self.E_plus = Eplus
    for i in range(totalLen):
      if i not in Eplus:
        self.E_minus += [i]
  
  def addPosExample( self, index ):
    self.E_plus += [index]

  def addNegExample( self, index ):
    self.E_minus += [index]

  def checkIfExampleIsPositive( self, clause ):
    # check if the effects of the example clause are covered by the rule
    # this doesn't check preconditions

    # each effect of the rule must be covered; note that since we have 1 effect per rule, this should be just 1
    for effectPred in self.effects:
      doesCover = False
      for pred in clause.effects:
        # found a predicate in a clause that is covered by the rule predicate
        if pred.sameAs(effectPred):
          doesCover = True
          break
      if not doesCover:
        return False
    return True

  def checkIfClauseSatisfiesPreconds( self, clause ):
    # the clause must have each of the preconditions of the rule

    for precondPred in self.preconds:
      isCovered = False
      for pred in clause.preconds:
        # found a predicate in a clause that is covered by the rule predicate
        if pred.sameAs(precondPred):
          isCovered = True
          break
      if not isCovered:
        return False
    return True



class Predicate:
  def __init__(self, name, arity, terms):
    self.name = name # armEmpty, pos, movable, etc
    self.arity = arity 
    self.terms = terms # terms: pos, obj, etc

  def __repr__(self):
    res = self.name + "("
    for term in self.terms:
      res += " " + term.__repr__()
    res += " )"
    return res

  def getAllObjs(self):
    objs = []
    for term in self.terms:
      # if term.type == 'obj':
      objs += [term.get()]
    return objs

  def isGround(self):
    for pred in self.terms:
      if pred.isVariable():
        return False
    return True

class Atom(Predicate):
  def __init__(self, name, arity, terms):
    super().__init__( name, arity, terms )

class Literal(Atom):
  def __init__(self, positive, name, arity, terms ):
    self.positive = positive
    super().__init__( name, arity, terms )

  def __repr__(self):
    if self.positive:
      return "" + Predicate.__repr__(self)
    return "NOT " + Predicate.__repr__(self)

  def sameAs(self, op):
    if self.positive != op.positive or self.name != op.name or self.arity != op.arity:
      return False
    
    for i in range( self.arity ):
      if not self.terms[i].sameAs( op.terms[i] ):
        return False
    return True

  def isCompatibleWith( self, op ):
    if self.positive == op.positive and self.name == op.name:
      return True
    return False

  def isSameType( self, op ):
    if self.name == op.name:
      return True
    return False

  def isMoreGeneralThan( self, op ):
    if not self.isCompatibleWith( op ):
      ERROR( "ATTEMPTING TO CHECK GENERALITY WITHOUT CHECKING COMPATIBILITY %s %s" %(self.__repr__(), op.__repr__()) )
      return
    for i in range(self.arity):
      term1 = self.terms[i]
      term2 = op.terms[i]
      # TO DO: literal generality is sketchy for variables; a variable is more general than a param, sure; 
      # but what about variable vs variable?
      # i guess i'd only call this function to compare variable to param / non-params
      if not term1.isMoreGeneralThan(term2):
        return False
    return True

class Term:
  def __init__(self, termType, value):
    self.type = termType # i am dealing with typed objects: obj, pos, conf
    self.valueType = "constant" # constants, parameters, variables. constants are more specific than parameters, more specific than variables
    self.value = value

  def get(self):
    return self.value

  def sameAs(self, term):
    if self.type == term.type and self.valueType == term.valueType and self.value == term.value:
      return True
    return False
      
  def makeVariable(self, varName):
    self.value = varName
    self.valueType = "variable"

  def makeParam(self, paramName):
    self.value = paramName
    self.valueType = "param"

  def makeConstant(self, value):
    self.value = varName
    self.valueType = "constant"

  def isConstant(self):
    return self.valueType == "constant"

  def isVariable(self):
    return self.valueType == "variable"

  def isParam(self):
    return self.valueType == "param"

  def __repr__(self):
    return str(self.value)
    return "(" + self.type + "," + str(self.value) + ")"

  def isMoreGeneralThan( self, term ):
    if self.type != term.type:
      ERROR( "COMPARING GENRALITY FOR TERMS OF DIFFERENT TYPES: %s %s" %( self.__repr__(), term.__repr__() ) )
      return
    st = self.valueType
    ot = term.valueType
    if st == "variable":
      if ot != "variable":
        return True
      WARN("COMPARING GENERALITY OF VARIABLES %s %s" %( self.__repr__(), term.__repr__() ))
      if ot == "variable" and self.value == term.value:
        return True
    elif st == "param" or st == "constant":
      if st == ot and self.value == term.value:
        return True
      # if ( ot == "param" and self.value == term.value) or ot == "constant":
    #     return True
    # elif st == "constant":
    #   if ot == "constant" and self.value == term.value:
    #     return True
    return False




