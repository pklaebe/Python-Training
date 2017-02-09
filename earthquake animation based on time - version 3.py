# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All Rights Reserved.
# modifications:
# Copyright (c) 2017 Peter Klaebe. All Rights Reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
# Based on : https://peak5390.wordpress.com
# -> 2012/12/08/matplotlib-basemap-tutorial-plotting-global-earthquake-activity/
# -----------------------------------------------------------------------------
import urllib
import numpy as np
import matplotlib
matplotlib.rcParams['toolbar'] = 'None'
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.basemap import Basemap
from  matplotlib.animation import FuncAnimation
from datetime import date, datetime, timedelta

# Open the earthquake data
# -------------------------
# -> http://earthquake.usgs.gov/earthquakes/feed/v1.0/csv.php
feed = "http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/"

# Significant earthquakes in the past 30 days
# url = urllib.urlopen(feed + "significant_month.csv")

# Earthquakes of magnitude > 4.5 in the past 30 days
#url = urllib.urlopen(feed + "4.5_month.csv")
url = urllib.urlopen("file:///C:/Python27/Training/earthquakes%20greater%20than%204.9%20-%2020000101%20to%2020091231.csv")

# Earthquakes of magnitude > 2.5 in the past 30 days
#url = urllib.urlopen(feed + "2.5_month.csv")

# Earthquakes of magnitude > 1.0 in the past 30 days
#url = urllib.urlopen(feed + "1.0_month.csv")

# Set earthquake data
data = url.read()
data = data.split(b'\n')[+1:-1]
E = np.zeros(len(data), dtype=[('datetime', datetime),
                               ('position',  float, 2),
                               ('magnitude', float, 1),
                               ('date', str, 24),
                               ('place', str, 80)])

for i in range(len(data)):
    row = data[i].split(b',')

    E['date'][i] = str(row[0])
    E['datetime'][i] = datetime.strptime(E['date'][i], "%Y-%m-%dT%H:%M:%S.%fZ")
    E['position'][i] = float(row[2]),float(row[1])
    E['magnitude'][i] = float(row[4])
    E['place'][i] = str(row[13])

# sort quakes with oldest first in list
E = np.sort(E,order='date')

# start of earthquakes
start_time = E['datetime'][0]
end_time = E['datetime'][len(E)-1]
elapsed_duration = (end_time - start_time).total_seconds()

fig = plt.figure(figsize=(20,15))
ax = plt.subplot(1,1,1)
P = np.zeros(200, dtype=[('position', float, 2),
                        ('magnitude', float, 1),
                        ('size',     float, 1),
                        ('growth',   float, 1),
                        ('color',    float, 4)])


# Basemap projection, with Pacific Ocean viewed in entirety to see "ring of fire"
#map = Basemap(projection='cyl',llcrnrlat=-90,urcrnrlat=90,llcrnrlon=-20,urcrnrlon=340)
map = Basemap(projection='cyl',lon_0=160,lat_0=0)
map.drawcoastlines(color='0.50', linewidth=0.25)
map.fillcontinents(color='0.95')
scat = ax.scatter(P['position'][:,0], P['position'][:,1], s=P['size'], lw=0.5,
                  edgecolors = P['color'], facecolors='None', zorder=10)


# add wrap-around point in longitude
for i in range(len(data)):
    if E['position'][i][0] < 0:
        E['position'][i][0] += 360


interval = 50
quake = 0
current = 0
elapsed_time = start_time

# change the animation rate based on elapsed duration of earthquakes
if elapsed_duration >= 86400*7*52:    #more than 1 year
    elapsed_seconds_per_frame = timedelta(seconds=3.5 * 86.4 * interval)  #half week elapsed = one second animation time
    total_frames = elapsed_duration / (interval*3.5*86.4)
elif elapsed_duration >= 86400*7*26:    #more than 6 months, but less than a year
    elapsed_seconds_per_frame = timedelta(seconds=3.5 * 86.4 * interval)  #half week elapsed = one second animation time
    total_frames = elapsed_duration / (interval*3.5*86.4)
else:                                  #less than 6 months
    elapsed_seconds_per_frame = timedelta(seconds= 86.4 * interval)  #one day elapsed = one second animation time
    total_frames = elapsed_duration / (interval*86.4)

x_axis_place = " "
frames_elapsed = 0

for i in range(len(P)):
    P['magnitude'][i]=1 #avoid divide by zero in update function

def update(frame):
    global quake, start_time, elapsed_time, elapsed_seconds_per_frame, frames_elapsed, current, x_axis_place

    elapsed_time = elapsed_time + elapsed_seconds_per_frame

    #calculate color and size of earthquakes from last frame
    P['color'][:,3] = np.maximum(0, P['color'][:,3] - 0.1/P['magnitude'][:])  # color fades out slowly every frame, faster for smaller quakes
    P['size'] += P['growth']

    # if elapsed time between current quake and last one is more than elapsed time per frame, then we need to show current quake
    while (E['datetime'][current] < elapsed_time):

        #calculate position & size & color of the next earthquake
        magnitude = P['magnitude'][quake] = E['magnitude'][current]
        P['position'][quake] = map(*E['position'][current])
        P['size'][quake] = 20
        P['growth'][quake]= np.exp(magnitude) * 0.1

        if magnitude >= 8:
            P['color'][quake]    = 0,0,0,1  #black
            x_axis_place = E['place'][current]
            frames_elapsed = 1
        elif magnitude >= 7:
            P['color'][quake]    = 1,0,0,1  #red
        elif magnitude >= 6:
            P['color'][quake]    = 1,0,1,1  #purple
        elif magnitude >= 5:
            P['color'][quake]    = 0,0,1,0.75  #blue
        elif magnitude >= 4:
            P['color'][quake]    = 1,1,0,0.66  #yellow
        else:
            P['color'][quake]    = 0,1,0,0.5  #green

        quake = (quake + 1) % len(P)
        current = (current + 1) % len(E)
        if current == 0:     #break when looping around again
            break

    #draw the new frame
    scat.set_edgecolors(P['color'])
    scat.set_facecolors(P['color']*(1,1,1,0.5))
    scat.set_sizes(P['size'])
    scat.set_offsets(P['position'])

    #keep track of when to blank out mega quake location (after 3 seconds)
    frames_elapsed += 1
    if frames_elapsed > (3000/interval):
        x_axis_place = " "
        frames_elapsed = 0

    #show current elapsed time ticking over each frame
    plt.xlabel(str(elapsed_time)[0:16] + " Z    \n" + x_axis_place)

    return scat

plt.title("Earthquakes > 4.5 over time")

# plot legend
black_patch = mpatches.Patch(color='black', label='>= 8')
red_patch = mpatches.Patch(color='red', label='>= 7')
purple_patch = mpatches.Patch(color=(1,0,1,1), label='>= 6')
blue_patch = mpatches.Patch(color=(0,0,1,0.75), label='>= 5')
yellow_patch = mpatches.Patch(color=(1,1,0,0.66), label='>= 4')
plt.legend(handles=[black_patch,red_patch,purple_patch,blue_patch,yellow_patch],loc='lower left', title='Magnitude')

#animation = FuncAnimation(fig, update, interval=interval)   # loop forever, don't use if saving to a file

#this stops after count of earthquakes frames, changing repeat to True will loop with one second delay
animation = FuncAnimation(fig, update, frames=int(total_frames), interval=interval, repeat=False, repeat_delay=1000)
animation.save('earthquakes from 2000 to 2009 - version 8.mp4', writer='ffmpeg', fps=20, dpi=200)

#plt.show()

