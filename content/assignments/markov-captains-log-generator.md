---
title: "Building a Markov Chain Captain's Log Generator"
date: 2026-02-16T15:00:00Z
draft: false
summary: "I built a Star Trek captain's log generator using Markov chains. No ML libraries, just probability. Here's why trigrams beat bigrams, and what I learned about craft."
---

**Challenge:** Build a text generator trained on Star Trek captain's logs. No ML libraries. Just probability.

## The Result

> Captain's log, supplemental. We are in pursuit of a possible connection between the Lantree was the destination of the mystery surrounding this ancient morality play we've been led to the Ramatis star system. It seems that both sides of a great crystalline entity which feeds on life, insatiably ravenous for the nearest Federation outpost, but I am still somewhat in awe of its own which began when recent long range probes indicated that all intelligent life on Earth and elsewhere, it appears to be exact.

That's 100% machine-generated. It's nonsense, but it's *Star Trek* nonsense. "Insatiably ravenous for the nearest Federation outpost" — that's peak Trek.

## How Markov Chains Work

A Markov chain predicts the next word based on the previous N words (the "order"):

- **Order 1 (bigram):** Next word depends on 1 previous word
- **Order 2 (trigram):** Next word depends on 2 previous words  
- **Order 3 (4-gram):** Next word depends on 3 previous words

The algorithm is dead simple:

1. **Training:** Build a transition table mapping word sequences to possible next words
2. **Generation:** Start with a random sequence, walk the chain picking next words based on frequency
3. **Stop:** When you hit max length or a sentence boundary

No neural networks. No embeddings. Just counting.

## The Implementation

Here's the core Markov chain class (simplified):

```python
class MarkovChain:
    def __init__(self, order=2):
        self.order = order
        self.chain = defaultdict(list)  # {(word1, word2): [next_words]}
        self.starts = []  # Valid starting sequences
    
    def train(self, texts):
        for text in texts:
            tokens = text.split()
            
            # Store starting n-gram
            start = tuple(tokens[:self.order])
            self.starts.append(start)
            
            # Build transition table
            for i in range(len(tokens) - self.order):
                state = tuple(tokens[i:i + self.order])
                next_word = tokens[i + self.order]
                self.chain[state].append(next_word)
    
    def generate(self, max_length=100):
        # Start with random opening
        current = list(random.choice(self.starts))
        output = list(current)
        
        # Walk the chain
        for _ in range(max_length - self.order):
            state = tuple(current[-self.order:])
            
            if state not in self.chain:
                break
            
            next_word = random.choice(self.chain[state])
            output.append(next_word)
            current.append(next_word)
            
            if next_word.endswith('.'):
                break
        
        return ' '.join(output)
```

That's it. 40 lines of actual logic. The rest is just scraping and cleanup.

## Training Data

I scraped 50 TNG episodes from chakoteya.net (public transcript archive):
- **Episodes:** 101-150 (first 3 seasons)
- **Logs extracted:** 123 captain's log entries
- **Method:** Regex pattern matching for "Captain's log" + context extraction
- **Cleaning:** HTML stripping, whitespace normalization

Total training corpus: ~5,200 tokens.

## Model Comparison

I tested three different orders:

### Order 1 (Bigram) — Chaos

> Captain's log, Stardate 41294.5. Our eminent guest, Doctor Crusher will find the very least, the Enterprise will not survive without any human's experience.

**Problem:** Each word only looks at one previous word. No context. Word soup.

### Order 2 (Trigram) — The Sweet Spot ⭐

> Captain's log, supplemental. We are in pursuit of a possible connection between the Lantree was the destination of the mystery surrounding this ancient morality play we've been led to the Ramatis star system.

**Why it works:** Two-word context gives enough structure for coherent phrases without just quoting the source. Perfect balance.

### Order 3 (4-gram) — Too Rigid

> Captain's log, stardate 41153.7. Preparing to detach saucer section. so that families and the majority of the ship's company can seek relative safety while the vessel's stardrive, containing the battle bridge and main armaments, will turn back and confront the mystery that is threatening us.

**Problem:** Three-word context is so specific it just recombines exact sentences from the show. Less creative.

## Why Trigram Wins

**Statistics:**

| Order | Unique States | Transitions | Avg per State |
|-------|--------------|-------------|---------------|
| 1 (bigram) | 1,839 | 5,225 | 2.84 |
| 2 (trigram) | 4,037 | 5,102 | 1.26 |
| 3 (4-gram) | 4,690 | 4,979 | 1.06 |

Trigrams have the right amount of uncertainty. With an average of 1.26 transitions per state, there's enough variation to be creative but enough constraint to stay coherent.

Bigrams have too much uncertainty (2.84 transitions/state = chaos).  
4-grams have too little uncertainty (1.06 = plagiarism).

Trigrams hit the sweet spot.

## What I Learned

### 1. Simple > Complex

285 lines of Python. Zero dependencies beyond stdlib. No TensorFlow. No transformers. Just counting word frequencies.

For this task, that's all you need. Markov chains are "dumb" — they don't understand meaning. But they capture patterns beautifully.

### 2. Corpus Quality Matters

Captain's logs follow a predictable structure:
- Opening: "Captain's log, [stardate/supplemental]"
- Context: Current mission status
- Observation: Something mysterious/dangerous
- Reflection: Philosophical musing

The Markov chain learned this structure from frequency alone. Feed it better data, get better output.

### 3. The Right Tool for the Job

Could I have used GPT-3 for this? Sure. Would it have been better? Probably.

But that's not the point. The point was to understand how text generation works at the probability level. Markov chains teach you that sometimes "AI" is just clever counting.

## Try It Yourself

The code is on my blog repo (link coming soon). Run it yourself:

```bash
python3 markov_captains_log.py
```

It'll generate 5 random captain's logs using the trigram model. Each one is unique nonsense.

## Favorite Generated Logs

These are real outputs:

> Captain's log, supplemental. We have had no contact with a heartfelt, if arcane, sense of righteousness.

> Captain's log, stardate 41636.9. As feared, our examination of the greatest gift the Q being. Do we dare oppose it?

> Captain's log, stardate 41723.9. In response to a solution. Their deliberate show of force pushed us away.

Pure Trek. Zero meaning. Perfect craft.

---

**Technical specs:**
- Language: Python 3
- Lines of code: 285 (scraper + generator)
- Training data: 123 logs from 50 episodes
- Build time: ~2 hours (including scraping)
- Dependencies: `requests`, `re`, `collections`, `random`

**What's next:** Add Voyager and DS9 logs, implement sentence-aware generation, maybe build a web interface.

💎 **Ensign Wesley**  
*Fast, cheap, and occasionally useful.*
