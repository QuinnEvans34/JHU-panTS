# Audience Notes — Week 1 Pitches

**M1P1 audience deliverable.** Fill one block per presentation I observe. Goal: notes for *every* presenter, and at least **2 meaningful questions** asked across all pitches — probing business relevance, data validity, technical feasibility, or scope realism (not surface-level / yes-no).

> Reminder of what a *good* question looks like: "How will you prevent the same patient's scans landing in both train and test?" · "Your data isn't real-time — does that limit the business use?" · "What's your fallback if the model can't beat the majority-class baseline?"

---

## Presentation 1 — TED 
**Summary (2–3 sentences):**
Teds project is focusing on computer vision to control a video game. He wants to use machine learning to identify different hand gestures to control five nights at freddies. He has a large dataset he is going to use to train a CNN on hand signals. And plans to interface with the game through controlling inputs on his laptop, rather than specifically inputing into the game.

**Question(s) I asked:**
I asked him what type of machine learning model he is going to use, what dataset he is planning to use, and then how he plans to train the model on images and then have it produce meaningful feeback when responding to videos. I also asked him how he plans to interface with the game, I was not sure exactly how he was going to do this, and thought moving the mouse might not be the way I would approach it.

**Strength:** (what's strong about this proposal)
I think the approach to using image net to classify the hand movements is very smart, I feel that he will be able to get a lot of accuracy with the hand signals becuase they seem to be very distinct, and because of this, the CNN should be able to really understand the movements he is making. I also think it is smart to use transfer learning, this should spead up the process a lot, and allow him to really fine tune the project to his exact expectations.

**Risk / unclear:** (what's risky, underspecified, or unconvincing)
I think there are two things that my be risky, one stems from the image classification. I think there could be some hiccups when using a model that is trained on images on video, and that the latency may become a problem down the line. If it is taking 15 images per second, and has to process each of these, I am not sure if the speed will match the input of information. I also think there could be some hurdles when it comes to interfacing with his laptop directly to play the game. So I will be excited to see how he pulls this off.
---

## Presentation 2 — Gracie
**Summary (2–3 sentences):**
Gracie is working on an earthquake dataset, where she is going to use three different locations, to train one model. She is worried about the overfitting that comes with training a ML model on one location, and so she has decided to diversify the dataset into more than one location, to ensure that she can find strong patterns between the three locations.

**Question(s) I asked:**
I was curious what type of ML model she wanted to use, and I was also curious on how granular the dataset is, and what features she is going to be feeding to the model. I also asked her why she chose to train one model on more than one location, rather than one model per location becuase I was curious about this appraoch as well.

**Strength:**
I did not think this was a strength at the begining of the presentation, but by the end I could really see the thinking behind training one model on more than one location to ensure there is no data bias and that the dataset allows the model to pick up on real patterns. But, to be clear, I also think this is the main risk with the project. I think choosing to use locations like Japan and California and Greece was a great decision though, they seem to have regular earthquakes, which would make for a cleaner dataset.

**Risk / unclear:**
The main risk that I see is stretching the data too thin, if there are clear patterns in geological locations, it seems like getting rid of these clear patterns could lead to lower accuracy, becoming a detriment to the model in an attempt to reduce over fitting. But, on the other hand, the other clearest risk is overfitting, by the nature of the project there seem to be a much larger percent of days with no earthquakes than with them, so overfitting is sort of the nature of the beast when it comes to this kind of split.
---

## Presentation 3 — Porter
**Summary (2–3 sentences):**
Porter indends to create a story plot breakdown, using an XGBoost model to pick out key portions of a script, using a book called "Plot". To do this, he plans to use NLP to do feature extraction, and train a ML model based on the appearence of the key plot structure in the story. He plans to use scripts from popular movies sourced by IMDB, and he mentioned that he had access to annotated scripts, but towards the end said they may not be usable.

**Question(s) I asked:**
I was curious about the user experience of his project. I asked him what type of target variable/s he may or may not have. He said there would be multiple, that include breakdowns of each portion of the script, where it lines up with the architecture described in "plot" and then a score on how high it scored.

**Strength:**
I think he came up with a really cool project, and I thought it was cool to watch him try to make sense of a really abmiguous problem, using scripts, and then creating some sort of measerable metrics that he could use to feed to the ML model. I also thought it was great that he looked into different datasets, I know from his presentation he mentioned at least 3 datasets, and outside of class I have heard about two more datasets that were not mentioned inside the presentation.

**Risk / unclear:**
There are a few things that I think are a little unclear, I am not sure exactly how he is going to go about feature extraction, and how he is going to feed quantifiable features to a ML model. I am not completely sure how he is going to use natural language, and come up with a way to predict measurements specifically from unstructured data like language. 

---

<!-- Duplicate the block above for each additional presenter. -->

## Self-check before submitting
- [ ] A block for every presenter I observed.
- [ ] At least 2 substantive questions recorded (and actually asked in class).
- [ ] Each block has a specific strength AND a specific risk — not generic praise.
