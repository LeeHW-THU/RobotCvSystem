# img set path generator
import os
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
file_list = os.listdir(current_dir)
# current_dir = "D://MyDearest//lessons//CV//LAB4//img_set//"
# current_dir = "D:/MyDearest/lessons/CV/LAB4/img_set/pirobot/"

ofile = open("img_list.txt",'w')
for file in file_list:
    if os.path.splitext(file)[1] == ".jpg":
        img_path = current_dir+'\\'+file
        # img_path = current_dir+file
        img_path.replace('\\','\/')
        ofile.write(img_path+'\n')
