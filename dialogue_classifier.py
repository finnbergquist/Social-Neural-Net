import nltk
from nltk.stem.lancaster import LancasterStemmer
import os
import json
import datetime
import csv
import numpy as np
import time

def get_raw_training_data(path):
    dicts = []
    row_info = {}
    with open(path, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            row_info["person"] = row[0].replace('"', '')
            row_info["sentence"] = row[1].replace('"', '')
            dicts.append(row_info)

    return dicts

def preprocess_words(words, stemmer):
    stems = set()
    for word in words:
        stems.add(stemmer.stem(word))
    return list(stems)

def organize_raw_training_data(raw_training_data, stemmer):
    words = [] #all words used by anyone
    documents = []
    classes = set()
    for row_dict in raw_training_data:
        tokens = nltk.word_tokenize(row_dict['sentence'])
        row_dict["sentence"] = tokens
        words.extend(tokens)#add all tokens to words
        classes.add(row_dict["person"])
        documents.append(row_dict)

    words = preprocess_words(words, stemmer)
    return words, list(classes), documents

def create_training_data(words, classes, documents, stemmer):
    training_data = []
    bag = [0] * len(words)

    output = []
    output_line = [0] * len(classes)

    for document in documents:
        tokens = document["sentence"]
        for i,word in enumerate(words):
            if word in tokens:
                bag[i] = 1

        training_data.append(bag)
        bag = [0] * len(words)

        for i,name in enumerate(classes):
            if name in classes:
                output_line[i] = 1
            
        output.append(output_line)
        output_line = [0] * len(classes)

    return training_data, output

def sigmoid(z):
    return 


def main():
    stemmer = LancasterStemmer()
    raw_training_data = get_raw_training_data('dialogue_data.csv')
    words, classes, documents = organize_raw_training_data(raw_training_data, stemmer)
    training_data, output = create_training_data(words, classes, documents, stemmer)


if __name__ == "__main__":
    main()