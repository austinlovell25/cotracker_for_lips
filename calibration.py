import os.path
import cv2 as cv
import glob
import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd
import subprocess
from pathlib import Path
import random
import string
import argparse

 
 
def calibrate_camera(images_folder, rows, columns, world_scaling):
    images_names = glob.glob(images_folder)
    images = []
    for imname in images_names:
        im = cv.imread(imname, 1)
        images.append(im)
 
    #criteria used by checkerboard pattern detector.
    #Change this if the code can't find the checkerboard
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    
    print(rows, columns, world_scaling)
    rows = int(rows) #number of checkerboard rows. Minus 1 from actual number
    columns = int(columns) #number of checkerboard columns. Minus 1 from actual number
    world_scaling = float(world_scaling) #change this to the real world square size. Or not. Currently, in cm
 
    #coordinates of squares in the checkerboard world space
    objp = np.zeros((rows*columns,3), np.float32)
    objp[:,:2] = np.mgrid[0:rows,0:columns].T.reshape(-1,2)
    objp = world_scaling* objp
 
    #frame dimensions. Frames should be the same size.
    width = images[0].shape[1]
    height = images[0].shape[0]
 
    #Pixel coordinates of checkerboards
    imgpoints = [] # 2d points in image plane.
 
    #coordinates of the checkerboard in checkerboard world space.
    objpoints = [] # 3d point in real world space
 
 
    for frame in images:
        #print(len(imgpoints))
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
 
        #find the checkerboard
        ret, corners = cv.findChessboardCorners(gray, (rows, columns), None)
 
        if ret == True:
            #Convolution size used to improve corner detection. Don't make this too large.
            conv_size = (11, 11)
 
            #opencv can attempt to improve the checkerboard coordinates
            corners = cv.cornerSubPix(gray, corners, conv_size, (-1, -1), criteria)

            objpoints.append(objp)
            imgpoints.append(corners)

    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, (width, height), None, None)
    print('rmse:', ret)
    #print('camera matrix:\n', mtx)
    #print('distortion coeffs:', dist)
    #print('Rs:\n', rvecs)
    #print('Ts:\n', tvecs)

    return mtx, dist, ret
 
def stereo_calibrate(mtx1, dist1, mtx2, dist2, frames_folder, rows, columns, world_scaling):
    #read the synched frames
    images_names = glob.glob(frames_folder)
    images_names = sorted(images_names)
    c1_images_names = images_names[:len(images_names)//2]
    c2_images_names = images_names[len(images_names)//2:]
 
    c1_images = []
    c2_images = []
    for im1, im2 in zip(c1_images_names, c2_images_names):
        _im = cv.imread(im1, 1)
        c1_images.append(_im)
 
        _im = cv.imread(im2, 1)
        c2_images.append(_im)
 
    #change this if stereo calibration not good.
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 100, 0.0001)

    rows = int(rows)  # number of checkerboard rows. Minus 1 from actual number. Old val 13
    columns = int(columns)  # number of checkerboard columns. Minus 1 from actual number. Old val 20
    world_scaling = float(world_scaling)  # change this to the real world square size. Or not. Currently, in cm. Old val 1.89

    #coordinates of squares in the checkerboard world space
    objp = np.zeros((rows*columns,3), np.float32)
    objp[:,:2] = np.mgrid[0:rows,0:columns].T.reshape(-1,2)
    objp = world_scaling* objp
 
    #frame dimensions. Frames should be the same size.
    width = c1_images[0].shape[1]
    height = c1_images[0].shape[0]
 
    #Pixel coordinates of checkerboards
    imgpoints_left = [] # 2d points in image plane.
    imgpoints_right = []
 
    #coordinates of the checkerboard in checkerboard world space.
    objpoints = [] # 3d point in real world space
 
    for frame1, frame2 in zip(c1_images, c2_images):
        #print(len(imgpoints_left))
        gray1 = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
        gray2 = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
        c_ret1, corners1 = cv.findChessboardCorners(gray1, (rows, columns), None)
        c_ret2, corners2 = cv.findChessboardCorners(gray2, (rows, columns), None)
 
        if c_ret1 == True and c_ret2 == True:
            corners1 = cv.cornerSubPix(gray1, corners1, (11, 11), (-1, -1), criteria)
            corners2 = cv.cornerSubPix(gray2, corners2, (11, 11), (-1, -1), criteria)

            objpoints.append(objp)
            imgpoints_left.append(corners1)
            imgpoints_right.append(corners2)
 
    stereocalibration_flags = cv.CALIB_FIX_INTRINSIC
    ret, CM1, dist1, CM2, dist2, R, T, E, F = cv.stereoCalibrate(objpoints, imgpoints_left, imgpoints_right, mtx1, dist1,
                                                                 mtx2, dist2, (width, height), criteria = criteria, flags = stereocalibration_flags)
 
    return R, T, imgpoints_left, imgpoints_right
 
def triangulate(mtx1, mtx2, R, T, uvs1, uvs2):
 
    uvs1 = np.array(uvs1)
    uvs2 = np.array(uvs2)

    #RT matrix for C1 is identity.
    RT1 = np.concatenate([np.eye(3), [[0],[0],[0]]], axis = -1)
    P1 = mtx1 @ RT1 #projection matrix for C1
 
    #RT matrix for C2 is the R and T obtained from stereo calibration.
    RT2 = np.concatenate([R, T], axis = -1)
    P2 = mtx2 @ RT2 #projection matrix for C2
 
    def DLT(P1, P2, point1, point2):
 
        A = [point1[1]*P1[2,:] - P1[1,:],
             P1[0,:] - point1[0]*P1[2,:],
             point2[1]*P2[2,:] - P2[1,:],
             P2[0,:] - point2[0]*P2[2,:]
            ]
        A = np.array(A).reshape((4,4))

        B = A.transpose() @ A
        from scipy import linalg
        U, s, Vh = linalg.svd(B, full_matrices = False)
 
        # print('Triangulated point: ')
        # print(Vh[3,0:3]/Vh[3,3])
        return Vh[3,0:3]/Vh[3,3]
 
    p3ds = []
    for uv1, uv2 in zip(uvs1, uvs2):
        _p3d = DLT(P1, P2, uv1, uv2)
        p3ds.append(_p3d)
    p3ds = np.array(p3ds)
    #print(f"{p3ds=}")

    return p3ds

def move_old_files(calib_dir):
    random_dir = ''.join(random.choices(string.ascii_uppercase, k=10))
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")
    print(f"Removing previous camera1.yml, camera2.yml, and stereo_coeffs.yml folders")
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")

    # os.mkdir(f"{calib_dir}/configs/scraps/{random_dir}")
    try:
        os.remove("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/camera1.yml")
        os.remove("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/camera2.yml")
        os.remove("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/stereo_coeffs.yml")
        os.remove("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/rmse.yml")
    except Exception as e:
        print("os.remove call failed.")

def save_coefficients(mtx, dist, path):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    cv_file = cv.FileStorage(path, cv.FILE_STORAGE_WRITE)
    cv_file.write("K", mtx)
    cv_file.write("D", dist)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()

def save_stereo_coefficients(_R, _T, _imgpoints_left, _imgpoints_right, path):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    # print(f"{R=}")
    # print(type(R))
    cv_file = cv.FileStorage(path, cv.FILE_STORAGE_WRITE)
    cv_file.write("R", _R)
    cv_file.write("T", _T)
    # cv_file.write("imgpoints_left", _imgpoints_left)
    # cv_file.write("imgpoints_right", _imgpoints_right)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()
    
    
def save_rmse(ret1, ret2, path):
    """ Save the RMSE for each camera. """
    cv_file = cv.FileStorage(path, cv.FILE_STORAGE_WRITE)
    cv_file.write("camera 1", ret1)
    cv_file.write("camera 2", ret2)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()



def load_coefficients(path):
    """ Loads camera matrix and distortion coefficients. """
    # FILE_STORAGE_READ
    cv_file = cv.FileStorage(path, cv.FILE_STORAGE_READ)

    # note we also have to specify the type to retrieve other wise we only get a
    # FileNode object back instead of a matrix
    camera_matrix = cv_file.getNode("K").mat()
    dist_matrix = cv_file.getNode("D").mat()

    cv_file.release()
    return [camera_matrix, dist_matrix]

def load_stereo_coefficients(path):
    """ Loads camera matrix and distortion coefficients. """
    # FILE_STORAGE_READ
    cv_file = cv.FileStorage(path, cv.FILE_STORAGE_READ)

    # note we also have to specify the type to retrieve other wise we only get a
    # FileNode object back instead of a matrix
    R = cv_file.getNode("R").mat()
    T = cv_file.getNode("T").mat()

    cv_file.release()
    return [R, T]

def flip_y(df):
    df["f1_lower_y"] = 2988 - df["f1_lower_y"]
    df["f2_lower_y"] = 2988 - df["f2_lower_y"]
    df["f1_upper_y"] = 2988 - df["f1_upper_y"]
    df["f2_upper_y"] = 2988 - df["f2_upper_y"]
    return df

def run_calibration(rows, columns, world_scaling, dir):
    dir = Path(dir).expanduser().resolve()
    mtx1, dist1, ret1 = calibrate_camera(images_folder=f'{dir}/D2/*', rows=rows, columns=columns,
                                         world_scaling=world_scaling)
    mtx2, dist2, ret2 = calibrate_camera(images_folder=f'{dir}/J2/*', rows=rows, columns=columns,
                                         world_scaling=world_scaling)

    save_coefficients(mtx1, dist1, f'{dir}/camera1.yml')
    save_coefficients(mtx2, dist2, f'{dir}/camera2.yml')
    save_rmse(ret1, ret2, f'{dir}/rmse.yml')

    R, T, imgpoints_left, imgpoints_right = stereo_calibrate(mtx1, dist1, mtx2, dist2, f'{dir}/synced/*', rows=rows,
                                                             columns=columns, world_scaling=world_scaling)
    save_stereo_coefficients(R, T, imgpoints_left, imgpoints_right, f'{dir}/stereo_coeffs.yml')

if __name__ == "__main__":
    if sys.argv[1] == "triangulate":
        tracker = sys.argv[2]
        exp_name = "exp"
        if tracker != "spiga" and tracker != "cotracker":
            print("Invalid tracker option")
            print("Correct usage: calibration.py test spiga/cotracker")
            exit(1)
        if len(sys.argv) > 3:
            exp_name = sys.argv[3]
            config_path = sys.argv[4]
            save_dir = sys.argv[5]
            if tracker == "spiga":
                time = sys.argv[6]

        Path(f"{exp_name}").mkdir(parents=True, exist_ok=True)

        mtx1, dist1 = load_coefficients(f"{config_path}/camera1.yml")
        mtx2, dist2 = load_coefficients(f"{config_path}/camera2.yml")
        R, T = load_stereo_coefficients(f"{config_path}/stereo_coeffs.yml")

        if tracker == "spiga":
            df = pd.read_csv("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/spiga_pts.csv")
        elif tracker == "cotracker":
            df = pd.read_csv("/home/kwangkim/Projects/cotracker_new/cotracker_pts.csv")
        df = flip_y(df)

        uvs1_lower = df[["f1_lower_x", "f1_lower_y"]].to_numpy()[0:600]
        uvs2_lower = df[["f2_lower_x", "f2_lower_y"]].to_numpy()[0:600]
        p3ds_lower = triangulate(mtx1, mtx2, R, T, uvs1_lower, uvs2_lower)
        np.savetxt(f'{exp_name}/{tracker}_lower_3dpts.txt',p3ds_lower)


        uvs1_upper = df[["f1_upper_x", "f1_upper_y"]].to_numpy()[0:600]
        uvs2_upper = df[["f2_upper_x", "f2_upper_y"]].to_numpy()[0:600]
        p3ds_upper = triangulate(mtx1, mtx2, R, T, uvs1_upper, uvs2_upper)
        np.savetxt(f'{exp_name}/{tracker}_upper_3dpts.txt',p3ds_upper)


        dist_array = np.ones(np.shape(p3ds_upper)[0])
        for i in range(np.shape(p3ds_upper)[0]):
            dist_array[i] = ((p3ds_upper[i][0] - p3ds_lower[i][0]) ** 2 + (p3ds_upper[i][1] - p3ds_lower[i][1]) ** 2 + (p3ds_upper[i][2] - p3ds_lower[i][2]) ** 2) ** 0.5
        np.savetxt(f'{save_dir}/cotracker_out/{exp_name}/{tracker}_3dist.txt',dist_array)

        stdv = np.std(dist_array, axis=0)
        min_val = np.min(dist_array, axis=0)
        max_val = np.max(dist_array, axis=0)
        mean = np.mean(dist_array, axis=0)
        med = np.median(dist_array, axis=0)
        stats_df = pd.DataFrame(
            {"stdv": stdv,
             "min": min_val,
             "max": max_val,
             "mean": mean,
             "median": med},
            index=[0]
        )
        stats_df.to_csv(f"{save_dir}/cotracker_out/{exp_name}/{tracker}_stats.csv")
        print(f"{stdv=}")

        fig, ax = plt.subplots()
        x = np.arange(np.shape(p3ds_upper)[0])
        ax.plot(x, dist_array*1, linewidth=2.0, c='r', label="3d euc. diff")
        legend = ax.legend(loc='upper right', shadow=True, fontsize='x-large')
        ax.set_xlabel('frames')
        ax.set_ylabel('3d Euclidean distance (mm)')
        ax.set_title('Difference between upper lip and lower lip point estimation')
        plt.savefig(f"{save_dir}/cotracker_out/{exp_name}/{tracker}_3d_distance")
        # print(f"Saving image to {save_dir}/cotracker_out/{exp_name}/{tracker}_3d_distance")

        # if tracker == "spiga":
        #     cmd = f"mkdir -p {save_dir}/SPIGA_out/{time}/"
        #     subprocess.run(cmd, shell=True)
        #     cmd = f"mv /home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/{exp_name} {save_dir}/SPIGA_out/{time}/data"
        #     subprocess.run(cmd, shell=True)
        # else:
        #     cmd = f"mv /home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/{exp_name} {save_dir}/cotracker_out/{exp_name}/data"
        #     subprocess.run(cmd, shell=True)

    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--run", help="ignore")
        parser.add_argument("--rows", type=int, help="Rows on checkerboard")
        parser.add_argument("--columns", type=int, help="Columns on checkerboard")
        parser.add_argument("--scaling", type=int, help="World scaling, default is 15", default=15)
        parser.add_argument("--dir", type=Path, help="Directory with videos and calibration files")
        args = parser.parse_args()
        rows = args.rows
        columns = args.columns
        world_scaling = args.scaling
        dir = args.dir.expanduser().resolve()
        mtx1, dist1, ret1 = calibrate_camera(images_folder=f'{dir}/D2/*', rows=rows, columns=columns, world_scaling=world_scaling)
        mtx2, dist2, ret2 = calibrate_camera(images_folder=f'{dir}/J2/*', rows=rows, columns=columns, world_scaling=world_scaling)
        # print(f"{mtx1=}")
        # print(f"{dist1=}")

        # calib_dir = "/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration"
        # move_old_files(calib_dir)

        save_coefficients(mtx1, dist1, f'{dir}/camera1.yml')
        save_coefficients(mtx2, dist2, f'{dir}/camera2.yml')
        save_rmse(ret1, ret2, f'{dir}/rmse.yml')

        #R, T = stereo_calibrate(mtx1, dist1, mtx2, dist2, '/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/synced/*')
        R, T, imgpoints_left, imgpoints_right = stereo_calibrate(mtx1, dist1, mtx2, dist2, f'{dir}/synced/*', rows=rows, columns=columns, world_scaling=world_scaling)
        save_stereo_coefficients(R, T, imgpoints_left, imgpoints_right, f'{dir}/stereo_coeffs.yml')


        # str1 = f"rm -rf {calib_dir}/configs/{config_name}"
        # subprocess.run(str1, shell=True)
        # os.mkdir(f"{calib_dir}/configs/{config_name}")
        # str1 = f"cp {calib_dir}/camera1.yml {calib_dir}/configs/{config_name}/camera1.yml"
        # subprocess.run(str1, shell=True)
        # str1 = f"cp {calib_dir}/camera2.yml {calib_dir}/configs/{config_name}/camera2.yml"
        # subprocess.run(str1, shell=True)
        # str1 = f"cp {calib_dir}/stereo_coeffs.yml {calib_dir}/configs/{config_name}/stereo_coeffs.yml"
        # subprocess.run(str1, shell=True)
        # str1 = f"cp {calib_dir}/rmse.yml {calib_dir}/configs/{config_name}/rmse.yml"
        # subprocess.run(str1, shell=True)

