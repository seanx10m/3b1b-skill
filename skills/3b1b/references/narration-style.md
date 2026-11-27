# Narration style guide

Use this when you write `narration.txt`.
Each line is one TTS clip and shows as one subtitle.
The patterns come from measuring four 3Blue1Brown transcripts (neural networks ch1 and ch2, Fourier transform, essence of calculus ch1).
Copy the moves, never the sentences.

## Measured numbers

Source: about 14,500 words across 4 videos, 616 sentences.
Captions had light punctuation, so sentence counts are approximate.

| Metric | Measured | What to do with it |
|---|---|---|
| Speaking rate | 178 to 184 wpm (mean 182) | Fast and steady. Your TTS is slower, so budget by time, not words. |
| Sentence length, median | 20 words | His spoken sentences chain clauses. Do not copy that in clips. |
| Sentence length, 90th percentile | 38 words | Too long for one subtitle. Split. |
| Questions | about 5% of sentences | One question per 15 to 20 sentences. Rare, so each one lands. |
| "you / your" | 2.2 per 100 words (about 4 per minute) | Talk to the viewer, not about the topic. |
| "we / let's / our" | 1.2 per 100 words | Use "we" for shared work, "you" for what the viewer sees or feels. |
| "just" | 1.3 per minute | Softener. Keep it rare in your lines. |
| "let's" | 0.3 per minute | A step marker, not a tic. |
| "you might" | 0.3 per minute | Voices the viewer's guess before the answer. |
| "think about" / "imagine" / "picture" | 0.6 per minute combined | The invitation to build a mental image. |
| "kind of" / "sort of" | 0.45 per minute | Honest hedging on a loose analogy. |
| "remember" / "notice" | 0.2 per minute combined | Callback and spotlight. |
| "a lot" (admitting scale) | 0.26 per minute | Names the load, then simplifies. |

Takeaway: his voice is plain words, a direct "you", and few questions placed on purpose.
Signature phrases are sparse.
The feel comes from structure, not from catchphrases.

## Moves

### 1. Concrete case first
What it is: open on one specific thing the viewer can picture, not on a definition.
When to use: the first 2 to 3 lines of every video and every new section.
Example: "Your browser loads this same logo from the server forty times an hour."

### 2. Invite a picture
What it is: ask the viewer to build an image in their head before you show or name anything.
When to use: right before a visual appears.
Example: "Picture a coat check with a hundred numbered hooks."

### 3. The viewer's guess ("you might")
What it is: say the obvious guess out loud, then test it.
When to use: before a reveal, so the answer has something to beat.
Example: "You might think a hash map scans every key until it finds yours."

### 4. Pose the question, then pause
What it is: a short real question, then a hold, then the picture.
When to use: once per section at most, at the exact point the viewer wonders.
Example: "So how does it jump straight to the right slot?"

### 5. Spotlight ("notice")
What it is: tell the viewer where to look in the frame.
When to use: when an animation changes something small but important.
Example: "Notice the second request never leaves the machine."

### 6. Name it after you show it
What it is: let the viewer see and feel the idea, then attach the label in one short line.
When to use: every new term.
Example: "That shortcut has a name - a cache hit."

### 7. Honest load ("this is a lot")
What it is: admit the complexity, give one anchor, move on.
When to use: after a dense frame or a formula.
Example: "That is a lot of boxes, but only one of them matters here."

### 8. Callback ("remember")
What it is: point back to a thing you built earlier and reuse its color or shape.
When to use: when an old idea returns in a new form.
Example: "Remember the hooks? Now each hook holds a short list."

### 9. Shared work ("we")
What it is: "we" for steps the video does together, "you" for what the viewer sees.
When to use: derivations and builds.
Example: "We keep the newest result and drop the oldest."

### 10. Hedge a loose analogy ("kind of")
What it is: flag an analogy as rough so the viewer trusts the rest.
When to use: once, right after the analogy.
Example: "It is kind of a bouncer who remembers faces."

## Reveal recipe

1. Set up the puzzle in one concrete line.
2. Voice the obvious guess ("you might think ...").
3. Ask one short question, five to nine words.
4. Hold 1 to 2 seconds. No narration, the picture is still the old one.
5. Cut to the new picture. Say nothing for the first half second.
6. Give the answer in one short line, lead with the plain result.
7. Name the concept in a separate, shorter line.
8. Add one consequence line ("which means ...").

Check: the name of the concept must appear after the picture, never before.

## Pacing

- Line budget: 8 to 16 words. Hard cap 22. If a line needs a second "and" or "which", split it.
- One idea per line. One subtitle, one thought.
- Mix lengths. After two long lines, write a short one of 3 to 6 words.
- Hold 1 to 2 seconds before the key picture, after a question, and after a formula appears.
- Put a hold as its own empty beat in the timeline, not as "..." in the text.
- Never hold more than 2 seconds. Longer reads as a stall.
- Put the key word last in the line so the voice can lean on it.
- Condition first, result second: "When the key is already stored, we skip the work."
- Aim for 150 to 165 wpm in TTS. Slower than his 182, because subtitles need reading time.

## Things that break the voice

- Lecture-speak: "It is important to note that", "As we can see", "In this section we will". Say the thing.
- Passive voice: "The key is hashed by the function." Write "The function hashes the key."
- Naming before showing: "This is called a hash collision" before the viewer sees two keys land together.
- Stacked clauses: a line with two "which" or three commas. Split it.
- Stacked questions: two questions in a row. Ask one, hold, answer.
- Fake enthusiasm: "Amazing", "incredible", "super cool". Let the picture earn it.
- Reading a formula aloud symbol by symbol. Say what it does, show the symbols.
- Recaps in the middle of a section. Recap only at section ends, in one line.
- Calling the viewer "guys" or "folks", or announcing "in this video".

## Before and after

Dry draft:
1. "A cache is a component that stores frequently accessed data in order to reduce latency."
2. "When a request is received, the cache is checked first by the system."
3. "If the data is not found, it is retrieved from the database and stored."
4. "This process is referred to as a cache miss, and it results in increased latency."

Rewrite:
1. "Say a thousand people ask for the same page."
2. "Fetching it fresh a thousand times would be slow."
3. "So we keep the first answer close, and check there first."
4. "When it is not there, we pay the slow trip once. That is a cache miss."

What changed: concrete case before definition, passive to active, "you" and "we" appear, question-free but built as a guess-then-test, name comes after the picture, every line under 16 words.

## Gemini TTS delivery prompt

Voice: Iapetus.
Director's note: Read this like a curious friend thinking out loud beside the viewer, warm and unhurried, never a lecturer.
Keep a steady, gentle pace, and let a small smile come through on the plain lines.
Lift the pitch slightly on questions and on the moment a picture changes, and take a tiny breath before the key word of each line so it lands softly.
Drop to a quieter, slower tone for the admission lines ("this is a lot"), and never rush the last few words of a line.
