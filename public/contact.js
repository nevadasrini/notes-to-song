// Project: Song Converter
// Names: Nivedha Srinivasan, Oreoluwa Alao
// Date: 6/14/20
// Task Description: Fetches feedback from form in contact.html and sends them to Firebase

const form = document.querySelector("#contact-form");

//saving data
form.addEventListener('submit', (e) =>{
    e.preventDefault();
    // add comments to "feedback" collection in Firebase
    db.collection('feedback').add({
        comment: form.textarea.value
    })
    // reset form
    form.textarea.value = '';
})