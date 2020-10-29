import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from TestRhyme import *
from Rhythm import *
import threading
import concurrent.futures

# Configure firebase cloud firestore
cred = credentials.Certificate('test-1f44a-firebase-adminsdk-vr15m-e36b95fc24.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# create a threadpoolexecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

callback_done = threading.Event()
def makeSong(text, syllScheme, rhymeScheme):
    '''makeSong(text, syllScheme, rhymeScheme)
    Conforms the provided text to the given syllable pattern and rhyme scheme;
    Uploads the finished song to firebase;
    
    @text: a str containing complete sentences
    @syllScheme: syllScheme: a list of ints where each int specifies the syllable count of a str
                in the returned list
    @rhymeScheme: str specifying the rhyme scheme'''
    lines = divideClauses(text, syllScheme)
    print('BREAK UP LINES')
    for line in lines:
        print(line)
    lines = rhymeaabb(getWords(lines), lines)
    print('RHYME')
    for line in lines:
        print(line)
    lines = lineStretch(lines, syllScheme)
    print('PERFECT SYLL COUNT')
    for line in lines:
        print(line)
    return lines
    

def processSnap(changes):
    '''processSnap(changes)
    Processes the songs(s) recently added to the database; adds a
    songText attribute'''
    for change in changes:
        print("FORMATTING DOC!!!!!!!!!!!")
        if change.type.name == 'ADDED':
            infoDoc = change.document.to_dict()
            if not infoDoc.get('songText', None):             # only process the input if it has not already been converted
                text = infoDoc['origText']
                totalSyll = countLineSyll(text)
                rhymeScheme = list(infoDoc['rhymeScheme'])
                # extract the syllable scheme
                syllScheme = infoDoc['syllScheme'].split(',')
                for i,num in enumerate(syllScheme):
                    num = num.strip()
                    if num.isnumeric():
                        syllScheme[i] = int(num)
                    else:
                        syllScheme[i] = 7                       # arbitrary replacement for non-number
                # extend the syllable scheme until it accounts for all input text syllables
                i = 0
                while sum(syllScheme) < totalSyll:
                    index = i%len(syllScheme)
                    syllScheme.append(syllScheme[index])
                    i += 1
                song = makeSong(text, syllScheme, rhymeScheme)
                songCollection.document(change.document.id).update({'songText': song})
    print("Finished thread!")


songCollection = db.collection(u'songs')
def onSnap(collSnap, changes, readTime):
    '''onSnap(colSnap, changes, readTime)
    Event handler for changes to the database; adds a
    songText attribute to newly-added songs that lack one'''
    print("CHANGE MADE: starting thread...............................c")
    executor.submit(processSnap, (changes))
          



def main():
    # listen for changes in the database
    collWatch = songCollection.on_snapshot(onSnap)
    while True:
        callback_done.wait()
        callback_done.clear()
    print('ALL DONE!')


#start thread
#loop + wait
#join

if __name__ == "__main__":
    main()