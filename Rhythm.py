from nltk import Tree, ParentedTree
from stat_parser import Parser                  # parses sentences into clauses
import datamuse                                 # a database of english words, their attrbuites, and their rhymes
from spacy.lang.en import English               # NLP toolkit
from spacy.matcher import Matcher               # allows rule-based matching in spaCy objects
import spacy
import re


parser = Parser()
dm = datamuse.Datamuse()
nlp = spacy.load("en_core_web_sm")              # pretrained model used for dependency parsing
matcher = Matcher(nlp.vocab)

syllDict = {}                                   # stores syllable count of each word used (to reduce the number of requests made to Datamuse)
                                                # Key: a str; Value: an int

firstRun = False                                # True when the grabClauses method has just been called non-recursively; used to handle Python's late-binding closures
NOCHANGE = ('DET', 'PRON', 'PROPN', 'X', 'CCONJ', 'NUM', 'CCONJ', 'PART', 'ADV', 'ADP', 'SPACE', 'INTJ')           # words that should never be swaped with synonyms
NOCHANGETAG = ('MD')
def trimPunc(word):
    '''trimPunc(word) -> Token
    Removes leading/trailng punctuation from the word
    
    @word: a str or spaCy token'''
    if isinstance(word, str):
        parts = nlp(word)
        word = [part for part in parts if part.is_alpha or part.is_digit] or parts
        word = word[0]
    return word

def getSingleSyll(word):
    '''getSingleSyll(word) -> int
    Returns the number of syllables in the provided word

    word: a str or a spaCy Token
    '''
    word = trimPunc(word).text.lower()
    if not syllDict.get(word, None):
        if len(word) > 2 and ("’" in word or "'" in word):
            syllDict[word] = 1
        elif not isWord(word):
            syllDict[word] = 0
        else:
            syllDict[word] = dm.words(sp=word, md="s", qe="sp", max=1)[0]['numSyllables']
    return syllDict[word]

def countLineSyll(line):
    '''countLineSyll(line) -> tuple
    Returns the total number of syllables in the provided string
    
    line: a spaCy Doc or Span object, an nltk Tree, a list of strings, or a str'''
    currSyll = 0                # current num of syllables in line
    if isinstance(line, str):
        line = nlp(line)
    try:
        line = line.leaves()    # only if the object provided is a tree
    except AttributeError:
        pass    
    for word in line:
        #add syll count to total
        currSyll += getSingleSyll(word)
    return currSyll

def isWord(word):
    '''isWord(word) -> bool
    Returns true if the provided text is a word
    
    word: a str or a spaCy Token'''
    word = trimPunc(word)
    anySyns = dm.words(rel_bgb=word.text.lower(), max=1)
    return not(not(anySyns)) and not word.is_punct

def grabClauses(ptree, goalSyll, wordList=[]):
    '''grabClauses(ptree, goalSyll, wordList=[]) -> tuple
    Returns a tuple containing:
        - the subset of words in ptree whose total syllable count matches goalSyll
        - the the amount by which this subset misses the goal syllable count
    
    ptree: a nltk ParentedTree containing a set of words to be used
    goalSyll: the total syllable count for the returned list of strings
    wordList: do not use! it is merely for recursion
    '''
    global firstRun
    if firstRun and wordList:
        wordList = []
    syllDif = goalSyll - countLineSyll(wordList) - countLineSyll(ptree)
    print(wordList)
    print(ptree.leaves() or ptree[0])
    if syllDif < -2:                      # current syllable count is too long
        print("TOO LONG")
        partialClause = ptree[0]
        if not isinstance(partialClause, str):
            firstRun = False
            return grabClauses(partialClause, goalSyll, wordList)
    else:
        wordList.extend(ptree.leaves() or [ptree[0]])
        print("Hmm...")
        if syllDif > 0:                   # current syllable count is too short
            print("TOO SHORT")
            # attempt to include words from a new clause
            nextClause = ptree.right_sibling()
            if nextClause:
                firstRun = False
                return grabClauses(nextClause, goalSyll, wordList)
    print("it's ok")
    return (wordList, syllDif)

def divideClauses(text, syllScheme):
    '''divideClauses(text, syllScheme) -> list of str
    
    Returns a list of strings where each line has a number of syllables 
    close to those specified by the corresponding item in the syllScheme list
    (attains this by dividing clauses among various lines)
    
    text: a str with complete sentences
    syllScheme: a list of ints where each int specifies the syllable count of a str
                in the returned list'''
    # remove extra whitespace
    replaceWhitespace = ('  ', '   ', '\n', '\t')
    for space in replaceWhitespace:
        text = text.replace(space, ' ')
    text = text.replace("'", '').replace('’', '')
    doc = nlp(text)             # tokenize the text
    lines = []                  # list of song lines
    sentences = list(doc.sents) # split the doc by sentence
    sentIndex = 0               # index of the sentence currently being processed
    restOfSent = ""             # a doc containing the part of a previous sentence that was left unprocessed
    for goalSyll in syllScheme:
        lineContent = []        # list of words in this line
        sent = restOfSent       # the text to be used in filling the line (Doc object)
        if not sent:
            try:
                sent = sentences[sentIndex]
            except:
                pass
        print(sent)
        if sent:
            # swap out parentheses for brackets (parentheses cause an error with the clause parser)
            woParenth = sent.text.replace(")", "]")
            woParenth = woParenth.replace("(", "[")
            sent = nlp(woParenth)
            # Parse the clauses in the sentence
            clauseTree = parser.parse(sent.text)                            # FIX - this step takes longest; reduce num trees needed!!!! >_<
            clauseTree = ParentedTree.fromstring(str(clauseTree))
            # Extract clauses that fit within the goal syllable count
            global firstRun
            firstRun = True
            words, syllDif = grabClauses(clauseTree, goalSyll)
            lineContent.extend(words)
            # Save the rest of this sentence for use in filling the next line OR move on to the next setence
            # locate the already-used portion of this sentence
            searchPattern = []
            words = nlp(" ".join(words))
            for token in words:
                searchPattern.append({"LOWER":token.text.lower()}) 
            # clear the previously-used search pattern         
            if matcher.get("SearchPattern"):
                matcher.remove("SearchPattern")
            print(searchPattern)
            matcher.add("SearchPattern", None, searchPattern)   # reset the search pattern to match the used portion of this sentence
            print(sent)
            matchID, startI, endI = matcher(nlp(sent.text))[0]
            if endI < len(sent):
                restOfSent = sent[endI:]
                print('got rest')
            else:
                # move onto the next sentence if this sentence is completely used up
                sentIndex += 1
                restOfSent = ""
                print('no rest')
            # convert lineContnent to a spaCy object
            lineContent = sent[startI:endI]
        else:
            # convert lineContnent to a spaCy object
            lineContent = nlp(sent)
        # If there are too few syllables in this line, compensate with filler words
        print('reached end iter')
        dif = goalSyll - countLineSyll(lineContent)
        print(lineContent)
        if len(lineContent) != 0:
            # Store the line
            lines.append(lineContent.text)
        print('reached end iter')

    return lines

def wordStretch(token, syllDif):
    '''wordStretch(token, syllDif) -> tuple
    Returns a tuple containing...
        -(str) a synonym of the provided token that has syllDif more syllables than the token;
        -(int) the number of syllables that could not be added to the word
    
    @token: a spaCy token object
    @syllDif: int; specifies the number of syllables to be added to the word; can be negative 
    if you want to remove syllables'''
    outTup = (token.text, syllDif)
    if isWord(token) and not token.pos_ in NOCHANGE and not token.tag_ in NOCHANGETAG:
        goalSyll = syllDif + getSingleSyll(token)
        root = token.lemma_                         # present/root tense of word
        # Search through the word's synonyms for a replacement making up for the syllDif
        syns = dm.words(ml=root, md='s')
        for syn in syns:
            syll = syn['numSyllables']
            if  abs(goalSyll - syll) < abs(outTup[1]):
                outTup = (syn['word'], goalSyll-syll)
    return outTup
    
def lineStretch(lines, syllScheme):
    '''lineStretch(lines, syllScheme) -> list of str
    Makes each string in lines have the number of syllables
    as specified by the int int in the corresponding possition
    of syllScheme; does so by swapping words out with shorter/
    longer synonyms
    
    Returns a list of strings
    
    @lines: list of str
    @syllScheme: a list of ints where each int specifies the syllable count of a str
                in the returned list'''
    outputSong = []                     # contains song lines
    print('SyllScheme' + str(syllScheme))
    for i in range(len(lines)):
        print("WORKNIG ON LINE " + str(i))
        # determine how far off the current line syll is from the goal syll
        currLineTxt = lines[i]
        currLine = nlp(currLineTxt)
        for k in range(len(currLine), 0, -1):   # ommit last word so it doesn't change
            if not(k == 0 or currLine[k-1].is_punct):
                currLine = currLine[:k-1]
                break
        goalSyll = syllScheme[i]
        dif = goalSyll - countLineSyll(nlp(currLineTxt))
        if dif:
            # arrange the words from longest to shortest
            wordDict = {}
            for token in currLine:
                wordDict[token] = getSingleSyll(token)
            longToShort = [token for token, syll in sorted(wordDict.items(), key=lambda item: item[1])]
            longToShort.reverse()
            print(longToShort)
            # starting with longest words, adjust the total number of syllables by substituting words for synonyms
            for token in longToShort:
                replacement, dif = wordStretch(token, dif)
                currLineTxt = currLineTxt.replace(token.text, replacement, 1)
                if not dif:
                    break
            
        outputSong.append(currLineTxt)
    return outputSong



'''
WATCH OUT FOR PUNC in rhyming and syll (isword)

'''
