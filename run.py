import os # os path
import sys, getopt # passing command line arguments
import numpy as np 

try:
  from tkinter import Tk, Canvas, Toplevel
except ImportError:
  from Tkinter import Tk, Canvas, Toplevel

# imports from local files
from sim.Environment import Environment
from sim.util.utils import user_input

def main(argv):
  print(argv)
  testMode, demoMode = False, False
  if len(argv) > 1:
    print('usage is: python3 run.py -d -t')
    print('\t-d for demo mode')
    print('\t-t for testing mode')
    print('\t-h for help')
    sys.exit(2)
  elif len(argv) == 0:
    testMode = True

  for arg in argv:
    if arg == '-h':
      print('usage is: python3 run.py -d -t')
      print('\t-d for demo mode')
      print('\t-t for testing mode')
      print('\t-h for help')
      sys.exit()
    elif arg == "-d":
      demoMode = True
      print("IN DEMO MODE")
    elif arg == "-t":
      testMode = True
      print("IN TEST MODE")

  env = Environment(3, 9)

  if testMode:
    env.inTestMode()
  


if __name__ == '__main__':
    main(sys.argv[1:])
    user_input("Finish?")