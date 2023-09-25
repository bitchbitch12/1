# -*- coding: utf-8 -*-
"""2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12tqaSQz3QNt41m5cc2zwnMd1dLUHpnML
"""

!pip install pyLDAvis

# Commented out IPython magic to ensure Python compatibility.
import warnings
warnings.filterwarnings('ignore',category=DeprecationWarning)

# import libraries
import numpy as np
import pandas as pd
import nltk
import matplotlib.pyplot as plt
import re,random,os
import seaborn as sns
from nltk.corpus import stopwords
import string
from pprint import pprint as pprint

# spacy for basic processing, optional, can use nltk as well(lemmatisation etc.)
import spacy

#gensim for LDA
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel

#plotting tools
import pyLDAvis
import pyLDAvis.gensim #dont skip this
import matplotlib.pyplot as plt
# %matplotlib inline

nltk.download("stopwords")

spacy.cli.download("en_core_web_sm")

from google.colab import drive
drive.mount("/content/drive")

df = pd.read_csv("/content/drive/MyDrive/SEM 8/NLP/Assignment PPT/demonetization-tweets.csv", encoding = "cp1252")
print(df.shape)
df.head()

df.info()

# see randomly chosen sample tweets
df.text[random.randrange(len(df.text))]

df.text[:10]

"""Note that many tweets have strings such as RT, @xyz, etc. Some have URLs, punctuation marks, smileys etc. The following code cleans the data to handle many of these issues.

## **DATA CLEANING & PREPROCESSING**
"""

# remove URLs
def remove_URL(x):
    return x.replace(r'https[a-zA-Z0-9]*',"",regex=True)

#clean tweet text
def clean_tweets(tweet_col):
    df=pd.DataFrame({'tweet':tweet_col})
    df['tweet']=df['tweet'].replace(r'\'|\"|\,|\.|\?|\+|\-|\/|\=|\(|\)|\n|"', '', regex=True)
    df['tweet']=df['tweet'].replace("  "," ")
    df['tweet']=df['tweet'].replace(r'@[a-zA-Z0-9]*', '', regex=True)
    df['tweet']=remove_URL(df['tweet'])
    df['tweet']=df['tweet'].str.lower()

    return(df)

cleaned_tweets=clean_tweets(df.text)
cleaned_tweets[:10]

# tokenize using gensims simple_preprocess
def sent_to_words(sentences, deacc=True):  # deacc=True removes punctuations
    for sentence in sentences:
        yield(simple_preprocess(str(sentence)))

def lemmatization(texts,allowed_postags=['NOUN','ADJ','VERB','ADV']):
    """https://spacy.io/api/annotation"""
    texts_out=[]
    for sent in texts:
        doc=nlp(' '.join(sent))
        texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out

"""Since tweets often contain slang words such as wat, rt, lol etc, we can append the stopwords with a list of such custom words and remove them."""

stop_words= stopwords.words('english') + list(string.punctuation)

words_remove = ["ax","i","you","edu","s","t","m","subject","can","lines","re","what", "there",
                    "all","we","one","the","a","an","of","or","in","for","by","on","but","is","in",
                    "a","not","with","as","was","if","they","are","this","and","it","have","from","at",
                    "my","be","by","not","that","to","from","com","org","like","likes","so","said","from",
                    "what","told","over","more","other","have","last","with","this","that","such","when",
                    "been","says","will","also","where","why","would","today", "in", "on", "you", "r", "d",
                    "u", "hw","wat", "oly", "s", "b", "ht", "rt", "p","the","th", "lol", ':']

#remove stop words, punctuations
stop_words = set(list(stopwords.words('english') + list(string.punctuation)+words_remove))
data_words= list(sent_to_words(cleaned_tweets.tweet.values.tolist(), deacc=False))

# remove stopwords
def remove_stopwords(texts, stop_words=stop_words):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]

data_words_nostops = remove_stopwords(data_words)


# spacy for lemmatization
nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
data_lemmatized = lemmatization(data_words_nostops, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])

# sample lemmatized tweets
data_lemmatized[0:3]

# create dictionary and corpus
id2word = corpora.Dictionary(data_lemmatized)
texts = data_lemmatized
corpus = [id2word.doc2bow(text) for text in texts]

corpus[0:3]

"""## **HYPERPARAMETER TUNING**"""

# compute coherence value at various values of alpha and num_topics
def compute_coherence_values(dictionary, corpus, texts, num_topics_range,alpha_range):
    coherence_values=[]
    model_list=[]

    for alpha in alpha_range:
        for num_topics in num_topics_range:
            lda_model= gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, alpha=alpha,num_topics=num_topics,\
                                                      per_word_topics=True)
            model_list.append(lda_model)
            coherencemodel=CoherenceModel(model=lda_model,texts=texts,dictionary=dictionary,coherence='c_v')
            coherence_values.append((alpha,num_topics,coherencemodel.get_coherence()))

    return model_list,coherence_values

# build models across a range of num_topics and alpha
num_topics_range=[2,6,10,15]
alpha_range=[0.01,0.1,1]
model_list, coherence_values=compute_coherence_values(dictionary=id2word,corpus=corpus,texts=data_lemmatized,
                                                      num_topics_range=num_topics_range,
                                                     alpha_range=alpha_range)

coherence_df = pd.DataFrame(coherence_values,columns=['alpha','num_topics','coherence_value'])

coherence_df

# plot
def plot_coherence(coherence_df,alpha_range,num_topics_range):
    plt.figure(figsize=(16,6))

    for i,val in enumerate(alpha_range):
        #subolot 1/3/i
        plt.subplot(1,3,i+1)
        alpha_subset=coherence_df[coherence_df['alpha']==val]
        plt.plot(alpha_subset['num_topics'],alpha_subset['coherence_value'])
        plt.xlabel('num_topics')
        plt.ylabel('Coherence Value')
        plt.title('alpha={0}'.format(val))
        plt.ylim([0.30,1])
        plt.legend('coherence value', loc='upper left')
        plt.xticks(num_topics_range)

# plot
plot_coherence(coherence_df,alpha_range,num_topics_range)

"""## **MODEL BUILDING**"""

# Build LDA model with alpha=0.1 and 10 topics
lda_model= gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=id2word, num_topics=10, random_state=100,\
                                          update_every=1,chunksize=100, passes=10, alpha=0.1, per_word_topics=True)

# print keywords
pprint(lda_model.print_topics())
doc_lda = lda_model[corpus]

# coherence score
coherence_model_lda = CoherenceModel(model=lda_model, texts=data_lemmatized, dictionary=id2word, coherence='c_v')
coherence_lda = coherence_model_lda.get_coherence()
print('Coherence Score: ', coherence_lda)

# Visualize the topics
pyLDAvis.enable_notebook()
vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word)
vis

"""### Heaps law"""

i = 0
tokens = text.split(" ")
words = set()
x,y = [],[]
for word in tokens:
    words.add(word)
    i += 1
    x.append(i)
    y.append(len(words))

plt.plot(x,y)

"""Zipf law"""

text = """This is a sample text demonstrating Zipf's law. Zipf's law is an empirical law that states that in a large text corpus, the frequency of a word is inversely proportional to its rank. This means that a few words occur very frequently, while most words occur rarely. Zipf's law has been observed in various natural language texts and is a fundamental principle in linguistics and information retrieval."""

words = text.lower().split()

word_freq = {}
for word in words:
    word = ''.join(e for e in word if e.isalnum())
    if word:
        word_freq[word] = word_freq.get(word, 0) + 1

sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

word_ranks = {word[0]: rank + 1 for rank, word in enumerate(sorted_words)}

product_freq_rank = [rank * freq for word, freq, rank in zip(sorted_words, word_ranks.values(), sorted_words)]

print("Top 10 most common words:")
for word, freq in sorted_words[:10]:
    print(f"{word}: {freq}")
import matplotlib.pyplot as plt

frequencies = [freq for word, freq in sorted_words]
ranks = list(range(1, len(sorted_words) + 1))

plt.figure(figsize=(10, 6))
plt.loglog(ranks, frequencies, marker='o', linestyle='-', color='b')
plt.xlabel("Rank (log scale)")
plt.ylabel("Frequency (log scale)")
plt.title("Zipf's Law")
plt.grid(True)
plt.show()