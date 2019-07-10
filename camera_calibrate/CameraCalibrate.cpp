// CV_LAB4.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//

#include "pch.h"
#include "opencv2/core/core.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/calib3d/calib3d.hpp"
#include "opencv2/highgui/highgui.hpp"
#include <iostream>
#include <string>
#include <fstream>

using namespace cv;
using namespace std;

//#define DEBUG

int main()
{
	string img_list_path = "D:/MyDearest/projects/RobotCvSystem/camera_calibrate/img_list.txt";
	//string img_list_path = "D:/MyDearest/lessons/CV/camera_calibrate_img_set/img_list.txt";
	ifstream fin; // 获取图片目录列表
	fin.open(img_list_path);
	// 对图片目录中的每一幅图像提取出角点，然后对角点进行亚像素精确化	
	int image_count = 0; 
	Size image_size; 
	Size board_size = Size(6, 9); // 标定板上角点的长宽规模
	vector<string> image_path_list; // 保存标定图片
	vector<Point2f> image_points;  // 一张图像上检测到的角点
	vector<vector<Point2f>> image_points_seq; // 所有图像的角点的序列
	string filename;
#ifdef DEBUG
	fin >> filename;
	std::cout << "FileName:"<<filename << endl;
#endif // DEBUG
	int count = -1; //用于存储角点个数。
	while (fin>>filename)
	{
		image_path_list.push_back(filename);
		image_count++;
		Mat image_input = imread(filename);
#ifdef DEBUG
		cout << "image_count = " << image_count << endl;
		cout << "-->count = " << count << '\t';
		cout << "Image file name: " << filename << endl;
		if (!image_input.data) {
			cout << "Image read failed" << endl;
		}
		imshow("img", image_input);
		waitKey(0);
#endif // DEBUG

		if (image_count == 1)  // 从第一张图片获取图像集尺寸
		{
			image_size.width = image_input.cols;
			image_size.height = image_input.rows;
			cout << "image_size.width = " << image_size.width << endl;
			cout << "image_size.height = " << image_size.height << endl;
		}

		// 第一次角点提取
		if (0 == findChessboardCorners(image_input, board_size, image_points))
		{
			cout << "can not find chessboard corners at image No."<< count << endl;
			exit(1);
		}
		else
		{
			Mat view_gray;
			cvtColor(image_input, view_gray, CV_RGB2GRAY);
			find4QuadCornerSubpix(view_gray, image_points, Size(5, 5)); // 对粗提取的角点进行精确化
			image_points_seq.push_back(image_points);  
			// 可视化验证
			drawChessboardCorners(view_gray, board_size, image_points, false); //用于在图片中标记角点
			imshow("Corners Check", view_gray);//显示图片
			waitKey(500); //暂停0.5S		
		}
	}
	fin.close();
	image_count = image_points_seq.size();
	cout << "Number of images: " << image_count << endl;
#ifdef DEBUG
	int corner_num = board_size.width*board_size.height;  //每张图片上总的角点数
	for (int ii = 0; ii < image_count; ii++)
	{
		if (0 == ii % corner_num)// 24 是每幅图片的角点个数。此判断语句是为了输出 图片号，便于控制台观看 
		{
			int i = -1;
			i = ii / corner_num;
			int j = i + 1;
			cout << "--> 第 " << j << "图片的数据 --> : " << endl;
		}
		if (0 == ii % 3)	// 此判断语句，格式化输出，便于控制台查看
		{
			cout << endl;
		}
		else
		{
			cout.width(10);
		}
		//输出所有的角点
		cout << " -->" << image_points_seq[ii][0].x;
		cout << " -->" << image_points_seq[ii][0].y;
	}
#endif // DEBUG
	cout << "角点提取完成" << endl;

	cout << "相机标定" << endl;
	Size square_size = Size(1, 1);  // 棋盘格的物理尺寸
	vector<vector<Point3f>> object_points; // 图像中角点的世界坐标	
	Mat camera_martrix = Mat(3, 3, CV_32FC1, Scalar::all(0)); //相机内参数矩阵
	Mat dist_coeffs = Mat(1, 5, CV_32FC1, Scalar::all(0)); // 5个畸变系数：k1,k2,p1,p2,k3 
	vector<Mat> t_vecs;  // 平移向量
	vector<Mat> r_vecs; // 旋转向量
	// 初始化每张图像中每个角点的世界坐标
	int i, j, t;
	for (t = 0; t < image_count; t++)
	{
		vector<Point3f> tmp_points_set;
		for (i = 0; i < board_size.height; i++)
		{
			for (j = 0; j < board_size.width; j++)
			{
				Point3f points_in_world;
				points_in_world.x = i * square_size.width;
				points_in_world.y = j * square_size.height;
				points_in_world.z = 0; // 假定标定板所在世界坐标系的z=0平面
				tmp_points_set.push_back(points_in_world);
			}
		}
		object_points.push_back(tmp_points_set);
	}
	calibrateCamera(object_points, image_points_seq, image_size, camera_martrix, dist_coeffs, r_vecs, t_vecs, 0);
	cout << "标定完成" << endl;


	//对标定结果进行评价
	cout << "评价标定结果" << endl;
	ofstream fout("caliberation_result.txt"); // 用于输出标定结果
	// 以完整标定板中的角点总数初始化每张图像中的角点数
	vector<int> point_counts; 
	for (i = 0; i < image_count; i++)
	{
		point_counts.push_back(board_size.width*board_size.height);
	}
	double total_err = 0.0; // 所有图像平均误差
	double err = 0.0;
	vector<Point2f> image_points_calc; // 通过畸变矫正得到的角点坐标
	cout << "\t每幅图像的标定误差：" << endl;
	fout << "每幅图像的标定误差：" << endl;
	for (i = 0; i < image_count; i++)
	{
		vector<Point3f> tmp_points_set = object_points[i];
		// 计算实际角点投影坐标
		projectPoints(tmp_points_set, r_vecs[i], t_vecs[i], camera_martrix, dist_coeffs, image_points_calc);
		// 误差计算
		vector<Point2f> tmp_points = image_points_seq[i];
		Mat tempImagePointMat = Mat(1, tmp_points.size(), CV_32FC2);
		Mat image_points2Mat = Mat(1, image_points_calc.size(), CV_32FC2);
		for (int j = 0; j < tmp_points.size(); j++)
		{
			image_points2Mat.at<Vec2f>(0, j) = Vec2f(image_points_calc[j].x, image_points_calc[j].y);
			tempImagePointMat.at<Vec2f>(0, j) = Vec2f(tmp_points[j].x, tmp_points[j].y);
		}
		err = norm(image_points2Mat, tempImagePointMat, NORM_L2);
		total_err += err /= point_counts[i];
		cout << "第" << i + 1 << "幅图像的平均误差：" << err << "像素" << endl;
		fout << "第" << i + 1 << "幅图像的平均误差：" << err << "像素" << endl;
	}
	cout << "总体平均误差：" << total_err / image_count << "像素" << endl;
	fout << "总体平均误差：" << total_err / image_count << "像素" << endl << endl;
	cout << "评价完成！" << endl;

	cout << "保存定标结果" << endl;
	Mat rotation_matrix = Mat(3, 3, CV_32FC1, Scalar::all(0)); 
	fout << "相机内参数矩阵：" << endl;
	fout << camera_martrix << endl << endl;
	fout << "畸变系数：" << endl;
	fout << dist_coeffs << endl << endl << endl;
	for (int i = 0; i < image_count; i++)
	{
		fout << "第" << i + 1 << "幅图像的旋转向量：" << endl;
		fout << t_vecs[i] << endl;

		Rodrigues(r_vecs[i], rotation_matrix); // 转换旋转向量为对应的旋转矩阵
		fout << "第" << i + 1 << "幅图像的旋转矩阵：" << endl;
		fout << rotation_matrix << endl;
		fout << "第" << i + 1 << "幅图像的平移向量：" << endl;
		fout << t_vecs[i] << endl << endl;
	}
	cout << "完成保存" << endl;
	fout << endl;

	// 可视化输出矫正结果
	cout << "保存矫正图像" << endl;
	stringstream str_stm;
	for (int i = 0; i != image_count; i++)
	{
		cout << "Image No." << i + 1 << "..." << endl;
		str_stm.clear();
		filename.clear();
		Mat image_src = imread(image_path_list[i]);
		Mat undisort_image = image_src.clone();
		undistort(image_src,undisort_image,camera_martrix,dist_coeffs);
		str_stm.clear();
		str_stm << i + 1;
		str_stm >> filename;
		filename += "_d.jpg";
		imwrite(filename, undisort_image);
	}
	cout << "保存结束" << endl;
	return 0;
}

// 运行程序: Ctrl + F5 或调试 >“开始执行(不调试)”菜单
// 调试程序: F5 或调试 >“开始调试”菜单

// 入门提示: 
//   1. 使用解决方案资源管理器窗口添加/管理文件
//   2. 使用团队资源管理器窗口连接到源代码管理
//   3. 使用输出窗口查看生成输出和其他消息
//   4. 使用错误列表窗口查看错误
//   5. 转到“项目”>“添加新项”以创建新的代码文件，或转到“项目”>“添加现有项”以将现有代码文件添加到项目
//   6. 将来，若要再次打开此项目，请转到“文件”>“打开”>“项目”并选择 .sln 文件
