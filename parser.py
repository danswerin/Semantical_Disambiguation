from collections import namedtuple
import xml.parsers.expat
import pandas as pd
import os
import numpy as np


word = namedtuple('word', ['pos','dom', 'feat', 'id', 'lemma', 'link'])

feat_ru_en = {
	'ЕД': 'sg',
	'МН': 'pl',
	'ЖЕН': 'f',
	'МУЖ': 'm',
	'СРЕД': 'n',
	'ИМ': 'nom',
	'РОД': 'gen',
	'ДАТ': 'dat',
	'ВИН': 'acc',
	'ТВОР': 'ins',
	'ПР': 'prep',
	'ПАРТ': 'gen2',
	'МЕСТН': 'loc',
	'ОД': 'anim',
	'НЕОД': 'inan',
	'ИНФ': 'inf',
	'ПРИЧ': 'adjp',
	'ДЕЕПР': 'advp',
	'ПРОШ': 'pst',
	'НЕПРОШ': 'npst',
	'НАСТ': 'prs',
	'1-Л': '1p',
	'2-Л': '2p',
	'3-Л': '3p',
	'ИЗЪЯВ': 'real',
	'ПОВ': 'imp',
	'КР': 'shrt',
	'НЕСОВ': 'imperf',
	'СОВ': 'perf',
	'СТРАД': 'pass',
	'СЛ': 'compl',
	'СМЯГ': 'soft',
	'СРАВ': 'comp',
	'ПРЕВ': 'supl',
}

link_ru_en = {
	'предик': 'subj',
	'1-компл': 'obj',
	'2-компл': 'obj',
	'3-компл': 'obj',
	'4-компл': 'obj',
	'5-компл': 'obj',
	'опред': 'amod',
	'предл': 'prep',
	'обст': 'pobj',
}

class Parser:
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_element
        self.parser.EndElementHandler = self.end_element
        self.parser.CharacterDataHandler = self.char_data

    def start_element(self, name, attr):
        if name == 'W':
            features = attr['FEAT'].split(' ') if 'FEAT' in attr else ['UNK']
            for i in range(0, len(features)):
                if features[i] in feat_ru_en:
                    features[i] = feat_ru_en[features[i]]

            lemma = lemma = attr['LEMMA'].lower() if 'LEMMA' in attr else ''
            link = attr['LINK'] if 'LINK' in attr else None

            dom = int(attr['DOM']) if attr['DOM'] != '_root' else 0
            pos = features[0]
            feat = set(features[1:])

            if 'adjp' in feat:
                pos = 'VADJ'
                feat -= {'adjp'}

            if 'advp' in feat:
                pos = 'VADV'
                feat -= {'advp'}

            if 'inf' in feat:
                pos = 'VINF'
                feat -= {'inf'}

            self.info = word(pos=pos, dom=dom, feat=feat, id=int(attr['ID']), lemma=lemma, link=link)
            self.cdata = ''

    def end_element(self, name):
        if name == 'S':
            self.sentences.append(self.sentence)
            self.sentence = []
        elif name == 'W':
            self.sentence.append((self.cdata, self.info))
            self.cdata = ''

    def char_data(self, content):
        self.cdata += content


    def read(self, filename):
        with open(filename) as file:
            content = file.read()

        self.sentences = []
        self.sentence = []
        self.cdata = ''
        self.info = ''

        self.parser.Parse(content)

        return self.sentences

class Table_creation:
    def __init__(self):
        self.count = 0
        self.df = pd.DataFrame(columns=['lemma_one', 'lemma_two', 'pos_one', 'pos_two'])
        self.correct = 0
        self.incorrect = 0

    def read_folder(self):
        path = './syntagrus/SynTagRus2016'

        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    parser = Parser()
                    current_path = os.path.join(root, name)
                    # print(path)
                    sentences = parser.read(current_path)
                    self.parse_sentence_group(sentences)
                    self.correct += 1
                    print('Correct paths: ', self.correct, len(sentences))
                except:
                    self.incorrect += 1
                    print(current_path, ' – ERROR')

                if self.correct % 10 == 0:
                    self.save_dataframe()

        print('Incorrect paths: ', self.incorrect)

    def parse_sentence_group(self, sentences):
        for sentence in sentences:
            self.parse_sentence(sentence)

    def parse_sentence(self, sentence):
        for word in sentence:
            info = word[1]
            if not info.dom == 0:
                self.df.loc[self.count] = 0
                self.df.lemma_one.loc[self.count] = sentence[info.dom - 1][1].lemma
                self.df.pos_one.loc[self.count] = sentence[info.dom - 1][1].pos
                self.df.lemma_two.loc[self.count] = info.lemma
                self.df.pos_two.loc[self.count] = info.pos
                self.count += 1

    def save_dataframe(self):
        file_name = 'syntagrus_lemma_' + str(self.correct) + '.csv'
        self.df.to_csv(file_name, encoding='utf-8', index=False)
        print('SAVED.')

        self.df = pd.DataFrame(columns=['lemma_one', 'lemma_two', 'pos_one', 'pos_two'])
        self.count = 0

table = Table_creation()
table.read_folder()
# s = P.read('interaktiv.tgt')
# table.parse_sentence_group(s)
# table.parse_sentence(s[1])
print(table.df)

# print(len(s))
# print(s[1][0])
