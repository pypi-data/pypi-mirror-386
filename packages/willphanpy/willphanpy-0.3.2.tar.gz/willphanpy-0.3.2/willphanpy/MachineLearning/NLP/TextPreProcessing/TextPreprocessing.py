import string
from collections import Counter

class TextPreprocessing:
    '''
    Pre-Processing techniques for Natural Language Processing
    '''
    def __init__(self, text: str = ""):
        self.text = text
        self.tokens = []
        self.emotions = []

    def readFile(self, filename):
        '''
        Read a file that includes a text
        '''
        self.text = open(filename, encoding='utf-8').read()

    def analyzeEmotion(self, filename):
        '''
        Read an emotion list and analyze emotions based on the emotion list
        '''
        with open(filename) as file:
            for line in file:
                line = line.replace('\n', '').replace(',', '').replace("'", '').strip()
                word, emotion = line.split(":")
                
                if word in self.tokens:
                    self.emotions.append(emotion.strip())

            self.emotions = Counter(self.emotions)


    def preprocess(self):
        '''
        Pre-processing methods
        - Convert all words into lowercase
        - Remove punctuation
        - Tokenization -> store words from a sentence to an array
        - Remove stop words -> words that do not contribute any meaning to a sentence
        '''
        # Convert all words to lowercas
        self.__lowercase()

        # Remove punctuation
        self.__removePunctuation()

        # Tokenization
        self.__tokenization()

        # Remove stop words
        self.__removeStopWords()

    def __lowercase(self):
        '''
        Convert text to all lowercase
        '''
        self.text = self.text.lower()

    def __removePunctuation(self):
        '''
        - Remove all punctuation in the text
        - 
        '''
        self.text = self.text.translate(str.maketrans('', '', string.punctuation))

    def __tokenization(self):
        '''
        Tokenization
        '''
        self.tokens = self.text.split()

    def __removeStopWords(self):
        '''
        Remove stop words
        '''
        stop_words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
              "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself",
              "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these",
              "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do",
              "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while",
              "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before",
              "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
              "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each",
              "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
              "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]
        new_tokens = []
        for word in self.tokens:
            if word not in stop_words:
                new_tokens.append(word)
        
        self.tokens = new_tokens
