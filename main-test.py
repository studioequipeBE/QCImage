from pymediainfo import MediaInfo

import timecode

# Avec cette librairie on récupère les info dont on a besoin dont le timecode début.

print('Hello')

filename = '/Users/mc-1/Desktop/MediaInfo_video/LeSautDuDiable_FTR_P2of2_H264_1080-239_25p_VO-TVR128-20_XX_XX_20210511_SEQ.mp4'

media_info = MediaInfo.parse(filename)

# ça marche avec un MOV mais pas un MP4 ...
print('First frame : ' + media_info.other_tracks[0].time_code_of_first_frame)

print()

# image_track = media_info.image_tracks[0]
"""print(
    f"{image_track.format} of {image_track.width}×{image_track.height} pixels"
    f" and {general_track.file_size} bytes."
)"""
