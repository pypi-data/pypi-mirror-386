from shapely.geometry import Polygon
import time
import numpy as np

import matplotlib.pyplot as plt


polys = [
  np.array([[100,  100],
 [150,  80],
 [250, 150],
 [300, 110],
 [350, 200],
 [300, 200],
 [500, 220],
 [450, 270],
 [200, 250],
 [200, 270],
 [100, 250],
 [130, 200],
 [100, 100]]) * 3.5,
        
 np.array([[400, 400],
 [600, 400],
 [600, 200],
 [400, 200],
 [400, 400]]),

 np.array([[800,600],
 [1000, 600],
 [1000, 200],
 [800, 200],
 [800, 600]]),

 np.array([[1200,400],
 [1400, 400],
 [1400, 600],
 [1200, 600],
 [1200, 400]]),

 np.array([[600,800],
 [800, 800],
 [800, 600],
 [600, 600],
 [600, 800]]),

 np.array([[1100,800],
 [1150, 800],
 [1150, 400],
 [1100, 400],
 [1100, 800]])
      ]


polys_sh = []
for poly in polys:
  poly_sh = Polygon(list(poly))
  polys_sh.append(poly_sh)
  
intersections = []

start_time = time.time()
for poly in polys_sh[1:]:
  intersect = polys_sh[0].intersection(poly)
  # intersections.append(intersect)
  # print(intersect)
print("--- %s seconds ---" % (time.time() - start_time))