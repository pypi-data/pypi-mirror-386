import re
import math
import random
import data_arcturus

# -------------------------
# NLP Pipeline
# -------------------------
class arcturusNLP:
    def __init__(self):
        self.LEMMATIZER = data_arcturus.LEMMATIZER

    def tokenize(self, text):
        text = text.lower()
        pattern = r'\w+|[^\w\s]'
        return re.findall(pattern, text)

    def lemmatizer(self, token):
        for lemma, forms in self.LEMMATIZER.items():
            if token in forms:
                return {token: (token, lemma)}
        return {token: "not found :<"}

    def sentence_to_vector(self, sentence):
        tokens = self.tokenize(sentence)
        tokens = [self.lemmatizer(t).get(t, (t, t))[1] for t in tokens]
        vec = {}
        for t in tokens:
            vec[t] = vec.get(t, 0) + 1
        return vec

    def cosine_similarity(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot = sum(vec1[t]*vec2[t] for t in intersection)
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot / (mag1 * mag2)

# -------------------------
# Supervised Intent-Based Bot
# -------------------------
class arcturusSUPERVISED_INTENT:
    def __init__(self, nlp_pipeline, intent_responses):
        """
        intent_responses: dict of {intent_tag: [response1, response2, ...]}
        """
        self.nlp = nlp_pipeline
        self.inputs = []
        self.intents = []
        self.intent_responses = intent_responses
        self.vectors = []

    def train(self, data):
        """
        data: list of (input_sentence, intent_tag)
        """
        self.inputs = [inp for inp, intent in data]
        self.intents = [intent for inp, intent in data]
        self.vectors = [self.nlp.sentence_to_vector(inp) for inp in self.inputs]

    def predict_intent(self, sentence):
        vec = self.nlp.sentence_to_vector(sentence)
        best_sim = -1
        best_idx = 0
        for i, v in enumerate(self.vectors):
            sim = self.nlp.cosine_similarity(vec, v)
            if sim > best_sim:
                best_sim = sim
                best_idx = i
        return self.intents[best_idx]

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
        ("make me laugh", "joke")
    ]

    # Intent responses
    intent_responses = {
        "greeting": ["Hello!", "Hey there!", "Hi! How can I help you?"],
        "goodbye": ["Goodbye!", "See you later!", "Bye!"],
        "joke": ["Why do programmers prefer dark mode? Because light attracts bugs!"]
    }

    bot = arcturusSUPERVISED_INTENT(nlp, intent_responses)
    bot.train(training_data)

    # Chat loop
    print("🤖 Flame-Bot Intent Chat! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Bot: Goodbye!")
            break
        print("Bot:", bot.get_response(user_input))
