// Project: Song Converter
// Names: Nivedha Srinivasan, Oreoluwa Alao
// Date: 6/14/20
// Task Description: Fetches songs from the Firebase and displays them in songs.html; sets song title and song text for songdisplay.html

//connect song list to firebase documents
const songList = document.querySelector('#song-list');

var songtitle = "error"
var songtext = "Sorry, an error occurred."

//create element and render songs to html browser
function renderSongs(doc){
    //create elements
    let li = document.createElement('li');
    let name = document.createElement('span');
    let tags = document.createElement('span')
    let cross = document.createElement('div');
    let view = document.createElement('button');

    //assign values to elements
    li.setAttribute('data-id', doc.id)
    name.textContent = doc.data().name;
    tags.textContent = doc.data().tags;
    cross.textContent = 'X';
    view.textContent = 'view';

    //get the song text from the doc
    let songtext = ""
    i = 0;
    while (i< doc.data().songText.length){
        songtext+=doc.data().songText[i];
        songtext+="\n";
        i++;
    }

    //append the "name" and "tags" of the song to each list item
    li.appendChild(name);
    li.appendChild(tags);
    li.appendChild(cross);
    li.appendChild(view);

    //append list item to songList
    songList.appendChild(li)

    //deleting data
    cross.addEventListener('click', (e) =>{
        e.stopPropagation();
        let id = e.target.parentElement.getAttribute('data-id');
        db.collection('songs').doc(id).delete();
    })

    view.addEventListener('click', (e) =>{
        e.stopPropagation();
        let id = e.target.parentElement.getAttribute('data-id')
        songtitle = name.textContent;
        console.log(songtitle);
        console.log(songtext);
        displayPage = window.open("songdisplay.html")
        displayPage.onload = function () {
            const preTitle = this.document.getElementById('song-title');
            const preText = this.document.getElementById('song-text');
            preText.innerText = songtext;
            preTitle.innerText = songtitle;
        };
    })
}

//cycle through songs and pass through render function
db.collection('songs').get().then((snapshot) => {
    snapshot.docs.forEach(doc => {
        auth.onAuthStateChanged(user => {
            if (doc.data().userID== user.uid){
                renderSongs(doc)
                console.log(doc.data());
            }
        })
    })
})

const form = document.querySelector("#contact-form");

//saving data
form.addEventListener('submit', (e) =>{
    e.preventDefault();
    // add comments to "feedback" collection in Firebase
    db.collection('songs').doc(docID).update({
        songText: form.textarea.value
    })
    // reset form
    form.textarea.value = '';
})