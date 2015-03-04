from __future__ import division
import os
from flask import Flask, request
from MeteorClient import MeteorClient
import itertools
import random
import operator
import math
import copy
import sys
import json


app = Flask(__name__)


@app.route('/')
def hello():
  return 'Hello World!'

@app.route('/solve', methods = ['POST'])
def solve():
  id = request.form.get('id', None)
  print 'received ' + id
  if id:
    return solve_cryptogram(id)
  else:
    return 'no id'

def subscribed(subscription):
  print '* SUBSCRIBED {}'.format(subscription)


def unsubscribed(subscription):
  print '* UNSUBSCRIBED {}'.format(subscription)


def added(collection, id, fields):
  print '* ADDED {} {}'.format(collection, id)
  for key, value in fields.items():
    print '  - FIELD {}'.format(key)


def callback_function(error, result):
  if error:
    print error


def solve_cryptogram(id):
  si = SimulatedAnnealing()
  return si.solve(id)


def connected():
  print '* CONNECTED'


def logged_in(data):
  print '* LOGGED IN {}'.format(data)


def subscription_callback(error):
  if error:
    print error


class SimulatedAnnealing:
  def __init__(self):
    self.exit = False


  def solve(self, id):

    print 'solving ', id

    def changed(collection, element_id, fields, cleared):
      if collection == 'guesses' and element_id == id and 'kill' in fields.keys():
        self.exit = True

    client.on('changed', changed)


    guess = client.find_one('guesses', selector={'_id': id})


    if not guess or guess.get('kill', False):
      return 'killed'


    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    letters = alphabet + ' '


    def get_ngram_frequencies(text, n, l=letters):
      ngrams = map(''.join, itertools.product(l, repeat=n))
      ngram_count = map(text.count, ngrams)
      return dict(zip(ngrams, [x/sum(ngram_count) for x in ngram_count]))

    def cost(cipher_text):
      cipher_digram_freq = get_ngram_frequencies(cipher_text, 2)
      return sum([abs(cipher_digram_freq[x] - exp_digram_freq[x]) for x in exp_digram_freq.keys()])


    def get_cipher_text(cipher, puzzle):
      return ''.join(map(lambda x: cipher.get(x, x), puzzle))


    def update_status(updates):
      status_object.update(updates)
      client.call('updateGuess', [id, status_object], callback_function)
      # client.update('guesses', {'_id': id}, {'$set': {'status': json.dumps(status_object)}}, callback=update_callback)


    # json object to display the status at each step in the process
    status_object = {}

    # iterations per temperature
    iterations = 2000

    # max characters in puzzle + last letters of a word
    max_characters = 2000

    # filename declaration and method running
    filename = 'moby_dick.txt'


    # open the file and run the method
    with open(filename, 'r') as f:

      # put the data in the string
      moby_dick = f.read()

      # get the sorted letter frequency for the training data
      letter_freq = sorted(get_ngram_frequencies(moby_dick, 1, alphabet).items(), key=operator.itemgetter(1), reverse=True)  # don't include spaces

      # get the digram frequency for the training data
      exp_digram_freq = get_ngram_frequencies(moby_dick, 2)

      # get the text and lowercase it
      full_puzzle = guess['puzzle'].lower()

      # shorten the puzzle for faster iterations -- 1000 characters for now
      if len(full_puzzle) > max_characters:
        next_space = full_puzzle.find(' ', max_characters)
        puzzle = full_puzzle[:max_characters] + (full_puzzle[max_characters: next_space] if next_space > 0 else [])
      else:
        puzzle = full_puzzle

      # get the sorted letter frequency for the puzzle
      puzzle_letter_freq = sorted(get_ngram_frequencies(full_puzzle, 1, alphabet).items(), key=operator.itemgetter(1), reverse=True)
      
      # create a cipher based on most common letters in puzzle mapped to training letter frequency
      cipher = {puzzle_letter_freq[x][0] : letter_freq[x][0] for x in range(26)}
      cipher_text = get_cipher_text(cipher, puzzle)
      parent_cost = cost(cipher_text)

      best_cipher = copy.copy(cipher)
      best_cost = parent_cost

      t = 0.1

      update_status({
        'status': 'starting to solve the puzzle',
        'cipher': best_cipher,
        'cost': best_cost,
        'guess': get_cipher_text(best_cipher, full_puzzle),
        'temperature': t
      })

      while t > .001:

        for j in range(iterations):

          if self.exit:
            print 'killed'
            return 'killed'

          a = random.choice(alphabet)
          b = random.choice(alphabet)

          child_cipher = copy.copy(cipher)

          child_cipher[a], child_cipher[b] = child_cipher[b], child_cipher[a]
          child_cost = cost(get_cipher_text(child_cipher, puzzle))

          if child_cost < parent_cost:
            parent_cost = child_cost
            cipher = child_cipher
            if child_cost < best_cost:
              best_cipher = copy.copy(cipher)
              best_cost = child_cost
          else:
            r = random.random()
            p = math.e**((parent_cost - child_cost)/t)

            if p > r:
              parent_cost = child_cost
              cipher = child_cipher

        update_status({
          'status': 'solving the puzzle',
          'cipher': best_cipher,
          'cost': best_cost,
          'guess': get_cipher_text(best_cipher, full_puzzle),
          'temperature': t
        })

        t *= 2/3

      update_status({
        'status': 'final guess',
        'cipher': best_cipher,
        'cost': best_cost,
        'guess': get_cipher_text(best_cipher, full_puzzle),
        'temperature': t
      })

      return 'returned'


if __name__ == '__main__':
  client = MeteorClient('ws://ddp--9611-cryptograms.meteor.com/sockjs/862/websocket')


  client.on('logged_in', logged_in)
  client.on('subscribed', subscribed)
  client.on('unsubscribed', unsubscribed)
  client.on('connected', connected)
  client.on('added', added)


  client.connect()
  client.subscribe('guesses')
  client.login(user='admin', password='apple1')

  app.run(threaded=True)