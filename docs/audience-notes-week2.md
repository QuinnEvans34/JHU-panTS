# Audience Notes - Week 2 Data Understanding Presentations

M2P2 audience deliverable. Fill one block per presentation I observe. Goal: notes for every presenter, with at least a couple of meaningful questions asked across the set. The Week 2 focus is different from Week 1: I am specifically judging whether each presenter's EDA findings actually justify their modeling decisions, whether their revised requirements and schedule are specific and achievable, and how they handled data-quality issues.

What a good Week 2 question looks like: "You found the classes are imbalanced, so how does your sampling or loss actually account for that?" or "You dropped those rows as anomalies, how did you decide they were bad and not signal?" or "Your revised schedule looks tight, what is the first thing you cut if you fall behind?"

---

## Presentation 1 - Gracie
Summary (2 to 3 sentences):
She is making an earthquake risk forecasting model, which will predict out to the next week. She is using a USGS dataset, which is live, requiring a live data processing pipeline. She is gathering data from three regions, California, Japan, and Greece, which much different data between the regions, especially in terms of magnitude. She is planning to take in data every couple of days, and plans to use one model to train on all three regions, to make predictions. 

Question(s) I asked: I asked a follow up question from last week, I was curious if she had any new information on why one model would perform better than 3 models, one per location. I also asked a follow up question on her answer, where she alluded to time being the biggest concern, and why she is choosing to train one model. I also asked a question about the distance from fault line, and if she was going to include this with the region, longitude, and latitude, I was also curious if this was data that came with the dataset or was feature engineered by her.


Does the EDA justify the modeling plan? (the required assessment)
I think she did a great amount of analysis into the dataset, more than I would have expected, and she also included some visualizations on exactly what each region looks like, and the magnitude vs consistency of earthquakes. So, overall here analysis seemed strong, I think choosing one model could be a good choice, but I also was not sure if her analysis backed this up, which is the one concern that I have for the project. She did provide some evidence based on time, meaning it might not be plausible to train three models when training one model may take too much time. Overall, I think she had a strong understanding of the data its self, with some room for more analysis when it comes to the model and the features she will be feeding to it.

Strength:
The main strength was her EDA, it seemed that she had a large amount of visualizations and P value based on the relationship between features. This made a strong case for her project, because the information she demonstrated had data to back it up.

Risk / unclear:
There were a few things, I think more research into model selection and choosing if she is going to train one model vs three would make me feel a little more confident in her project. Then, there were a few things with the input features, like putting 24 hours into the model, which she called 25 days, and said "this doesnt make sense" so this made me feel that she might have not looked into the input features as much as the relationships between the variables.

---

## Presentation 2 - Ted
Summary (2 to 3 sentences):
Ted is training a model to detect hand signals, and predicting labels based on the hand signals. He has a substantial amount of different labels(18 features to be exact), such as thumbs up, palm, ok, etc based on the way the hand is being moved and held in a static pose. He has a few approaches that he is considering such as using two models, one to zoom in on the hand, and one to find the gesture, and then predict from there. From the past presentation he mentioned this will be used to interface with a video game, but this was not mentioned specifically during the presentation. 

Question(s) I asked:
I wanted to know how he was processing the images, and if he was going to be doing this live. He told me the images are already labeled, so he is able to transform the data before the images are passed to the ML model. I was also curious how fast the model would be able to predict hand signals/gestures, because if you are going to be playing a game it would have to ingest and predict quickly for UX. I also asked if he had enough signals in the dataset to interface with the game. 

Does the EDA justify the modeling plan?
I think he has a decent amount of EDA, and has done research on the project its self. I know from speaking to him through out the course he has a good outline on what he wants to do. But I did not necessarily feel this way during his presentation. I think he has a very viable project outline, and scope, but I am also not fully confident that he will have a fully operational project by the end of the course, if I am being completely honest.

Strength:
I think his main strength is the dataset that he chose, he seems to have a large dataset, with lots of information, and excellent labeling, in terms of the locations of gestures, composition of the images, and preprocessing pipeline. So, overall, I think the biggest strength he has is his dataset, which would turn into a great outline for the project if he is able to turn this into a clear input for a live model. I also think his greatest strength was the answers to questions, after asking him more questions I seemed much more confident in his project overall, when compared to listening to the presentation.

Risk / unclear:
I think the main risk stems from the live model, and how he is going to get from images with hand gesture, training a model, to identifying the image live, to interfacing with a game. I think he has a great outline for how he is going to set up the model, but the risk comes in with interfacing with the game live and having a model that is accurate enough that he could interact with it in a way that simulates playing the game with your hands.

---

## Presentation 3 - Porter
Summary (2 to 3 sentences):
Porters project is based around Hollywood scripts, he is making a deep learning tool that is going to read screenplays and identify labels based on the structure of plots/movies. He has 28 emotions that he can detect of a given text or script, where he will utilize this to label and predict and evaluate different scripts. This will help automate reading scripts and valuating how profitable they could potentially be.

Question(s) I asked:
I was curious why he chose to use an LSTM, and why he chose to use a BI-LSTM, and what the BI means. So, I was curious about what model he was choosing to use, and why. Then I had a comment, more of a question, based on the understanding of his presentation, and the questions that were being asked, I said that I thought the language model was being used to get a sentiment more than anything else.

Does the EDA justify the modeling plan?
I think the EDA did justify the modelling plan. It seemed like Porter had good data, and has the ability to make a good project, but the thing that was lacking was the evidence on how we was going to use it. Which, could be fine, if we are working to train the models in week 3, but he still might be a little behind compared to the other presentations when it comes to the actual application of the data. So, I think he has enough data, enough useful data, but he has some room to improve on how he is going to actual use it. This is the only place that I think has clear weaknesses in his plan. 

Strength:
I think he did a great job at outlining the project, during his presentation I understood what the overall goal was, and what he was working with, I liked the slides that he had because they seemed to make his argument stronger. I also think the data that he has works for the project that he is working on, so that is a strength as well. But I still think there is something else there, that has not been completely thought through, or a final decision on the architecture to understand the exact scoping of the project.

Risk / unclear:
If I am being honest, I think he had a great presentation, that made sense, but when it came to questions, it seemed like he did not have answers to a few key points of the project. So, in terms of risks, I think this is clear and present. So, it sounds like a good idea, I am just not sure if it is completely been scoped out and planned out. This becomes a risk, because if you are deeper into the project like we are at this point, if everything has not been scoped out, you cannot be certain that the final product will be tangible, and perform as expected. I know from my experience, I have already had some curve balls in my project, but I had already planned accordingly, so if the plan is not there, you may not be able to bounce back from adversity. I also think, and this is just my opinion, that leaning heavily on deep learning models, or LLMs might be the only approach to this project that works. Last week he did not want to use deep learning, this week he proposed a mini language model, and a BI-LSTM, which I think is a great approach, but with the nuance that comes with text, using deep learning/LLMs, might be the only way to structure the project, using many models, for sentiment analysis, coming up with clear features that you can engineer, and ways to fit the structure of the class, may be the only way to get this project functional, but also meet the needs of the course. I am also not speaking from experience, but this was my take away from the presentation, which was cool, because I got to step into his shoes, and think about how I would approach this project.

---
