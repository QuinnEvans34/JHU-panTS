# Audience Notes - Week 3 Experiment Review & Model Selection

M3P1 audience deliverable. Fill one block per presentation as I observe it (presenters go in random order — record the name in each block). Goal: notes for every presenter, with at least a couple of meaningful, substantive questions asked across the set. This week I am specifically judging three things for each presenter:

- Whether the experiments are genuinely distinct or just minor variations of one run.
- Whether the model selection is justified by the evidence presented, not just the single top metric.
- Whether a non-technical stakeholder could understand why this model was chosen.

What a good Week 3 question looks like: "You compared A and B — was that a clean single-variable test, or did other things change between the runs too?" / "You picked the model with the best score — what did you trade off to get it (overfitting risk, speed, complexity)?" / "How do you know that number isn't just overfitting to your validation set — did you hold out a separate test set?" / "In one sentence a stakeholder would understand, why is this the right model to build on?"

---

## Presentation 1
Presenter: Porter

Summary (2 to 3 sentences):
Porter is building a script analyzer that he is calling "Outlier". He is analyzing scripts to see where the emotional arcs are, and turning points. His first example he showed an analysis on Die Hard, where the model thought the point of no return at scene 60, when in reality it was on scene 100. He is using this model to break down scripts, and decide if they follow a structure that would engage audiences. He is analyzing the text inside the script, and using a mini LM to pick up on sentiment, so he can engineer features off data that does not necessarily hold meaning to computers/algorithms.


Question(s) I asked:
I wanted to know if he thought the results from this weeks training were strong enough for him to derive if the models that he have chosen are good enough to continue training, or if he feels that changing the models may be necessary to bring up accuracy.


Assessment (the required focus):
- Genuinely distinct experiments, or minor variations? - Yes, Porter had distinct experiments, with varying results. This satisfies the deliverables for the project. 
- Model selection justified by the evidence shown, not just the top metric? - Model selection was strong for the most part, he had good enough evidence, I was not sure exactly what metrics he was measuring or how they were computed, but other than that I think it was perfect.
- Could a non-technical stakeholder follow why this model was chosen? - Yes, beyond a doubt a non technical stakeholder could follow, I think a technical stakeholder may have a few questions however.

Strength:
I think it was really great to see that his model was able to pick up on any patterns at all, and that it works for the use case that he wanted. When he first presented this, I had some fears about the viability of the project, and was not sure if it would work to pick up features and make valid predictions. But after seeing his presentation this week, it seems to be a viable product/project, and the main strength was being able to see real numbers, what was useful, and what was not, and where the model has fallen short so far. I also think that he had distinct experiments, showing what happens when you change different features, and how they effect the outputs, which was helpful from the audience standpoint. 


Risk / unclear:
I think the main risk with this project may become the accuracy, it seems that he has a great idea that has been implemented, but if I were to bring up what I think could bring the project down, it would be accuracy. It seems that he is working with a dataset that has a lot of ambiguity and less clear features than most, and because of this, it may become really difficult to make predictions that are accurate, and could be used by a stake holder. 


---

## Presentation 2
Presenter: Gracie

Summary (2 to 3 sentences):
Gracie is doing risk forecasting on earthquakes on 3 separate locations, with one machine learning model. She is feeding the model 9 features, and she is splitting the train test val based on year. She has training data from 2000-18, val from 2019-2021, and then test from 2022 to present day. She is measuring F1 LOs and PR-AUC for her metrics, and has trained multiple different models. She trained two logistic regression models, one pooled and one per region, and a random forest model. She also ran different expirements on each of the models, where we decided that the lat and long should not be included inside the model as features.


Question(s) I asked:
I was curious if she had seen any patterns with earth quakes being time sensitive, meaning if the time of year or period where her data is coming from could create bias in her project. This was based off her saying she was splitting the train val test data being split by time.


Assessment (the required focus):
- Genuinely distinct experiments, or minor variations? - Yes, she had distinct experiments with different metrics. And, beyond that she had multiple models. So I think she meets these requirements.
- Model selection justified by the evidence shown, not just the top metric? - Yes, I think she was justified in the model she chose, but think there is further fine tuning needed.
- Could a non-technical stakeholder follow why this model was chosen? - Yes, I think a non technical stakeholder would follow all the choices made. And that she had numbers to back them up.


Strength:
I think she had a really strong case for herself this week. She had a lot of data to show, multiple models, all her features, experiments showing what worked well and what did not, so she did the work to back up her project this week. I also liked all of the visualizations that she had, it made it much easier to understand what she was speaking about. I also think the leakage checks were really smart, and made me trust the model more.


Risk / unclear:
There were a few things that I think show some real risks, for one, I thought the F1 score would have been a little higher than it was. This is not a bad thing by its self, I know that my model did not have the best accuracy compared to a model getting 90 percent accuracy. But, I think the accuracy a lone is the biggest risk that I saw during her presentation, everything else looked really solid.


---

## Presentation 3
Presenter: Ted

Summary (2 to 3 sentences):
Ted is making a computer vision application that allows him to interface with a video game. He trained his model on hand signals so that he could predict hand movements live. He is using the webcam frame, then a media hand land marker that was trained by google, then he is using his model that he trained after it has been zoomed in for predictions on the hand, then to use a cursor + click. He has moved from classifying the full frame, to zooming in on the hand, and now predicting click or no click where he has gotten 98 percent accuracy.


Question(s) I asked:
I wanted to know if he plans to do anything with he hand signals in the final application, or if it is going to migrate more towards just being a cursor movement and clicking. 


Assessment (the required focus):
- Genuinely distinct experiments, or minor variations? - Yes, he had at least three models that he trained, metrics for all of them, and results from changes. So he was great from this standpoint.
- Model selection justified by the evidence shown, not just the top metric? - Yes, I think the selection had evidence, and that his demo was a home run showcasing why. When he showed the three different models, it was super clear what model worked best and why he chose it.
- Could a non-technical stakeholder follow why this model was chosen? - Yes, I also think the demo was super helpful, and that any non technical stakeholder would be really excited by it.


Strength:
I think the main strengths that he has come in the form of accuracy, having an accuracy of 98 means his model is performing really well. And I have seen this when he demos it, it seems like he has a really strong application, that does exactly what he wants it to do. So, I think the biggest strength, because his application seems to be working really well. I dont think he is ready, just because the top metric is impressive, but because he is using more than one model, and they build upon each other as well. Seeing how the models work together to give strong outputs, and how they have progressed over time makes me really confident in his final product. So, I think his main strength is the clarity and responsiveness of his models, and then the fact that they seem to be working well during his live demo.


Risk / unclear:
There are a few things that show risks in his project however, I think the main one is the clarity behind his goal. I have seen him present three times during this project, and it seems like every time he presented it was very different. This is not a bad thing, because it has gotten better each time, but I also dont know what the final product will look like. I also am not sure what the hand signals will turn into now, because they were the main focus of the project before, but if he is using the camera to interface with the cursor, the signals seem to not have much to do with the project, which from my understanding is his entire dataset and what he trained on. So, the project is impressive, and I loved watching it, but I am not 100 percent sure where this started or where it is heading.
