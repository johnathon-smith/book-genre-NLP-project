import numpy as np
import pandas as pd
import nltk
from nltk.tokenize.toktok import ToktokTokenizer
from nltk.corpus import stopwords
import unicodedata
import re

def basic_clean(string):
    """
    This function will perform basic cleaning of a string. It will reduce all characters 
    to lower case, normalize unicode characters, and remove anything that is not a 
    letter, number, whitespace, or a single quote.
    """
    
    #Lower case everything
    string = string.lower()
    
    #Normalize unicode characters, 
    #encode into ascii byte strings and ignore unknown chars,
    #decode back into a UTF-8 string that we can work with
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode('UTF-8')
    
    #Use regex to replace anything that is not a letter, number, whitespace, or a single quote
    string = re.sub(r"[^a-z0-9\s']", '', string)
    
    return string

def tokenize(string):
    """
    This function will tokenize all the words in the given string and return the 
    tokenized string.
    """
    
    #Create the tokenizer
    tokenizer = nltk.tokenize.ToktokTokenizer()
    
    #Use the tokenizer
    string = tokenizer.tokenize(string, return_str = True)
    
    return string

def stem(string):
    """
    This function will accept some text and return a stemmed version of the text.
    """
    
    #Create porter stemmer
    ps = nltk.porter.PorterStemmer()
    
    #Apply the stemmer to each word in the string to create a list of stemmed words
    stems = [ps.stem(word) for word in string.split()]
    
    #join our list of stemmed words into a string
    string_stemmed = ' '.join(stems)
    
    return string_stemmed

def lemmatize(string):
    """
    This function accepts some text and returns the lemmatized version of the string.
    """
    
    #Create the lemmatizer
    wnl = nltk.stem.WordNetLemmatizer()
    
    #Use the lemmatizer on each word in the string to create a list of lemmatized words
    lemmas = [wnl.lemmatize(word) for word in string.split()]
    
    #Join the lemmatized words into one string
    string_lemmatized = ' '.join(lemmas)
    
    return string_lemmatized

def remove_stopwords(string, extra_words = [], exclude_words = []):
    """
    This function will accept a string and return a version of the text without any stopwords.
    It will also allow the user to add extra words to remove or exclude words from the removal list.
    """
    #Get the standard english stop word list from nltk
    stop_words = stopwords.words('english')
    
    #Add the extra words to be removed to the stop word list
    for word in extra_words:
        stop_words.append(word)
    
    #Remove the words to be excluded from the stop word list
    for word in exclude_words:
        stop_words.remove(word)
    
    #Create a list of words to be checked by splitting the given string
    words = string.split()
    
    #Now filter out all of the stop words
    filtered_words = [word for word in words if word not in stop_words]
    
    #Join the list of filtered words into a string
    filtered_string = ' '.join(filtered_words)
    
    return filtered_string

def prepare_articles(df, col, extra_words = [], exclude_words = []):
    """
    This function will take in a df and prepare the articles within. It will utilize the functions defined above and return the df with
    new columns for the original, cleaned, stemmed, and lemmatized versions of the content.
    """

    #rename the content column to be original
    df.rename(columns = {col:'original'}, inplace = True)

    #create the 'clean' column
    df['clean'] = df['original']

    #apply the basic_clean, tokenize, and remove_stopwords functions
    df['clean'] = df['clean'].apply(basic_clean)
    df['clean'] = df['clean'].apply(tokenize)

    #create the stemmed column
    df['stemmed'] = df['clean']

    #apply the stem function
    df['stemmed'] = df['stemmed'].apply(stem).apply(remove_stopwords, extra_words = extra_words, exclude_words = exclude_words)

    #create the lematize column
    df['lemmatized'] = df['clean']

    #apply the lemmatize function
    df['lemmatized'] = df['lemmatized'].apply(lemmatize).apply(remove_stopwords, extra_words = extra_words, exclude_words = exclude_words)

    #apply the remove_stopwords function to the 'clean' column
    df['clean'] = df['clean'].apply(remove_stopwords, extra_words = extra_words, exclude_words = exclude_words)

    #Remove any entries that did not have a description
    df.dropna(inplace = True)

    return df

def get_char_count(string):
    """
    This function will take in a string and return the number of characters in it.
    """
    
    return len(string)

def get_word_count(string):
    """
    This function will take in a string and return the number of words in that string.
    This function will include repeat words.
    """
    
    #Create a list of words separated by a space
    words = string.split()
    
    return len(words)

def get_unique_words(string):
    """
    This function will take in a string and return the number of unique words in that string.
    """
    
    words = string.split()
    words = set(words)
    
    return len(words)

def get_sentence_count(string):
    """
    This function will take in a string and return the number of sentences in that string.
    """

    sentences = nltk.sent_tokenize(string)

    return len(sentences)

def get_sentiment_compound(string):
    """
    This function will take in a string, analyze the sentiment, and return the compound
    value.
    """
    
    sia = nltk.sentiment.SentimentIntensityAnalyzer()
    
    #sia returns a dict, so access the compound score accordingly
    compound = sia.polarity_scores(string)['compound']
    
    return compound

def get_stopword_count(string):
    """
    This function takes in a string and returns the number of stopwords in that string.
    """
    
    #Create a list of the words in the string
    words = string.split()
    
    #Initialize the count var
    count = 0
    
    #Loop through each word and check whether or not it is in the stopword dict
    #If it is, increase count by 1
    
    for word in words:
        if word in stopwords.words('english'):
            count += 1
    
    return count

def prep_for_exploration(df):
    """
    This function takes in the dataframe of prepared book blurbs and performs several functions to create features
    for exploration. This function will create columns for character counts, word counts, unique word counts,
    sentence counts, stop word counts, average number of words per sentence, stop word to word ratios, and 
    sentiment analysis compound scores.

    It returns the updated dataframe.
    """

    #get the character counts of the lemmatized documents
    df['lem_char_count'] = df.lemmatized.apply(get_char_count)

    #get the word counts of the lemmatized documents
    df['lem_word_count'] = df.lemmatized.apply(get_word_count)

    #get the unique word counts of the lemmatized documents
    df['lem_unique_word_count'] = df.lemmatized.apply(get_unique_words)

    #get the sentence counts
    df['sentence_count'] = df.original.apply(get_sentence_count)

    #get the average number of words per sentence
    df['avg_words_per_sentence'] = round(df.lem_word_count / df.sentence_count).astype(int)

    #get the sentiment analysis compound scores of the original documents
    df['sentiment'] = df.original.apply(get_sentiment_compound)

    #get the stop word counts
    df['stopword_count'] = df.original.apply(get_stopword_count)

    #get the stop word to word ratio
    df['word_stopword_ratio'] = round(df.stopword_count / df.lem_word_count, 2)

    return df