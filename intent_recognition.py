import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import WordNetLemmatizer
import csv

# nltk downloads
nltk.download('punkt')
nltk.download('wordnet')

# Preprocesses text by tokenization, lemmatization, and removing non-alphabetic characters
def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    tokens = nltk.word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalpha()]
    # Stopwords removal has been commented out
    # tokens = [token for token in tokens if token not in stopwords.words('english')]
    return ' '.join(tokens)

# Loads and returns intents, questions, and answers from given files
def load_data(intents_file, qa_file, restaurant_file):
    with open(intents_file) as file:
        intents = json.load(file)['intents']

    questions, answers = [], []
    # Load general QA data
    with open(qa_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        for row in reader:
            questions.append(row[1])
            answers.append(row[2])

    # Load restaurant-specific questions and answers
    restaurant_questions, restaurant_answers = [], []
    with open(restaurant_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        for row in reader:
            question = row[1]
            answer = row[2]
            restaurant_questions.append(question)
            restaurant_answers.append(answer)

    
    return intents, questions, answers, restaurant_questions, restaurant_answers

# Vectorizes text data and returns vectorizer, matrix X, and labels for intent recognition
def vectorize_data(intents, questions):
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))  # Using bigrams in addition to unigrams
    labels, patterns = [], []

    for intent in intents:
        for pattern in intent['patterns']:
            labels.append(intent['tag'])
            patterns.append(preprocess_text(pattern))

    all_texts = patterns + questions
    X = vectorizer.fit_transform(all_texts)

    return vectorizer, X, labels

# Define similarity thresholds for intent recognition and question-answering
INTENT_SIMILARITY_THRESHOLD = 0.3  # Adjusted threshold for intents
QA_SIMILARITY_THRESHOLD = 0.15     # Threshold for QA pairs

# Recognizes intent or answers a question based on input text, using cosine similarity
def recognize_intent(input_text, vectorizer, X, labels, questions, answers):
    input_vec = vectorizer.transform([preprocess_text(input_text)])
    similarities = cosine_similarity(input_vec, X).flatten()
    best_match = np.argmax(similarities)
    best_similarity = similarities[best_match]

    
    if best_match < len(labels):
        if best_similarity < INTENT_SIMILARITY_THRESHOLD:
            return 'unknown', None
        return 'intent', labels[best_match]
    else:
        if best_similarity < QA_SIMILARITY_THRESHOLD:
            return 'unknown', None
        return 'qa', answers[best_match - len(labels)]

# Sets up intent recognition by loading data and vectorizing text
def setup_intent_recognition(intents_file, qa_file, restaurant_file):
    intents, questions, answers, restaurant_questions, restaurant_answers = load_data(intents_file, qa_file, restaurant_file)
    vectorizer, X, labels = vectorize_data(intents, questions + restaurant_questions)
    return vectorizer, X, labels, questions, answers, restaurant_questions, restaurant_answers


































 
   
