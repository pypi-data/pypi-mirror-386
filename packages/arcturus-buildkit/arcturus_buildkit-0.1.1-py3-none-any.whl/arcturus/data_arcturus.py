POS_LOOKUP = {
    # Pronouns
    "PRON": {
        "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
        "myself", "yourself", "himself", "herself", "itself", "ourselves", "yourselves", "themselves",
        "who", "whom", "whose", "which", "that", "anyone", "everyone", "someone", "noone", "nobody", "anybody",
        "each", "either", "neither", "one", "nothing", "something", "everything"
    },

    # Possessive Pronouns
    "PPRON": {
        "my", "your", "his", "her", "its", "their", "our", "mine", "yours", "hers", "ours", "theirs"
    },

    # Articles
    "ART": {"a", "an", "the"},

    # Determiners
    "DET": {
        "this", "that", "these", "those", "each", "every", "some", "any", "no", "enough", "all", "both",
        "several", "many", "few", "other", "another", "such", "certain", "what", "which", "whose"
    },

    # Nouns (over 200 common nouns)
    "NOUN": {
        "time", "person", "year", "way", "day", "thing", "man", "world", "life", "hand", "part", "child",
        "eye", "woman", "place", "work", "week", "case", "point", "government", "company", "number", "group",
        "problem", "fact", "school", "state", "family", "student", "story", "job", "word", "business", "issue",
        "side", "house", "water", "room", "mother", "area", "money", "friend", "health", "personality", "mind",
        "idea", "city", "game", "song", "team", "dog", "cat", "computer", "phone", "car", "food", "movie",
        "river", "mountain", "ocean", "question", "answer", "day", "night", "month", "year", "life", "dream",
        "chance", "event", "activity", "plan", "goal", "effort", "relationship", "society", "culture", "language",
        "history", "art", "music", "law", "order", "lawyer", "court", "teacher", "student", "book", "volume",
        "idea", "decision", "move", "love", "hate", "rain", "coffee", "light", "job", "school", "childhood",
        "friendship", "holiday", "vacation", "trip", "experience", "adventure", "risk", "opportunity", "problem",
        "solution", "lesson", "story", "conversation", "discussion", "debate", "plan", "strategy", "approach",
        "method", "system", "process", "project", "task", "effort", "goal", "purpose", "function", "feature",
        "tool", "device", "technology", "software", "hardware", "internet", "network", "website", "application",
        "game", "level", "score", "player", "team", "match", "competition", "tournament", "award", "prize",
        "festival", "event", "celebration", "holiday", "season", "weather", "temperature", "rain", "snow",
        "storm", "wind", "sun", "moon", "star", "planet", "universe", "galaxy", "space", "time"
    },

    # Verbs (over 200 common verbs)
    "VERB": {
        "be", "am", "is", "are", "was", "were", "been", "being",
        "have", "has", "had", "do", "does", "did", "say", "says", "said", "go", "goes", "went", "gone",
        "can", "could", "will", "would", "shall", "should", "may", "might", "must",
        "get", "gets", "got", "make", "makes", "made", "know", "knows", "knew", "think", "thinks", "thought",
        "take", "takes", "took", "see", "sees", "saw", "come", "comes", "came", "want", "wants", "wanted",
        "use", "uses", "used", "find", "finds", "found", "give", "gives", "gave", "tell", "tells", "told",
        "work", "works", "worked", "call", "calls", "called", "try", "tries", "tried", "ask", "asks", "asked",
        "need", "needs", "needed", "feel", "feels", "felt", "become", "becomes", "became", "leave", "leaves",
        "left", "put", "puts", "keep", "keeps", "kept", "let", "lets", "begin", "begins", "began", "seem",
        "seems", "seemed", "help", "helps", "helped", "talk", "talks", "talked", "turn", "turns", "turned",
        "start", "starts", "started", "show", "shows", "showed", "hear", "hears", "heard", "play", "plays",
        "played", "run", "runs", "ran", "move", "moves", "moved", "live", "lives", "lived", "believe", "believes",
        "believed", "hold", "holds", "held", "bring", "brings", "brought", "write", "writes", "wrote", "read",
        "sit", "sits", "sat", "stand", "stands", "stood", "lose", "loses", "lost", "pay", "pays", "paid",
        "meet", "meets", "met", "include", "includes", "included", "continue", "continues", "continued",
        "set", "sets", "learn", "learns", "learned", "change", "changes", "changed", "lead", "leads", "led",
        "understand", "understands", "understood", "watch", "watches", "watched", "follow", "follows", "followed",
        "stop", "stops", "stopped", "create", "creates", "created", "speak", "speaks", "spoke", "listen", "listens",
        "listened", "read", "reads", "study", "studies", "studied", "travel", "travels", "traveled", "open", "opens",
        "opened", "close", "closes", "closed", "win", "wins", "won", "lose", "loses", "lost", "move", "moves",
        "moved", "play", "plays", "played", "run", "runs", "ran", "jump", "jumps", "jumped", "sleep", "sleeps",
        "slept", "drive", "drives", "drove", "driven"
    },

    # Auxiliary Verbs
    "AUX": {
        "am", "is", "are", "was", "were", "be", "been", "being",
        "do", "does", "did",
        "have", "has", "had"
    },

    # Modal Verbs
    "MODV": {"will", "can", "should", "would", "may", "might", "must", "shall", "could", "ought"},

    # Adjectives (over 150 common adjectives)
    "ADJ": {
        "good", "bad", "big", "small", "heavy", "light", "fast", "slow", "happy", "sad", "angry", "calm",
        "bright", "dark", "hot", "cold", "strong", "weak", "new", "old", "easy", "difficult", "interesting",
        "boring", "tall", "short", "beautiful", "ugly", "smart", "stupid", "rich", "poor", "young", "friendly",
        "hostile", "clean", "dirty", "early", "late", "modern", "ancient", "simple", "complex", "safe", "dangerous",
        "quiet", "loud", "funny", "serious", "bright", "dark", "cold", "warm", "hard", "soft", "creative",
        "lazy", "busy", "hungry", "thirsty", "brave", "cowardly", "curious", "shy", "polite", "rude", "healthy",
        "sick", "beautiful", "ugly", "unique", "famous", "infamous", "strong", "weak"
    },

    # Adverbs (over 150 common adverbs)
    "ADV": {
        "quickly", "slowly", "well", "badly", "happily", "sadly", "angrily", "brightly", "quietly",
        "loudly", "easily", "hardly", "fast", "recently", "soon", "always", "never", "often", "sometimes",
        "now", "then", "here", "there", "yesterday", "today", "tomorrow", "inside", "outside", "upstairs",
        "downstairs", "away", "back", "together", "apart", "almost", "already", "actually", "eventually",
        "certainly", "probably", "possibly", "generally", "usually", "rarely", "finally", "immediately"
    },

    # Conjunctions
    "CONJ": {
        "and", "or", "because", "for", "so", "if", "although", "but", "yet", "while", "nor", "since", "as",
        "even", "though", "whereas", "once", "until", "unless"
    },

    # Prepositions
    "PREP": {
        "in", "on", "at", "by", "with", "under", "over", "to", "from", "into", "between", "through", "across",
        "about", "against", "during", "without", "within", "among", "behind", "beyond", "near", "above", "below",
        "beside", "along", "past", "toward", "upon", "off", "out"
    },

    # Interjections
    "INTJ": {"wow", "oh", "hey", "ouch", "huh", "ah", "oops", "yikes", "yay", "ugh", "bravo", "hurray", "alas"},

    # Numerals
    "NUM": {
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"
    },

    # Punctuation
    "PUNCT": {"!", ".", ",", "?", ":", ";", "-", "(", ")", "[", "]", "{", "}", "\"", "'", "..."}
}

ABBREVIATIONS = {
    "US": "United States",
    "UK": "United Kingdom",
    "UAE": "United Arab Emirates",
    "PK": "Pakistan"
}

LEMMATIZER = {
    "walk": ["walker", "walking", "walks", "walked"],
    "sit": ["sit", "sat", "sitting"],
    "use": ["use", "uses", "using", "used"],
    "pakistan": ["pakistani"]
}

FORMS_WORDS = {
    "VERB": [["walk", "walking", "walked", "walks"], ["sit", "sat", "sitting"], ["use", "uses", "using", "used"]],
    "NOUN": [["walk", "walks"], ["dollar", "dollars"]]
}
SYNONYM = {
    "fast": ["speedy", "quick"]
}

SYNONYM_NGRAM = {
    ("the", "car"): [("the", "vehicle")],
}
