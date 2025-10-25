class BengaliBPE:
    def __init__(self, num_merges=10):
        self.num_merges = num_merges
        self.bpe_codes = {}
        self.vocab = {}

    def build_vocab(self, corpus):
        vocab = {}
        for line in corpus:
            words = line.strip().split()
            for word in words:
                token = ' '.join(list(word))
                vocab[token] = vocab.get(token, 0) + 1
        return vocab

    def train(self, corpus):
        self.vocab = self.build_vocab(corpus)
        for i in range(self.num_merges):
            pairs = self.get_stats(self.vocab)
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            self.bpe_codes[best] = i
            self.vocab = self.merge_vocab(best, self.vocab)

    def get_stats(self, vocab):
        pairs = {}
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pair = (symbols[i], symbols[i + 1])
                pairs[pair] = pairs.get(pair, 0) + freq
        return pairs

    def merge_vocab(self, pair, vocab):
        new_vocab = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)
        for word, freq in vocab.items():
            new_word = word.replace(bigram, replacement)
            new_vocab[new_word] = freq
        return new_vocab

    def get_pairs(self, word):
        symbols = word.split()
        pairs = set()
        for i in range(len(symbols) - 1):
            pairs.add((symbols[i], symbols[i + 1]))
        return pairs

    def encode_word(self, word):
        word_with_spaces = ' '.join(list(word))
        while True:
            pairs = self.get_pairs(word_with_spaces)
            merge_candidates = {
                pair: self.bpe_codes.get(pair, float('inf')) for pair in pairs if pair in self.bpe_codes
            }
            if not merge_candidates:
                break
            best = min(merge_candidates, key=lambda pair: merge_candidates[pair])
            pattern = ' '.join(best)
            replacement = ''.join(best)
            word_with_spaces = word_with_spaces.replace(pattern, replacement)
        return word_with_spaces.split()

    def encode(self, text):
        words = text.strip().split()
        encoded_sentences = []
        for word in words:
            encoded = self.encode_word(word)
            encoded_sentences.append(encoded)
        return encoded_sentences

    def decode(self, encoded_words):
        decoded_words = [''.join(tokens) for tokens in encoded_words]
        return ' '.join(decoded_words)
