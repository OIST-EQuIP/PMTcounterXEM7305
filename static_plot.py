#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 11:23:31 2022

@author: lucian
"""

# import matplotlib.pyplot as plt
# data_lst = [60, 59, 49, 51, 49, 52, 53]
# fig, ax = plt.subplots()
# ax.plot(data_lst)
# ax.set_xlabel('Day Number')
# ax.set_ylabel('Temperature (*F)')
# ax.set_title('Temperature in Portland, OR over 7 days')
# fig.savefig('static_plot.png')
# plt.show()
from random import randint

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# create empty lists for the x and y data
x = []
y = []

# create the figure and axes objects
fig, ax = plt.subplots()

def animate(i):
    pt = randint(1,9) # grab a random integer to be the next y-value in the animation
    x.append(i)
    y.append(pt)

    ax.clear()
    ax.plot(x, y)
    ax.set_xlim([0,200])
    ax.set_ylim([0,10])
# run the animation
ani = FuncAnimation(fig, animate, frames=40, interval=50, repeat=False)
#unit of interval is millisecond

plt.show()