// Project: Song Converter
// Names: Nivedha Srinivasan, Oreoluwa Alao
// Date: 6/14/20
// Task Description: Sends info from form in convert.html to Firebase

const form = document.querySelector("#convert");

//saving data
form.addEventListener('submit', (e) =>{
    e.preventDefault();
    // set a unique DOC ID
    docID = form.name.value+form.age.value;
    // add song to document in "songs" collection in Firebase
    db.collection('songs').doc(docID).set({
        name: form.name.value,
        tags: form.tags.value,
        origText: form.textarea.value,
        syllScheme: form.syllables.value,
        rhymeScheme: form.rhyme.value,
        likes: 0
    })
    // add userID to song document (so only that user can access it later)
    
    // reset form
    form.name.value = '';
    form.tags.value = '';
    form.textarea.value = '';
    form.syllables.value = '';
    form.rhyme.value = '';
})