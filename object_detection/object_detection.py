import os
import cv2
import numpy as np
import tensorflow as tf
import multiprocessing
import zmq
#屏蔽TensorFlow_Log
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
def Massage(mode,data):
	context = zmq.Context()
	if mode=="SUB":
		ImgData = context.socket(zmq.SUB)
		ImgData.set_hwm(3)
		ImgData.setsockopt(zmq.SUBSCRIBE, b'')
		ImgData.connect("ipc:///run/toponavi/camera/raw.ipc")

		Img = ImgData.recv(copy=False)
		frame = np.frombuffer(Img, dtype=np.uint8)[:976*1312]
		frame = frame.reshape((976,1312))
		return frame
	if mode=="PUB":
		data=context.socket(zmq.PUB)
		socket.bind("ipc:///run/toponavi/object_detection/label.ipc")
		socket.send_string(data)

def read_classes(classes_path):
    with open(classes_path) as f:
        class_names = f.readlines()
    class_names = [c.strip() for c in class_names]
    return class_names

def print_boxes(image, out_scores, out_boxes, out_classes, class_names,need_class):
    h, w, _ = image.shape
    for i, c in reversed(list(enumerate(out_classes))):
        predicted_class = class_names[c]
        if predicted_class in need_class:
            box = out_boxes[i]
            score = out_scores[i]

            label = '{}'.format(predicted_class)
            score='{:.2f}'.format(score)

            ymin, xmin, ymax, xmax = box
            left, right, top, bottom = (xmin * w, xmax * w,
                                      ymin * h, ymax * h)

            top = max(0, np.floor(top + 0.5).astype('int32'))
            left = max(0, np.floor(left + 0.5).astype('int32'))
            bottom = min(h, np.floor(bottom + 0.5).astype('int32'))
            right = min(w, np.floor(right + 0.5).astype('int32'))
            
            #TUDO:Pub to ParticleFilter Module (label)
            #label-str
            Massage=Massage("PUB",label)
            #print(label,score, (left, top), (right, bottom))

    return image
def non_max_suppression(scores, boxes, classes, max_boxes=10, min_score_thresh=0.6):
    out_boxes = []
    out_scores = []
    out_classes = []
    if not max_boxes:
        max_boxes = boxes.shape[0]
    for i in range(min(max_boxes, boxes.shape[0])):
        if scores is None or scores[i] > min_score_thresh:
            out_boxes.append(boxes[i])
            out_scores.append(scores[i])
            out_classes.append(classes[i])

    out_boxes = np.array(out_boxes)
    out_scores = np.array(out_scores)
    out_classes = np.array(out_classes)

    return out_scores, out_boxes, out_classes

def object_detection(image, image_data, sess):

    image_tensor = sess.graph.get_tensor_by_name('image_tensor:0')
    detection_boxes = sess.graph.get_tensor_by_name('detection_boxes:0')
    detection_scores = sess.graph.get_tensor_by_name('detection_scores:0')
    detection_classes = sess.graph.get_tensor_by_name('detection_classes:0')
    num_detections = sess.graph.get_tensor_by_name('num_detections:0')
    
    #识别
    boxes, scores, classes, num = sess.run([detection_boxes, detection_scores, detection_classes, num_detections],
                                                    feed_dict={image_tensor: image_data})
    #调整维度
    boxes, scores, classes = np.squeeze(boxes), np.squeeze(scores), np.squeeze(classes).astype(np.int32)
    out_scores, out_boxes, out_classes = non_max_suppression(scores, boxes, classes)
    #输出目标位置
    class_names = read_classes('./coco_classes.txt')
    need_class=['bottle','sofa','cup','chair']
    image = print_boxes(image, out_scores, out_boxes, out_classes, class_names,need_class)
            
    return image

def real_time_image_detect(detection_graph):
    with detection_graph.as_default():
        with tf.Session() as sess:
            #TUDO:Sub from Control Module (camera)
            while True:
	            frame=Massage("SUB","frame")
	            image_data = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	            image_data_expanded = np.expand_dims(image_data, axis=0)
	            frame = object_detection(frame, image_data_expanded, sess)
def main():
	path_to_ckpt = './model.pb'
	detection_graph = tf.Graph()
	with detection_graph.as_default():
		od_graph_def = tf.GraphDef()
		with tf.gfile.GFile(path_to_ckpt, 'rb') as fid:
			serialized_graph = fid.read()
			od_graph_def.ParseFromString(serialized_graph)
			tf.import_graph_def(od_graph_def, name='')

	print('----Start Object Detection----')
	real_time_image_detect(detection_graph)

def run():
	process = multiprocessing.Process(target=main())
	process.start()
if __name__ == '__main__':
    run()
    exit()

  