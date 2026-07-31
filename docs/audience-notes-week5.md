# Audience Notes — Week 5 Final Demos & Defense

**M5P1 audience deliverable.** This is the final peer review. Fill one block per presentation I observe. Each block needs a summary, the questions I asked, an assessment of **system integration** and **business value**, and one question framed the way a **hiring manager** would ask it.

**Rubric reminders:**
- *Question Quality* — questions must be substantive and specific, probing system integration, business credibility, model limitations, or what the presenter would do differently. **At least one question across the session must be framed as a hiring manager would ask it.**
- *Notes Quality* — analytical and specific throughout, for every presenter. Not surface-level.

> **What a good question looks like this week:** "When you clicked predict, did that hit a live model or a saved file?" · "What happens to your pipeline if the input data changes format next month?" · "Your metric looks strong — what does it look like on the cases you didn't cherry-pick?" · "If I handed you this repo on Monday, what would break first?"
>
> **Hiring-manager framing** means asking what you'd ask if you were deciding whether to hire them: about ownership, judgment under constraint, and what they'd do differently — not just about the tech. e.g. "Which decision on this project would you defend hardest in a code review, and which one would you undo?"

---

## Presentation 1 — Ted
**Summary (2–3 sentences):**
Ted chose to make an application that allowed him to interface with a video game "Five nights at freddy's". He chose to use a machine learning model, a CNN to classify and predict different hand gestures that could be used to interface with the game. He then went from training 8 classes to 2 classes, which became a binary yes or no in terms of clicking on a page. He also had to add a new feature that allowed him to move his cursor using his hand. 

**Question(s) I asked:**
I wanted to know if the cursor tracking on his hand came from a machine learning model, or if it was just tracking his hand and using math to coordinate where his hand location is. He responded saying it was a machine learning model, and that it uses the hand tracing and anchor cords to locate exactly where the cursor should go.

**System integration** — does it feel genuinely end-to-end, or stitched together? (Did real data flow through to a visible prediction? Did the pipeline, model, and UI look like one system or three separate demos?)
It does feel end to end, and I think that was the strongest part of the project. Every part of the project was used to make the project work faster, and make better predictions. So, the project in terms of architecture, and how they work together, seems to be very strong. One thing that stands out to me though, is it seems the first model that he trained was used for hand signals, but then it had little to no effect on the final project.

**Business value** — is it clearly communicated and credible? (Could a non-technical person explain what this does and why it matters? Is the claimed value believable?)
Yes, I think a non technical person could definately understand what the project is doing, and how you can use it. I dont think a non technical person could understand the architecture behind it. But the basic idea of how it works, how it was made, and what everything does. 

**Hiring-manager question:** (what I'd ask if I were evaluating them for a role)
If I were evaluating him for a role I would want to know the exact limitations of his application, and what he would do to take the application to the next level. I would want to know if he had looked into this, and if he knew how he could make this better, if it were hardware, a more robust system, or what would make this work better.

---

## Presentation 2 — Porter
**Summary (2–3 sentences):**
Porter made a script analyzing pipeline that would analyze a script and predict turning points, emotion, and key scenes in the script. The purpose of this application is to help writers understand what parts of their stories may drag, and how they line up with principals that have already been agreed on in Hollywood, and have been applied from the book called "story". He would take in a script, and analyze the different scenes, to then output key points, what they mean to the story, and had checks that a writer could go through to understand the scope of the writing.

**Question(s) I asked:**
I wanted to know if he felt at the end of this project if he was able to get it to a point that he felt he was able to extract information and features from ambiguous data. Going into the assignment, I knew that analyzing something qualitative and text based makes it hard to extract features that can be used for predictions and analysis. So, I wanted to know if he felt that he found a solution to this problem, and was able to take data that is hard to score, and make some sort of meaning from it. His answer was realy solid as well, I agreed with what he said, he said that in hind-sight looking at one specific concept would have made more sense becuase it would have been more specific and measurable, but that he felt he was able to extract meaning, specifically from scripts that were hand annotated.

**System integration** — does it feel genuinely end-to-end, or stitched together?
Yes, I think his project seems to be structured well, and feels end to end. I honestly was impressed with the metrics that he was able to get with the approach that he took. All of the predictions and metrics directly line up with key features that are measured and looked for by script writers. And, I think this is what really makes it feel end to end. There is a source of truth, for specific features that are important to scripts, and the pipeline is designated to measure them specifically. I also will admit I did not think this until later on in the course, but with this final presentation I felt the system was well rounded in a way that I did not see before. The only weaknesses that I saw came from explanations of the work, I did not follow a few things, but the UI and work its self looked coherant and clear.

**Business value** — is it clearly communicated and credible?
Yes, I think he was clear in what the purpose of the project was, and I think he came from a background that understood the concepts better than any one else in the class room. So, he was able to speak some of the "jargon" that people in this field would have been looking for, which made it feel valuable for its specific use case. I also think almost all of the points and portions of the project were clearly communicated, but there were some places where the code and stats behind it became fuzzy at times when answering questions. So, the presentation was very clear, and the project was well rounded, but some times his answers to questions I did not know if he completely understood how they were being computed.

**Hiring-manager question:**
If I were hiring him, or wanted to use his application, I would want to know more about how he is analyzing the scenes. I would want to know why he chose the models that he used, and why he chose them. So, I would want to see and understand what he chose to use, and why, so I could trust it more, and trust that he understood the choices that were made.

---

## Presentation 3 — Gracie
**Summary (2–3 sentences):**
Gracie made an earthquake prediction pipeline, that use airstream to bring in live data, and score it on the next 7 days. She built this model on three locations, California, Greece, and Japan. And made predictions in boxes of 110 KM inside each of the regions. She created a UI on top of this model to display different predictions, where they will be, how confident the model is, and then how many earth quakes have occured in the past 7 days and the past month. She used an XGBoost model for the predictions, and saved the data to SQL lite for local storage inside of the project.

**Question(s) I asked:**
I wanted to know what she made her UI in, because it looked like streamlit, but I thought she had mentioned she was going to use react. I was just curious what she ended up using. I also wanted to know how she was getting predictions outside of state boarders, she is getting some data from Nevada and New Mexico, as they effect the earthquakes in California specifically, and then from earth quakes in the ocean for countries like Japan.

**System integration** — does it feel genuinely end-to-end, or stitched together?
Yes, I feel that her project was end to end. I think it looks a lot better from the project that she presented last, and this is why I feel this way. I thought she had some holes, I thought training three different models would have made sense, and that making one prediction per region would be harder as well. But, in the final presentation she addressed some of these issues, I still am not sure if three models on three regions would have been a stronger approach, and acknowledge she worked on this project and I did not, and that her approach could have been much better. But, I felt there were some places I would have used a different approach. Overall, however I think she had an end to end project, specifically in the flow of the architecture. She included DAG, used airstream to pull data live, which was something no one else in the class did. You could argue Ted is pulling in live data for his project, but she had it set up in the most official way. I still think there are some places that could be strengthened, but also know that we were on a time restraint, and think that contributed to a lot of it.

**Business value** — is it clearly communicated and credible?
Yes, I think the business value was stated clearly. She based this around first responders, and it made a lot of sense for this use case. I also think with the changes that she made this week, it was much stronger. Having one signal for an earthquake for the entire state of California would be hard to justify every first responder must prepare. So, I think the boxes inside of each region made this much stronger. I also think her presentation was very strong, and it outlined everything needed for a business use case to be justified. There were a few places that I was not completely confident in her explanations and answers to questions. But, other than that, I think it was a solid presentation.

**Hiring-manager question:**
If I were a hiring manager, I would want to know more about the training process, why she chose her model, how it would compare to other models, why she chose to have one model for three regions, and how this effects her training and predictions. So, I would want to know more about the model in question, and know why she made the choices that she made. I think I would be able to learn a lot about the project, and the process that she went through during the class. Which would lead to more confidence in her and her work, or lead to more questions that I could ask to see where her understanding is limited.

---