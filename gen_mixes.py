import youtube_dl
import utils
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import numpy as np

from cvcalib.audiosync import offset

curr_dir = "/home/sean/Documents/experiments/stage-mix-generator/"
download_dir = os.path.join(curr_dir, 'temp')

# get top kpop songs
song_titles = [
    'Chung ha Gotta Go',
    'BTS Boy With Luv',
    'Blackpink Kill This Love',
    'ITZY DALLA DALLA'
]

LA_FMT = '140'
LA_EXT = 'm4a'

SV_FMT = '137'
SV_EXT = 'mp4'

SA_FMT = '140'
SA_EXT = 'm4a'

for song_title in song_titles:

    # get lyrics and stage videos from search
    lyrics_video_url = utils.yt_search(song_title+' lyrics')[0]
    stage_video_urls = utils.yt_search(song_title+' live performance', exclude='stage mix')[:5]

    # download videos
    utils.download_yt_video(lyrics_video_url, LA_FMT, LA_EXT, download_dir, f"lyrics_audio.{LA_EXT}")
    for i, url in enumerate(stage_video_urls):
        try:
            utils.download_yt_video(url, SV_FMT, SV_EXT, download_dir, f"stage_video{i}.{SV_EXT}")
            utils.download_yt_video(url, SA_FMT, SA_EXT, download_dir, f"stage_audio{i}.{SA_EXT}")
        except Exception as e:
            print(e)
            stage_video_urls.remove(url)

    lyrics_audio_path = os.path.join(download_dir, f"lyrics_audio.{LA_EXT}")
    stage_video_paths = [ os.path.join(download_dir, f"stage_video{i}.{SV_EXT}") for i in range(len(stage_video_urls)) ]
    stage_audio_paths = [ os.path.join(download_dir, f"stage_audio{i}.{SA_EXT}") for i in range(len(stage_video_urls)) ]
    
    # find timestamp of start of song in stage videos
    stage_song_starts = []
    for i in range(len(stage_video_urls)):
        try:
            output = offset.find_time_offset([f"lyrics_audio.{LA_EXT}", f"stage_audio{i}.{SA_EXT}"], download_dir+'/', [0, 0])
            print(output)
            stage_song_starts.append(output[0])
        except Exception as e:
            print(e)
            stage_song_starts.append((1, 0))
    
    # get subclips of the song in the stage videos
    stage_videos, stage_audios = [], []
    for i in range(len(stage_video_paths)):
        if stage_song_starts[i][0] == 0:
            stage_videos.append(VideoFileClip(stage_video_paths[i]).subclip(stage_song_starts[i][1]))
            stage_audios.append(AudioFileClip(stage_audio_paths[i]).subclip(stage_song_starts[i][1]))
    
    # load lyrics audio
    lyrics_audio = AudioFileClip(lyrics_audio_path)

    # every 5 seconds during the song, splice clips from different performances
    clips = []
    stage_video_idx = 0
    for step in np.arange(0, lyrics_audio.duration, 5):
        if step+5 < stage_videos[stage_video_idx].duration:
            clips.append(stage_videos[stage_video_idx].subclip(step, step+5))
        
        stage_video_idx = (stage_video_idx + 1) % len(stage_videos)

    # assemble clips 
    final_clip = concatenate_videoclips(clips)

    # replace audio with lyrics video
    #final_clip = final_clip.set_duration(lyrics_video.duration)
    #final_clip = final_clip.set_audio(lyrics_video.audio)

    # replace audio with first stage video
    final_clip = final_clip.set_audio(stage_audios[0])

    # write mix
    final_clip.write_videofile(f"{song_title}-stage_mix.mp4")