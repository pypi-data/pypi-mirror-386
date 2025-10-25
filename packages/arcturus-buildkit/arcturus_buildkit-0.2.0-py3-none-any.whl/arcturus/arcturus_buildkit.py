import re
import math
import random
from . import data_arcturus

# -------------------------
# NLP Pipeline
# -------------------------
class arcturusNLP:
    def __init__(self):
        self.LEMMATIZER = data_arcturus.LEMMATIZER
        self.STOPWORDS = {"a", "an", "the", "is", "am", "are", "was", "were", "to", "of", "and", "in", "on", "for", "it"}

    def tokenize(self, text):
        text = text.lower()
        pattern = r'\w+'
        tokens = re.findall(pattern, text)
        return [t for t in tokens if t not in self.STOPWORDS]

    def lemmatizer(self, token):
        for lemma, forms in self.LEMMATIZER.items():
            if token in forms:
                return {token: (token, lemma)}
        return {token: (token, token)}

    def sentence_to_vector(self, sentence, idf=None):
        tokens = self.tokenize(sentence)
        lemmas = [self.lemmatizer(t).get(t, (t, t))[1] for t in tokens]
        vec = {}
        for t in lemmas:
            vec[t] = vec.get(t, 0) + 1

        # Apply TF-IDF weighting if IDF data exists
        if idf:
            for t in vec:
                vec[t] *= idf.get(t, 1.0)
        return vec

    def cosine_similarity(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[t] * vec2[t] for t in intersection)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot / (mag1 * mag2)

# -------------------------
# Supervised Intent-Based Bot
# -------------------------
class arcturusSUPERVISED_INTENT:
    def __init__(self, nlp_pipeline, intent_responses):
        self.nlp = nlp_pipeline
        self.intent_responses = intent_responses
        self.inputs = []
        self.intents = []
        self.vectors = []
        self.idf = {}

    def compute_idf(self, dataset):
        """Compute IDF values for TF-IDF weighting."""
        doc_count = {}
        total_docs = len(dataset)
        for sent, _ in dataset:
            tokens = set(self.nlp.tokenize(sent))
            for t in tokens:
                doc_count[t] = doc_count.get(t, 0) + 1
        for t, c in doc_count.items():
            self.idf[t] = math.log((1 + total_docs) / (1 + c)) + 1

    def train(self, data):
        self.inputs = [inp for inp, intent in data]
        self.intents = [intent for inp, intent in data]
        self.compute_idf(data)
        self.vectors = [self.nlp.sentence_to_vector(inp, self.idf) for inp in self.inputs]

    def predict_intent(self, sentence, show_scores=False):
        vec = self.nlp.sentence_to_vector(sentence, self.idf)
        scores = []
        for i, v in enumerate(self.vectors):
            sim = self.nlp.cosine_similarity(vec, v)
            scores.append((self.intents[i], sim))
        # Pick best scoring intent
        scores.sort(key=lambda x: x[1], reverse=True)
        if show_scores:
            print("Intent similarity scores:", scores)
        return scores[0][0] if scores else "unknown"

    def get_response(self, sentence):
        intent = self.predict_intent(sentence)
        responses = self.intent_responses.get(intent, ["I don't understand."])
        return random.choice(responses)

# -------------------------
# Example Usage
# -------------------------
if __name__ == "__main__":
    nlp = arcturusNLP()

    # Training data: (user_input, intent_tag)
    training_data = [
        ("hi", "greeting"),
        ("hello", "greeting"),
        ("hey", "greeting"),
        ("how are you", "greeting"),
        ("bye", "goodbye"),
        ("see you later", "goodbye"),
        ("tell me a joke", "joke"),
        ("make me laugh", "joke"),
        ("thanks", "thanks"),
        ("thank you", "thanks"),
        ("what's your name", "identity")
    ]

    # Intent responses
    intent_responses = {
        "greeting": ["Hello!", "Hey there!", "Hi! How can I help you?"],
        "goodbye": ["Goodbye!", "See you later!", "Bye!"],
        "joke": ["Why do programmers prefer dark mode? Because light attracts bugs!"],
        "thanks": ["You're welcome!", "No problem!", "Anytime!"],
        "identity": ["I'm Arcturus, your AI assistant."]
    }

    bot = arcturusSUPERVISED_INTENT(nlp, intent_responses)
    bot.train(training_data)

    # Chat loop
    print("🤖 Arcturus NLP Bot v0.2.0 | Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Bot: Goodbye!")
            break
        print("Bot:", bot.get_response(user_input))
