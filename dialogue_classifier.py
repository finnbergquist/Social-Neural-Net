import nltk
from nltk.stem.lancaster import LancasterStemmer
import os
import json
import datetime
import csv
import numpy as np
import time

"""* * * PREPARING DATA * * *"""
def get_raw_training_data(path):
    """ Reads data in from a csv file, returning a list of dictionaries. Each
    dictionary will have two key-val pairs with keys 'person' and 'sentence."""

    dicts = []
    with open(path, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            if row:
                #create a dictionary with person and sentence for each row
                row_info = {}
                row_info["person"] = row[0].replace('"', '')
                row_info["sentence"] = row[1].replace('"', '')
                dicts.append(row_info)
    return dicts

def preprocess_words(words, stemmer):
    """Generate stems for each word, eliminating duplicates. The stem 
    represents the meaningful chunk of the word that will be useful. Returns 
    a list of all the unique stems."""

    stems = set()
    for word in words:
        stems.add(stemmer.stem(word))
    return list(stems)

def organize_raw_training_data(raw_training_data, stemmer):
    """Organizes the training data by gathering lists of all the unique word
    stems and actors(we calling them classes) observed from the training data.
    Words holds all the unique word stems, classes holds all the unique actors, 
    and documents holds tuples of actor name with tokens for the sentence."""

    #Initialize variables
    words = []
    documents = []
    classes = set()

    #Fill the organized trianing structures
    for row_dict in raw_training_data:
        tokens = nltk.word_tokenize(row_dict['sentence'])
        words.extend(tokens)#combine current words with all new ones
        classes.add(row_dict["person"])
        documents.append((row_dict["person"], tokens,stemmer))

    words = preprocess_words(words, stemmer)#eliminates duplicate words
    return words, list(classes), documents

def create_training_data(words, classes, documents, stemmer):
    """Our training data gets organized into two 2D lists, which store info
    on actors and words used. Each element in the training_data list is a list
    of n integers(0 or 1) where n is the number of words. There is a 1 at any 
    index where that corresponding word is used in the sentence. The same 
    strategy is used for output, but n represents the number of 
    classes(actors), and there is a 1 at the index of corresponding actor."""

    #Initialize the structures
    training_data = []
    bag = [0] * len(words)
    output = []
    output_line = [0] * len(classes)

    #loop through all training data points
    for document in documents:
        tokens = document[1]

        #mark which words were used
        for i,word in enumerate(words):
            if word in tokens:
                bag[i] = 1 #set corresponding word's index to 1

        #set bag back to default
        training_data.append(bag)
        bag = [0] * len(words)

        #marks which character said the line
        character_name = document[0]
        for i,name in enumerate(classes):
            if character_name == name:
                output_line[i] = 1#set corresponding class's index to 1

        #set output_line back to default    
        output.append(output_line)
        output_line = [0] * len(classes)

    return training_data, output

def sigmoid(z):
    """Returns output of sigmoid function on z."""

    return 1/(1 + np.exp(-z))

def sigmoid_output_to_derivative(output):
    """Convert the sigmoid function's output to its derivative."""

    return output * (1-output)

"""* * * TRAINING * * *"""

def init_synapses(X, hidden_neurons, classes):
    """Initializes our synapses (using random values)."""

    # Ensures we have a "consistent" randomness for convenience.
    np.random.seed(1)

    # randomly initialize our weights with mean 0
    synapse_0 = 2*np.random.random((len(X[0]), hidden_neurons)) - 1
    synapse_1 = 2*np.random.random((hidden_neurons, len(classes))) - 1

    return synapse_0, synapse_1

def feedforward(X, synapse_0, synapse_1):
    """Feed forward through layers 0, 1, and 2."""

    layer_0 = X
    layer_1 = sigmoid(np.dot(layer_0, synapse_0))
    layer_2 = sigmoid(np.dot(layer_1, synapse_1))
    return layer_0, layer_1, layer_2


def get_synapses(epochs, X, y, alpha, synapse_0, synapse_1):
    """Update our weights for each epoch."""

    # Initializations.
    last_mean_error = 1

    prev_synapse_0_weight_update = np.zeros_like(synapse_0)
    synapse_0_direction_count = np.zeros_like(synapse_0)

    prev_synapse_1_weight_update = np.zeros_like(synapse_1)
    synapse_1_direction_count = np.zeros_like(synapse_1)

    # Make an iterator out of the number of epochs we requested.
    for j in iter(range(epochs+1)):
        layer_0, layer_1, layer_2 = feedforward(X, synapse_0, synapse_1)

        # How much did we miss the target value?
        layer_2_error = y - layer_2

        if (j% 10000) == 0 and j > 5000:
            # If this 10k iteration's error is greater than the last iteration,
            # break out.
            if np.mean(np.abs(layer_2_error)) < last_mean_error:
                print("delta after "+str(j)+" iterations:" + \
                    str(np.mean(np.abs(layer_2_error))) )
                last_mean_error = np.mean(np.abs(layer_2_error))
            else:
                print("break:", np.mean(np.abs(layer_2_error)), ">", \
                    last_mean_error )
                break

        # In what direction is the target value?  
        # How much is the change for layer_2?
        layer_2_delta = layer_2_error * sigmoid_output_to_derivative(layer_2)

        # How much did each l1 value contribute to the l2 error 
        # (according to the weights)?
        # (Note: .T means transpose and can be accessed via numpy!)
        layer_1_error = layer_2_delta.dot(synapse_1.T)

        # In what direction is the target l1?  
        # How much is the change for layer_1?
        layer_1_delta = layer_1_error * sigmoid_output_to_derivative(layer_1)

        # Manage updates.
        synapse_1_weight_update = (layer_1.T.dot(layer_2_delta))
        synapse_0_weight_update = (layer_0.T.dot(layer_1_delta))

        if j > 0:
            synapse_0_direction_count += \
                np.abs(((synapse_0_weight_update > 0)+0) - \
                    ((prev_synapse_0_weight_update > 0) + 0))
            synapse_1_direction_count += \
                np.abs(((synapse_1_weight_update > 0)+0) - \
                    ((prev_synapse_1_weight_update > 0) + 0))

        synapse_1 += alpha * synapse_1_weight_update
        synapse_0 += alpha * synapse_0_weight_update

        prev_synapse_0_weight_update = synapse_0_weight_update
        prev_synapse_1_weight_update = synapse_1_weight_update

    return synapse_0, synapse_1

def save_synapses(filename, words, classes, synapse_0, synapse_1):
    """Save our weights as a JSON file for later use."""

    now = datetime.datetime.now()

    synapse = {'synapse0': synapse_0.tolist(), 'synapse1': synapse_1.tolist(),
               'datetime': now.strftime("%Y-%m-%d %H:%M"),
               'words': words,
               'classes': classes
              }
    synapse_file = "synapses.json"

    with open(synapse_file, 'w') as outfile:
        json.dump(synapse, outfile, indent=4, sort_keys=True)
    print("Saved synapses to:", synapse_file)

def train(X, y, words, classes, hidden_neurons=10, alpha=1, epochs=50000):
    """Train using specified parameters."""

    print("Training with {0} neurons and alpha = {1}".format(hidden_neurons, \
        alpha))

    synapse_0, synapse_1 = init_synapses(X, hidden_neurons, classes)

    # For each epoch, update our weights
    synapse_0, synapse_1 = \
        get_synapses(epochs, X, y, alpha, synapse_0, synapse_1)

    # Save our work
    save_synapses("synapses.json", words, classes, synapse_0, synapse_1)

def start_training(words, classes, training_data, output):
    """Initialize training process and keep track of processing time."""

    start_time = time.time()
    X = np.array(training_data)
    y = np.array(output)

    train(X, y, words, classes, hidden_neurons=20, alpha=0.1, epochs=100000)

    elapsed_time = time.time() - start_time
    print("Processing time:", elapsed_time, "seconds")

"""* * * CLASSIFICATION * * *"""

def bow(sentence, words):
    """Return bag of words for a sentence."""

    stemmer = LancasterStemmer()

    # Break each sentence into tokens and stem each token.
    sentence_words = [stemmer.stem(word.lower()) for word in \
        nltk.word_tokenize(sentence)]

    # Create the bag of words.
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                bag[i] = 1
    return (np.array(bag))

def get_output_layer(words, sentence):
    """Open our saved weights from training and use them to predict based on
    our bag of words for the new sentence to classify."""

    # Load calculated weights.
    synapse_file = 'synapses.json'
    with open(synapse_file) as data_file:
        synapse = json.load(data_file)
        synapse_0 = np.asarray(synapse['synapse0'])
        synapse_1 = np.asarray(synapse['synapse1'])

    # Retrieve our bag of words for the sentence.
    x = bow(sentence.lower(), words)
    # This is our input layer (which is our bag of words for the sentence).
    l0 = x
    # Perform matrix multiplication of input and hidden layer.
    l1 = sigmoid(np.dot(l0, synapse_0))
    # Create the output layer.
    l2 = sigmoid(np.dot(l1, synapse_1))
    return l2

def classify(words, classes, sentence):
    """Classifies a sentence by examining known words and classes and 
    loading our calculated weights (synapse values)."""

    error_threshold = 0.2
    results = get_output_layer(words, sentence)
    results = [[i,r] for i,r in enumerate(results) if r>error_threshold ]
    results.sort(key=lambda x: x[1], reverse=True)
    return_results =[[classes[r[0]],r[1]] for r in results]
    print("\nSentence to classify: {0}\nClassification: {1}".format(sentence, \
        return_results))
    return return_results

def main():
    # All the training  preperations.
    nltk.download('punkt')
    stemmer = LancasterStemmer()
    raw_training_data = get_raw_training_data('dialogue_data.csv')
    words, classes, documents = \
        organize_raw_training_data(raw_training_data, stemmer)
    training_data, output = \
        create_training_data(words, classes, documents, stemmer)
    
    # Comment this out if you have already trained once 
    # and don't want to re-train.
    start_training(words, classes, training_data, output)

    # Classify new sentences.
    classify(words, classes, "will you look into the mirror?")
    classify(words, classes, "mithril, as light as a feather, \
        and as hard as dragon scales.")
    classify(words, classes, "the thieves!")

if __name__ == "__main__":
    main()