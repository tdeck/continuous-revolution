"""
A really hasty implementation of the dissociative press algorithm.
"""
import re
import random

def ngrams(tokens, n):
    return [
        tokens[i:i+n]
            for i in range(len(tokens) - n + 1)
    ]

class Dissoc(object):
    """
    A class for generating nonsense text based on a corpus.
    """
    def __init__(self, n=2):
        self.ngrams = {}
        self.n = n
        self.starting_ngrams = []
    
    def train(self, messages):
        """
        Train with a list of messages.
        """
        for message in messages:
            self.process(message)

    def process(self, message):
        """
        Train with a single message.
        """
        tokens = [
            token
                for token in re.split(' +|([\.\(\),?!\n])', message)
                if token
        ] + ['EOM']

        if len(tokens) < self.n: return

        message_ngrams = ngrams(tokens, self.n)
        for ngram in message_ngrams:
            key = '+'.join(tok.lower() for tok in ngram[:self.n - 1])
            if key not in self.ngrams:
                self.ngrams[key] = []
            self.ngrams[key].append(ngram)

        self.starting_ngrams.append(message_ngrams[0])
    
    def produce(self):
        """
        Generate a randomized message.
        """
        message_tokens = random.choice(self.starting_ngrams)[:]
        while message_tokens[-1] != 'EOM':
            key = '+'.join((tok.lower() for tok in message_tokens[-self.n + 1:]))
            message_tokens.append(random.choice(self.ngrams[key])[-1])
        
        return re.sub("\s*\n[\n\s]*", "\n",
            re.sub(r" (\W)", r'\1', 
                ' '.join(message_tokens[:-1])
            )
        ).strip()
