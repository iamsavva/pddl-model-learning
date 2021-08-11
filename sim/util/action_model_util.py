from sim.state_estimator import Rule, ActionRuleBased
from termcolor import colored
import pandas as pd 

# -----------------------------
def sum(listA, listB):
  if len(listA) != len(listB):
    print(colored("ERROR:", 'red'), "can't add two lists, unequal sizes")
    return None
  return tuple([i+j for i,j in zip(listA, listB)])

def negate(listA):
  return tuple([-i for i in listA])