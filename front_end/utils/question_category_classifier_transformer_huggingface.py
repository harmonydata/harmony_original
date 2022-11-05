import bz2
import pickle as pkl
import re
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model='sentence-transformers/distiluse-base-multilingual-cased-v2')

labels = ['anger/irritability',
 'appetite disturbance',
 'attention span',
 'breakdown',
 'cognitive impairment',
 'cognitive impairment - concentration problems',
 'cognitive impairment - indecision',
 'competitive',
 'coordination',
 'destructive',
 'disruptive/disobedient',
 'distracted',
 'disturbed appetite',
 'fatigue',
 'fatigue/apathy/motivation',
 'fussy',
 'general anxiety',
 'general anxiety/fear',
 'health anxiety',
 'health anxiety/perceived poor health',
 'hopelessness',
 'hyperactivity/arousal/restlessness',
 'imaginative',
 'impairment/functionality',
 'impulsivity',
 'interpersonal aggression',
 'irritability',
 'laziness',
 'lies',
 'loneliness',
 'lonely',
 'loss of interest',
 'low mood',
 'motivation',
 'obsessional',
 'overwhelmed',
 'panic',
 'prosocial',
 'restlessness',
 'self-esteem/worth',
 'show-off',
 'situational anxiety',
 'sleep problems',
 'social anxiety',
 'social phobia',
 'social preference (loner etc. )',
 'social skills – (popular, lots of friends)',
 'soiling',
 'somatic',
 'somatic complaints',
 'speech difficulty',
 'steals',
 'suicidal ideation',
 'sulks',
 'tearful',
 'tense/stressed',
 'tidiness',
 'timid',
 'truant',
 'twitches /habit',
 'uncompetitive',
 'worry',
 'worthlessness/self-esteem']


class QuestionCategoryClassifierTransformerHuggingFace:

    def categorise_questions(self, df):
        classifier_output = classifier(
            list(df.question), labels)

        df["question_category"] = [classifier_output[i]['labels'][0] for i in range(len(df))]