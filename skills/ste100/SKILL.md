---
name: ste100
description: Write or rewrite text in ASD-STE100 Simplified Technical English - the aerospace maintenance-manual standard Karpathy recommends asking LLMs for because the output is much easier to read. Short sentences, one meaning per word, active voice, one instruction per sentence. Has a strict mode (real STE) and a relaxed mode (the readable core, for docs, explanations, and narration). Use when the user says "/ste100", "STE", "simplified technical English", "aircraft manual style", "write it like an aviation manual", "the Karpathy writing style", "make this easier to read", or asks for docs, procedures, or explanations that must be unambiguous.
---

# ste100

ASD-STE100 is a controlled language for technical writing.
It was made for aircraft maintenance manuals, where readers are often not native English speakers and a misread step is dangerous.
Its rules remove ambiguity, so text becomes faster to read for everyone.
Andrej Karpathy suggested asking models for it: models know it well, and the output is much more readable.

## Modes

- **relaxed** (default): apply the rules marked core below. Use for docs, READMEs, explanations, reports, and video narration.
- **strict**: apply every rule, including the dictionary rules. Use for procedures, runbooks, safety steps, or when the user says "strict" or "real STE".

State the mode in one line only when the user did not pick one and the choice matters.

## Core rules (both modes)

**Words**
1. **One word, one meaning.** Use "close" for close, not also "shut" and "secure". Pick one term for each thing and never change it.
2. **One meaning, one word.** Do not use a word in two senses ("set" as noun and verb, "check" as test and as mark).
3. **Simple, common words.** "use", not "utilize"; "start", not "initiate"; "help", not "facilitate"; "about", not "approximately".
4. **No phrasal verbs** when a single verb exists: "remove", not "take out"; "find", not "figure out"; "continue", not "keep on".
5. **Name the thing.** Use the noun again instead of "it", "this", or "that" when the reference could be unclear.
6. **No noun stacks** of more than three words. "the pressure valve of the fuel pump", not "fuel pump pressure valve assembly bolt".

**Sentences**
7. **Short sentences.** Procedures: 20 words maximum. Descriptions: 25 words maximum.
8. **One instruction per sentence.** Two actions at the same time may share one sentence.
9. **Active voice.** "The script writes the file", not "The file is written by the script". Passive is allowed only when the actor is unknown and unimportant.
10. **Instructions use the imperative.** "Open the panel." Not "You should open the panel" or "The panel should be opened".
11. **Keep articles and small words.** Do not drop "the", "a", "is" to save space. Telegraphic text is ambiguous.
12. **Use verbs, not nouns made from verbs.** "Install the unit", not "Do the installation of the unit".

**Structure**
13. **One topic per paragraph.** Six sentences maximum.
14. **Put the condition first.** "If the light is on, stop the pump."
15. **Warnings come before the step they apply to**, start with the command, and give the risk: "WARNING: Disconnect power before you open the case. The capacitor can hold a dangerous charge."
16. **Lists for steps and parallel items.** Number steps in order.

## Strict-only rules

17. **Verb tenses**: only simple present, simple past, simple future, and the imperative. Infinitive is allowed. Do not use "-ing" forms except as technical names and modifiers ("landing gear").
18. **Past participle** only as an adjective ("the damaged part") or with "is/are" in passive descriptions.
19. **Approved vocabulary only.** Prefer the STE approved word over its unapproved synonym: "to do", not "to perform"; "make sure", not "ensure"; "near", not "adjacent to"; "show", not "indicate"; "stop", not "terminate"; "get", not "obtain"; "large", not "big" (choose one and keep it).
20. **Technical names and verbs** for your domain are allowed (a part name, a command name). Keep them consistent.
21. **No contractions, no idioms, no figures of speech.**

## How to work

When you **write** new text: write it to these rules from the start.

When you **rewrite** text:
1. Keep every fact, number, name, and link. Simplify the language, not the content.
2. List the key terms first and pick one word for each. Use that word everywhere.
3. Rewrite. Split long sentences. Change passive to active.
4. Check each sentence against rules 7, 9, and 1. These three give most of the gain.
5. Give the result. Do not explain the changes unless the user asks.

## Example

Before:
> The configuration file should be updated prior to initiating the deployment process, as failure to do so may result in the service being brought up with stale settings that could potentially cause issues.

After (relaxed):
> Update the configuration file before you start the deployment.
> If you do not, the service starts with old settings, and these settings can cause errors.

After (strict):
> Update the configuration file before you start the deployment.
> CAUTION: If you do not update the file, the service starts with old settings. Old settings can cause errors.
