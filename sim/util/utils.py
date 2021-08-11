import io
from termcolor import colored

try:
   user_input = raw_input
except NameError:
   user_input = input

def ERROR(text):
  print(colored(text,'red'))

def WARN(text):
  print(colored(text,'yellow'))

def GOOD(text):
  print(colored(text,'green'))

def INFO(text):
  print(colored(text,'blue'))
