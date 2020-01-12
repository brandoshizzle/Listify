let result_counter = -1;
let searchResults = {};
let preview_interval;

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById('sheet-id').value = localStorage.getItem('sheet_id');
})

async function get_playlists() {
    localStorage.setItem('sheet_id', document.getElementById('sheet-id').value);
    const searchTerm = document.getElementById('searchTerm').value;
    searchResults = await eel.get_playlists(searchTerm)();
    console.log(searchResults);
    result_counter = -1;
    show_next();
}

function nice() {
    const accepted_playlist_info = searchResults['playlists']['items'][result_counter];
    const fb_search_link =  accepted_playlist_info.owner_name.split(' ').join('%20');
    const infoToWrite = [
        document.getElementById('searchTerm').value, // A: Search term
        '', // B: Note
        accepted_playlist_info.name, // C: Playlist name
        accepted_playlist_info.id,  // D: Playlist ID
        accepted_playlist_info.followers, // E: Number of followers
        accepted_playlist_info.href, // F: Playlist url
        `=HYPERLINK("${fb_search_link}","${accepted_playlist_info.owner_name}")`, // G: Owner name
        '', // H: Facebook link
        document.getElementById('song').value, // I: Song name
    ];
    const sheetId = document.getElementById('sheet-id').value;
    const playlistId = searchResults['playlists']['items'][result_counter]['id'];
    eel.nice(sheetId, infoToWrite, playlistId)(show_next());
}

function nah() {
    const rejected_playlist_id = searchResults['playlists']['items'][result_counter]['id'];
    eel.save_as_sorted(rejected_playlist_id)(show_next());
}

function show_next() {
    result_counter++;
    clearInterval(preview_interval);
    document.getElementById('track-previews').pause();
    let pl = searchResults['playlists']['items'][result_counter]
    document.getElementById('playlist-name').textContent = pl.name;
    document.getElementById('curator-name').textContent = pl.owner_name;
    document.getElementById('followers').textContent = pl.followers.toString().replace(/\B(?=(\d{3})+(?!\d))/g,
        ",");
    document.getElementById('artists').textContent = pl.artists;
    document.getElementById('playlist-art').src = pl.image;

    let preview_counter = 0;
    preview_interval = setInterval(() => {
        document.getElementById('track-previews').src = pl.track_previews[preview_counter];
        document.getElementById('track-previews').play();
        if (preview_counter < pl.track_previews.length) {
            preview_counter++;
        } else {
            preview_counter = 0;
        }

    }, 5000);

}

function validate_google() {
    eel.authorize_google()();
}