"""
Spotify Playlist Analyzer
"""
# Importing Libraries
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import re
#import c
import time
from spotipy.oauth2 import SpotifyOAuth
import os
#from flask import Flask, request

# Spotify app credentials from your Spotify Developer Dashboard
SPOTIPY_CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
SPOTIPY_CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
SPOTIPY_REDIRECT_URI = 'https://spotifyanalyzertest.streamlit.app'

# Create a SpotifyOAuth instance
#sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope='user-library-read')

class Playlist:
    def __init__(self, playlist_name):

        # Your Spotify API credentials (note: it's not secure to include your credentials in the code)
        # client_id = '8cfa81fbc4074f3aad32716a36044864'
        # client_secret = 'a64ec813eaa24d19a42c694dbc61ba35'
        client_id = '2bdfeb8580304b9fb343ff8cc8744e76'
        client_secret = '73cbcc49de99490f821c2925c2b41419'
        # Set up the Spotify client credentials manager and Spotipy client
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        self._url_type, self._playlist_id = Playlist.id_from_url(playlist_name)  # done
        self._playlist = sp.playlist(self._playlist_id)  # done
        self._playlist_name = self._playlist['name']  # done
        self._playlist_image = self._playlist['images'][0]['url']  # done
        self._playlist_desc = self._playlist['description']  # done
        # self._broad_track_info = self._playlist['tracks']['items']
        self._broad_track_info = []
        results = sp.playlist_tracks(self._playlist_id)
        while results:
            self._broad_track_info.extend(results['items'])
            if results['next']:
                results = sp.next(results)
            else:
                break

        Playlist.set_track_info(self)
        self._tracks = [i for i in self.track_info]
        self._artists = [i['artist'] for i in self.track_info.values()]
        self._popularities = [i['popularity'] for i in self.track_info.values()]
        self._durations = [i['duration'] for i in self.track_info.values()]
        self._combined_durations = sum(self.durations)
        self._albums = [i['album'] for i in self.track_info.values()]
        self._release_dates = [i['release date'] for i in self.track_info.values()]

        # NEW
        self._track_durations_formatted = []
        for duration_ms in self._durations:
            duration_seconds = duration_ms / 1000
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            formatted_duration = f"{int(minutes)}:{int(seconds):02d}"  # Format seconds to have leading zero if < 10
            self._track_durations_formatted.append(formatted_duration)

        # END
        self.fetch_audio_features(sp)
        self.set_mood_ratings()

        Playlist.set_df(self)
        Playlist.set_recommendations(self, sp)
        Playlist.fetch_genres(self, sp)

    # Function to extract the ID and type (e.g., playlist, track) from a Spotify URL using regex
    @staticmethod
    def id_from_url(url) -> tuple[str, str]:
        try:
            url_regex = re.search(
                r"^https?:\/\/(?:open\.)?spotify.com\/(user|episode|playlist|track|album)\/(?:spotify\/playlist\/)?(\w*)",
                url)
            return url_regex.group(1), url_regex.group(2)
        except AttributeError:
            st.error("Invalid URL")  # Display an error message in the Streamlit app if the URL is invalid

    @property
    def playlist_id(self):
        return self._playlist_id

    @property
    def playlist(self) -> dict[dict]:
        return self._playlist

    @property
    def playlist_name(self):
        return self._playlist_name

    @property
    def playlist_image(self):
        return self._playlist_image

    @property
    def playlist_desc(self):
        return self._playlist_desc

    @property
    def broad_track_info(self):
        return self._broad_track_info

    def set_track_info(self):
        self._track_info = {}
        # print(self._track_info)
        for track in self._broad_track_info:
            self._track_info.update({track["track"]["name"]: {
                'artist': (", ".join([artist["name"] for artist in track["track"]["artists"]])),
                'popularity': track["track"]["popularity"],
                'duration': track["track"]["duration_ms"],
                'album': track["track"]["album"]["name"],
                'release date': track["track"]["album"]["release_date"]
            }})
        # print(self._track_info)

    @property
    def track_info(self):
        return self._track_info

    @property
    def tracks(self):
        return self._tracks

    @property
    def artists(self):
        return self._artists

    @property
    def popularities(self):
        return self._popularities

    @property
    def albums(self):
        return self._albums

    @property
    def durations(self):
        return self._durations

    @property
    def release_dates(self):
        return self._release_dates

    @property
    def track_durations_formatted(self):
        return self._track_durations_formatted

    def set_df(self):
        # Numeric and formatted durations
        numeric_durations = [duration_ms / 60000 for duration_ms in self._durations]  # Duration in minutes
        formatted_durations = []
        for duration_ms in self._durations:
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            formatted_duration = f"{minutes}m {seconds}s"
            formatted_durations.append(formatted_duration)

        popularity_ranges = pd.cut(self._popularities, bins=[-1, 30, 60, 101],
                                   labels=['Hidden Gems (0-30%)', 'Common (30-60%)', 'Popular (60-100%)'])

        data = {
            "Name": self.tracks,
            "Artist": self.artists,
            "Album": self.albums,
            "Release Date": self.release_dates,
            "Popularity": self.popularities,
            "Popularity Range": popularity_ranges,
            "Duration (min)": numeric_durations,  # Numeric duration for sorting and plotting
            "Duration": formatted_durations  # Formatted duration for display
        }

        self._df = pd.DataFrame(data)

    @property
    def df(self):
        return self._df

    
    def get_track_uris(self, sp):
        # Assume self.playlist is a dictionary containing the playlist ID
        playlist_id = self.playlist.get('id')

        if playlist_id:
            # Fetch the tracks from the playlist using the correct playlist ID
            playlist = sp.playlist_tracks(playlist_id)

            # Extract track URIs from the playlist
            track_uris = [item['track']['uri'] for item in playlist['items']]

            return track_uris
        else:
            print("No playlist ID found.")
            return []

    def set_recommendations(self, sp, limit=20):
        # Get track URIs from the playlist
        playlist_tracks = self.get_track_uris(sp)

        # Fetch recommendations from Spotify using multiple seed tracks
        if playlist_tracks:
            # Use multiple tracks as seeds for diversity
            seed_tracks = playlist_tracks[:min(5, len(playlist_tracks))]
            recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=limit)['tracks']

            # Update the recommendations attribute
            self._recommendations = recommendations
        else:
            print(f"No tracks found in the playlist. Unable to fetch recommendations.")

    @property
    def recommendations(self):
        return self._recommendations

    
    # THIS WORKS
    def fetch_genres(self, sp):
        genre_count = {}
        total_tracks = len(self._broad_track_info)
        self._genres = {}

        for track in self._broad_track_info:
            artist_genres = set()  # Collect all unique genres for this track
            for artist in track["track"]["artists"]:
                artist_id = artist["id"]
                if artist_id not in self._genres:  # Cache the artist's genres to avoid repeated API calls
                    artist_info = sp.artist(artist_id)
                    self._genres[artist_id] = {
                        'name': artist_info['name'],
                        'genres': artist_info['genres']
                    }
                for genre in self._genres[artist_id]['genres']:

                    if 'country' in genre:
                        genre = 'Country'
                    elif 'rock' in genre:
                        genre = 'Rock'
                    elif 'rap' in genre:
                        genre = 'Rap'
                    elif 'pop' in genre:
                        genre = 'Pop'
                    elif 'hip hop' in genre:
                        genre = 'Hip hop'
                    elif 'jazz' in genre:
                        genre = 'Jazz'
                    elif 'soul' in genre:
                        genre = 'Soul'
                    elif 'metal' in genre:
                        genre = 'Metal'
                    elif 'funk' in genre:
                        genre = 'Funk'
                    elif 'indie' in genre:
                        genre = 'Indie'
                    elif 'techno' in genre:
                        genre = 'Techno'
                    elif 'dubstep' in genre:
                        genre = 'Dubstep'
                    elif 'alternative' in genre:
                        genre = 'Alt'
                    elif 'folk' in genre:
                        genre = 'Folk'
                    else:
                        genre = 'Other'
                    artist_genres.add(genre)

            # Distribute the count equally among the genres for this track
            count_per_genre = 1 / len(artist_genres) if artist_genres else 0
            for genre in artist_genres:
                genre_count[genre] = genre_count.get(genre, 0) + count_per_genre

        self._genre_percentages = {genre: (count / total_tracks) * 100 for genre, count in genre_count.items()}

    def fetch_audio_features(self, sp):
        # Filter out None or empty track IDs
        valid_track_ids = [track['track']['id'] for track in self._broad_track_info if track['track']['id']]

        # Fetch audio features in batches if necessary
        self._audio_features = {}
        for i in range(0, len(valid_track_ids), 50):  # Spotify API limits to 50 IDs per request
            batch_ids = valid_track_ids[i:i+50]
            audio_features = sp.audio_features(batch_ids)
            for track, features in zip(self._broad_track_info[i:i+50], audio_features):
                if features:
                    self._audio_features[track['track']['name']] = features

    def set_mood_ratings(self):
        # Set mood ratings based on audio features
        self._mood_ratings = {}
        for track_name, features in self._audio_features.items():
            mood = self.determine_mood(features)
            self._mood_ratings[track_name] = mood

    @staticmethod
    def determine_mood(features):
        # This is a simplistic approach; modify as needed
        if features['valence'] > 0.7 and features['energy'] > 0.6:
            return 'Happy'
        elif features['valence'] < 0.3 and features['energy'] < 0.4:
            return 'Sad'
        elif features['energy'] > 0.7:
            return 'Energetic'
        elif features['tempo'] < 100:
            return 'Chill'
        else:
            return 'Neutral'

    def calculate_mood_percentages(self):
        mood_counts = {}
        total_tracks = len(self._mood_ratings)

        # Count each mood occurrence
        for mood in self._mood_ratings.values():
            if mood in mood_counts:
                mood_counts[mood] += 1
            else:
                mood_counts[mood] = 1

        # Calculate percentages
        mood_percentages = {mood: (count / total_tracks) * 100 for mood, count in mood_counts.items()}
        return mood_percentages


# def display_page():
#     SPOTIPY_CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
#     SPOTIPY_CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
#     SPOTIPY_REDIRECT_URI = 'http://localhost:8080/'
    
# #     # Keep
#     # Set up the Streamlit app title
#     st.title("Spotify Playlist Analyzer")

#     # Load an image and display it in the Streamlit sidebar
#     image = Image.open('Vibify.png')
#     st.sidebar.image(image)

#     # Keep
#     # Create an input field in the sidebar for the Spotify playlist URL
#     #if st.sidebar.text_input("Enter the URL of the Spotify playlist:"):
#     playlist_name = st.sidebar.text_input("Enter the URL of the Spotify playlist:")
#     return playlist_name


def display_playlist_info(p: Playlist):
    total_duration_hours = (p._combined_durations) // (1000 * 60 * 60)
    remaining_ms = p._combined_durations % (1000 * 60 * 60)
    remaining_minutes = remaining_ms // (1000 * 60)

    p.df.index = range(1, len(p.df) + 1)

    # Create two columns for layout
    col1, _, col2, _ = st.columns([1, 1, 2, 1])

    # Display the playlist cover and title in the left column
    with col1:
        st.image(p.playlist_image, width=250)
    # Display the rest of the information on the right column
    with col2:
        st.markdown(f"<div class='bubble' style='font-size: 24px; text-align: center;'>{p.playlist_name}</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Description: {p.playlist_desc}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Number of tracks: {len(p.track_info)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bubble'>Total Time: {total_duration_hours} hours {remaining_minutes} minutes</div>",
                    unsafe_allow_html=True)

    # Use CSS to style text bubbles
    st.markdown(
        """
        <style>
            .bubble {
                background-color: #262730; /* Light grey background color */
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 16px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display the interactive table
    st.markdown("<div style='font-size: 24px; text-align: center;'><div class='bubble'>Tracklist</div></div>",
                unsafe_allow_html=True)
    st.dataframe(p.df)


def display_pop_chart(p):
    # Create and display a histogram of track popularity
    popularity_percentage = p.df['Popularity Range'].value_counts(normalize=True) * 100
    fig_popularity = px.bar(
        x=popularity_percentage.index,  # Specify the x-axis variable
        y=popularity_percentage.values,  # Specify the y-axis variable
        labels={'y': 'Percentage of Songs (%)', 'x': 'Popularity Range'},
        category_orders={'x': ['Hidden Gems (0-30%)', 'Common (30-60%)', 'Popular (60-100%)']}
    )

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Track Popularity Distribution</div>",
                unsafe_allow_html=True)

    # Display the popularity chart
    st.plotly_chart(fig_popularity)


def display_bivariate_analysis(p):
    # Set up bivariate analysis with dropdown options for x and y variables
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Bivariate Analysis</div>",
                unsafe_allow_html=True)
    x_axis = "Duration (min)"
    y_axis = "Popularity"
    fig_bivariate = px.scatter(p.df, x=x_axis, y=y_axis, title=f"{x_axis} vs. {y_axis}", hover_name='Name',
                               hover_data={"Duration (min)": False, "Duration": True})
    st.plotly_chart(fig_bivariate)


def display_multivariate_analysis(p):
    # Set up multivariate analysis with dropdown options for color and size variables
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Multivariate Analysis</div>",unsafe_allow_html=True)
    color_by = st.selectbox("Select a variable to color by:", ["Artist", "Album", "Release Date"])
    size_by = st.selectbox("Select a variable to size by:", ["Popularity", "Duration (min)"])
    fig_multivariate = px.scatter(p.df, x="Duration (min)", y="Popularity", color=color_by, size=size_by,
                                  hover_name="Name", title="Duration vs. Popularity Colored by Artist",
                                  hover_data={"Duration (min)": False, "Duration": True})
    st.plotly_chart(fig_multivariate)

def display_playlist_summary(p):
    # Convert the 'Popularity' column to numeric type
    p.df['Popularity'] = pd.to_numeric(p.df['Popularity'], errors='coerce')

    # Provide a summary of the playlist, showing the most and least popular tracks
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Playlist Summary</div>", unsafe_allow_html=True)

    most_popular_track = p.df.loc[p.df['Popularity'].idxmax()]
    least_popular_track = p.df.loc[p.df['Popularity'].idxmin()]

    st.write(
        f"Most popular track: {most_popular_track['Name']} by {most_popular_track['Artist']} ({most_popular_track['Popularity']} popularity)"
    )
    st.write(
        f"Least popular track: {least_popular_track['Name']} by {least_popular_track['Artist']} ({least_popular_track['Popularity']} popularity)"
    )

def display_recommendations(p):
    st.write("Recommended songs:")

    # Set the width and spacing for each column (adjust as needed)
    col_width = 300
    spacing = 20

    for i in range(0, len(p.recommendations), 2):
        # Create two columns for layout
        col1, col2 = st.columns(2)

        # Display the first song in the row
        with col1:
            display_song(p.recommendations[i], col_width, spacing)

        # Display the second song in the row if it exists
        with col2:
            if i + 1 < len(p.recommendations):
                display_song(p.recommendations[i + 1], col_width, spacing)

def display_song(track, col_width, spacing):
    # Display the song cover as a clickable image with custom HTML and CSS
    spotify_url = track['external_urls']['spotify']
    image_html = f'<a href="{spotify_url}" target="_blank"><img src="{track["album"]["images"][0]["url"]}" width="{col_width - spacing}" style="cursor:pointer;"></a>'
    st.write(f'{image_html}', unsafe_allow_html=True)

    # Display the wrapped song title starting from the left
    st.markdown(
        f"<p style='word-wrap: break-word;'>{track['name']} - {track['artists'][0]['name']}</p>",
        unsafe_allow_html=True
    )


def display_genre_pi(p):
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Genre Percentages</div>",unsafe_allow_html=True)
    # Creating a pie chart
    fig = px.pie(
        names=p._genre_percentages.keys(),
        values=p._genre_percentages.values(),
    )

    # Showing the pie chart
    st.plotly_chart(fig)


def display_mood_pi(p):
    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Mood Percentages</div>",unsafe_allow_html=True)
    percentages = p.calculate_mood_percentages()
    # Creating a pie chart
    fig = px.pie(
        names=percentages.keys(),
        values=percentages.values(),
    )

    #Showing the pie chart
    st.plotly_chart(fig)

def display_top10_artists(p):
    artist_popularity = {}
    for track_info in p.track_info.values():
        artists = track_info['artist'].split(", ")
        for artist in artists:
            if artist in artist_popularity:
                artist_popularity[artist] += track_info['popularity']
            else:
                artist_popularity[artist] = track_info['popularity']

    max_popularity = max(artist_popularity.values())
    artist_popularity = {artist: (popularity / max_popularity) * 100 for artist, popularity in
                         artist_popularity.items()}

    sorted_artists = sorted(artist_popularity.items(), key=lambda x: x[1], reverse=True)[:10]

    top_artists, top_popularity = zip(*sorted_artists)

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Top 10 Artists by Popularity</div>",unsafe_allow_html=True)
    df_top_artists = pd.DataFrame({'Artist': top_artists[::-1], 'Popularity': top_popularity[::-1]})
    fig = px.bar(df_top_artists, x='Popularity', y='Artist', orientation='h')
    fig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                      marker_line_width=1.5, opacity=0.6)
    st.plotly_chart(fig)


def display_top10_songs(p):
    max_popularity = p.df['Popularity'].max()
    p.df['Popularity'] = (p.df['Popularity'] / max_popularity) * 100

    top_songs = p.df.nlargest(10, 'Popularity')

    st.markdown("<div class='bubble' style='font-size: 24px; text-align: center;'>Top 10 Songs by Popularity</div>",unsafe_allow_html=True)
    fig = px.bar(top_songs[::-1], x='Popularity', y='Name', orientation='h')
    fig.update_traces(marker_color='rgb(255, 123, 127)', marker_line_color='rgb(165, 38, 42)',
                      marker_line_width=1.5, opacity=0.6)
    st.plotly_chart(fig)


def run(p):
    display_playlist_info(p)
    display_playlist_summary(p)
    display_pop_chart(p)
    display_bivariate_analysis(p)
    #display_multivariate_analysis(p)
    display_genre_pi(p)
    display_mood_pi(p)
    display_top10_artists(p)
    display_top10_songs(p)
    display_recommendations(p)


# Real Main
def main():
    # Spotify app credentials from your Spotify Developer Dashboard
    SPOTIPY_CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
    SPOTIPY_CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
    SPOTIPY_REDIRECT_URI = 'https://spotifyanalyzertest.streamlit.app'
    
    st.title("Spotify Playlist Analyzer")

    # Load an image and display it in the Streamlit sidebar
    image = Image.open('Vibify.png')
    st.sidebar.image(image)
    
    
    button_style = f"""
    <style>
        /* Button style */
        .stButton button {{
            background-color: transparent !important;
            color: #1DB954 !important;
            border: 2px solid #1DB954 !important; /* Green border all the time */
            transition: background-color 0.3s, border-color 0.3s, color 0.3s;
        }}

        /* Button hover style */
        .stButton button:hover {{
            background-color: #1DB954 !important; /* Green background on hover */
            color: white !important; /* White text on hover */
        }}
    </style>
    """

    # Display the custom CSS style
    st.markdown(button_style, unsafe_allow_html=True)


    try:
        playlist_name
    except NameError:
        playlist_name = st.sidebar.text_input("Enter the URL of the Spotify playlist:")


    # NEW
    playlists_dict = {}
    if st.sidebar.button("Manage Spotify Account"):
        # Spotify API credentials
        CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
        CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
        
        # Authenticate the user with Spotify
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id='2bdfeb8580304b9fb343ff8cc8744e76',
            client_secret='73cbcc49de99490f821c2925c2b41419',
            redirect_uri='https://spotifyanalyzertest.streamlit.app',  # Update the redirect_uri
            scope='playlist-read-private',
            show_dialog=True
        ))

        user = sp.current_user()
        st.sidebar.success(f"Logged in as {user['display_name']}")

        # Get the playlists of the authenticated user
        playlists = sp.current_user_playlists()

        st.session_state.spotify_playlists = playlists['items']

        playlist_name = None
        

    def generate_analysis(playlist):
        #print(f"button for {playlist['name']} hit")
        playlist_name = playlist['external_urls']['spotify']
        return playlist_name
        #st.sidebar.text(playlist_name)
        #p = c.Playlist(playlist_name)
        #c.run(p)

        # Print the contents of the session state variable and add a button for each playlist
    if 'spotify_playlists' in st.session_state:
        playlists = st.session_state.spotify_playlists
        for idx, playlist in enumerate(playlists):
            st.sidebar.write(f"{idx + 1}. {playlist['name']}")
            #st.sidebar.write(f"   External URL: {playlist['external_urls']['spotify']}")
            generate_button = st.sidebar.button(f"Generate Analysis for {playlist['name']}", key=f"generate_{idx}")
            st.sidebar.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
            if generate_button:
                # Call a function to generate the analysis for the selected playlist
                playlist_name = generate_analysis(playlist)
    else:
        #st.write("No Spotify playlists available. Please log in to Spotify.")
        pass


    #playlist_name = c.display_page()
    flag = False

    # Define the desired loading bar color (Spotify green)
    loading_bar_color = "#1DB954"

    # Define the custom CSS style for the loading bar with the chosen color
    loading_bar_style = f"""
    <style>
    @keyframes loading {{
        0% {{
            width: 0%;
        }}
        100% {{
            width: 100%;
        }}
    }}

    .loading-bar {{
        width: 100%;
        background-color: #ddd;
        position: relative;
    }}

    .loading-bar div {{
        height: 4px;
        background-color: {loading_bar_color};  # Set the color here
        width: 0;
        position: absolute;
        animation: loading 2s linear infinite;
    }}
    </style>
    """

    # Display the custom CSS style
    st.markdown(loading_bar_style, unsafe_allow_html=True)
    loading_container = st.empty()

    if playlist_name:
        loading_container.markdown('<div class="loading-bar"><div></div></div>', unsafe_allow_html=True)
        # This is where you instantiate the class
        p = Playlist(playlist_name)
        flag = True
        loading_container.empty()


    # If we have a valid playlist ID, proceed to fetch and display playlist data
    if flag:
        #st.balloons(bg_color="green")
        st.balloons()  # Show celebration balloons in the app
        run(p)
    cache_file = ".cache"
    if os.path.exists(cache_file):
        os.remove(cache_file)
if __name__ == '__main__':
    main()
