import unittest

from utils.topic_identifier import get_keywords_for_groups


class TestGetTopics(unittest.TestCase):

    def test_simple_example(self):
        list_of_lists_of_texts = [['Feeling nervous, anxious, or on edge',
                                   'I feel shut out and excluded by others'],
                                  ['Not being able to stop or control worrying',
                                   'I cannot tolerate being so alone'],
                                  ['Worrying too much about different things',
                                   'I am unhappy doing so many things alone'],
                                  ['Trouble relaxing', 'I feel left out'],
                                  ['Being so restless that it is hard to sit still',
                                   'It is difficult for me to make friends'],
                                  ['Becoming easily annoyed or irritable', 'I am unhappy being so withdrawn'],
                                  ['Feeling afraid, as if something awful might happen',
                                   'I feel as if nobody really understands me'],
                                  [
                                      'If you checked any problems, how difficult have they made it for you to do your work, take care of things at home, or get along with other people?'],
                                  ['I have nobody to talk to'],
                                  ['I lack companionship'],
                                  ['I find myself waiting for people to call or write'],
                                  ['There is no one I can turn to'],
                                  ['I am no longer close to anyone'],
                                  ['My interests and ideas are not shared by those around me'],
                                  ['I feel completely alone'],
                                  ['I am unable to reach out and communicate with those around me'],
                                  ['My social relationships are superficial'],
                                  ['I feel starved for company'],
                                  ['No one really knows me well'],
                                  ['I feel isolated from others'],
                                  ['People are around me but not with me']]
        kws = get_keywords_for_groups(list_of_lists_of_texts)
        self.assertEqual(len(list_of_lists_of_texts), len(kws))
        self.assertEqual("nervous", kws[0])
