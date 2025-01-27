import tensorflow as tf
import numpy as np
import os
import os.path
from scipy import misc
import argparse
import sys

g_mean = np.array(([126.88,120.24,112.19])).reshape([1,1,3])
output_folder = "./test_output"

def rgba2rgb(img):
	return img[:,:,:3]*np.expand_dims(img[:,:,3],2)

def main(args):
	
	if not os.path.exists(output_folder):
		os.mkdir(output_folder)	
	
	gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction = args.gpu_fraction)
	with tf.Session(config=tf.ConfigProto(gpu_options = gpu_options)) as sess:
		saver = tf.train.import_meta_graph('./meta_graph/my-model.meta')
		saver.restore(sess,tf.train.latest_checkpoint('./salience_model'))
		image_batch = tf.compat.v1.get_collection('image_batch')[0]
		pred_mattes = tf.compat.v1.get_collection('mask')[0]

		if args.rgb_folder:
			rgb_pths = os.listdir(args.rgb_folder)
			for rgb_pth in rgb_pths:
				rgb = misc.imread(os.path.join(args.rgb_folder,rgb_pth))
				if rgb.shape[2]==4:
					rgb = rgba2rgb(rgb)
				origin_shape = rgb.shape
				rgb = np.expand_dims(misc.imresize(rgb.astype(np.uint8),[320,320,3],interp="nearest").astype(np.float32)-g_mean,0)

				feed_dict = {image_batch:rgb}
				pred_alpha = sess.run(pred_mattes,feed_dict = feed_dict)
				final_alpha = misc.imresize(np.squeeze(pred_alpha),origin_shape)
				misc.imsave(os.path.join(output_folder,rgb_pth),final_alpha)

		else:
			origin_rgb = misc.imread(args.rgb)
			if origin_rgb.shape[2]==4:
				origin_rgb = rgba2rgb(origin_rgb)
			origin_shape = origin_rgb.shape[:2]
			rgb = np.expand_dims(misc.imresize(origin_rgb.astype(np.uint8),[320,320,3],interp="nearest").astype(np.float32)-g_mean,0)

			feed_dict = {image_batch:rgb}
			pred_alpha = sess.run(pred_mattes,feed_dict = feed_dict)
			final_alpha = misc.imresize(np.squeeze(pred_alpha),origin_shape)
			misc.imsave(output_path(output_folder, args.rgb, 'alpha_'), final_alpha)

			rgb_alpha = add_alpha_channel_to_rgb(final_alpha, origin_rgb)
			misc.imsave(output_path(output_folder, args.rgb, 'rgb_alpha_'), rgb_alpha)

def add_alpha_channel_to_rgb(alpha, rgb):
	s = alpha.shape
	return np.append(rgb, alpha.reshape((s[0], s[1], 1)), axis=2)

def output_path(output_folder, input_filename, prefix):
	return os.path.join(output_folder, prefix + os.path.splitext(os.path.basename(input_filename))[0] + '.png')

def parse_arguments(argv):
	parser = argparse.ArgumentParser()

	parser.add_argument('--rgb', type=str,
		help='input rgb',default = None)
	parser.add_argument('--rgb_folder', type=str,
		help='input rgb',default = None)
	parser.add_argument('--gpu_fraction', type=float,
		help='how much gpu is needed, usually 4G is enough',default = 1.0)
	return parser.parse_args(argv)


if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
