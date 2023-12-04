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
import c
import time
from spotipy.oauth2 import SpotifyOAuth
import os

# Spotify app credentials from your Spotify Developer Dashboard
SPOTIPY_CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
SPOTIPY_CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
SPOTIPY_REDIRECT_URI = 'http://localhost:8080/'

# Create a SpotifyOAuth instance
#sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope='user-library-read')


# Real Main
def main():
    # Spotify app credentials from your Spotify Developer Dashboard
    SPOTIPY_CLIENT_ID = '2bdfeb8580304b9fb343ff8cc8744e76'
    SPOTIPY_CLIENT_SECRET = '73cbcc49de99490f821c2925c2b41419'
    SPOTIPY_REDIRECT_URI = 'http://localhost:8080/'

    st.title("Spotify Playlist Analyzer")

    # Load an image and display it in the Streamlit sidebar
    image = Image.open('Vibify.png')
    st.sidebar.image(image)



    # button_style = f"""
    # <style>
    #     /* Change the button border color to Spotify green */
    #     .stButton button {{
    #         border: 2px solid #1DB954 !important; /* Spotify green color */
    #         background-color: transparent !important; /* Make the button transparent */
    #         color: #1DB954 !important; /* Text color to Spotify green */
    #     }}
    # </style>
    # """

    # button_style = f"""
    # <style>
    #     /* Button style */
    #     .stButton button {{
    #         background-color: transparent !important;
    #         color: #1DB954 !important;
    #         border: 2px solid transparent !important;
    #         transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    #     }}
        
    #     /* Button hover style */
    #     .stButton button:hover {{
    #         background-color: #1DB954 !important; /* Green background on hover */
    #         border-color: #1DB954 !important; /* Green border on hover */
    #         color: white !important; /* White text on hover */
    #     }}
    # </style>
    # """
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
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(CLIENT_ID,
                                                       CLIENT_SECRET,
                                                       redirect_uri="http://localhost:8080/",
                                                       scope="playlist-read-private",  # Scope for reading playlists
                                                       show_dialog=True))

        user = sp.current_user()
        st.sidebar.success(f"Logged in as {user['display_name']}")

        # Get the playlists of the authenticated user
        playlists = sp.current_user_playlists()

        st.session_state.spotify_playlists = playlists['items']

        playlist_name = None


    # try:
    #     playlist_name
    # except NameError:
    #     playlist_name = st.sidebar.text_input("Enter the URL of the Spotify playlist:")






    # if st.sidebar.button("Log Out"):
    #     cache_file = ".cache"
    #     if os.path.exists(cache_file):
    #         os.remove(cache_file)
    #     st.session_state.spotify_playlists = None


        # Iterate through the playlists and print their names and external URLs
        #st.sidebar.subheader("Your Spotify Playlists:")
        #for idx, playlist in enumerate(playlists['items']):
            #st.sidebar.write(f"{idx + 1}. {playlist['name']}")
            #st.sidebar.write(f"   External URL: {playlist['external_urls']['spotify']}")
        # END


    #     # Print the contents of the session state variable
    # if 'spotify_playlists' in st.session_state:
    #     playlists = st.session_state.spotify_playlists
    #     for idx, playlist in enumerate(playlists):
    #         st.write(f"{idx + 1}. {playlist['name']}")
    #         st.write(f"   External URL: {playlist['external_urls']['spotify']}")
    # else:
    #     st.write("No Spotify playlists available. Please log in to Spotify.")

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





    # st.title("Spotify Playlist Analyzer")

    # # Load an image and display it in the Streamlit sidebar
    # image = Image.open('Vibify.png')
    # st.sidebar.image(image)

    # Keep
    # Create an input field in the sidebar for the Spotify playlist URL
    #if st.sidebar.text_input("Enter the URL of the Spotify playlist:"):
    # try:
    #     playlist_name
    # except NameError:
    #     playlist_name = st.sidebar.text_input("Enter the URL of the Spotify playlist:")



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
        p = c.Playlist(playlist_name)
        flag = True
        loading_container.empty()


    # If we have a valid playlist ID, proceed to fetch and display playlist data
    if flag:
        #st.balloons(bg_color="green")
        st.balloons()  # Show celebration balloons in the app
        c.run(p)
    cache_file = ".cache"
    if os.path.exists(cache_file):
        os.remove(cache_file)
if __name__ == '__main__':
    main()
