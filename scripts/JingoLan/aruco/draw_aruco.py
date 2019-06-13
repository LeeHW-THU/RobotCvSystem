import cv2
import cv2.aruco as aruco
import matplotlib.pyplot as plt
import matplotlib as mpl

# draw marker
fig = plt.figure()
nx = 4
ny = 3
aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
for i in range(1, nx*ny+1):
    ax = fig.add_subplot(ny, nx, i)
    img = aruco.drawMarker(aruco_dict, i, 700)
    plt.imshow(img, cmap = mpl.cm.gray, interpolation="nearest")
    ax.axis("off")

plt.savefig("marker.pdf")
plt.show()