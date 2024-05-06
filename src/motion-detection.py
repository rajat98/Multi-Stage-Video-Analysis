__copyright__ = "Copyright 2024, VISA Lab"
__license__ = "MIT"

import os
import pathlib

import cv2
import imutils

from s3_utils import upload_frames, S3_STAGE_2_BUCKET_NAME, download_folder_from_s3, \
    is_folder_uploded_completeley


def detect(lgray, frame, min_area):
    frame = imutils.resize(frame, width=320)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    frameDelta = cv2.absdiff(lgray, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    thresh = cv2.dilate(thresh, None, iterations=2)
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    for c in contours:
        if cv2.contourArea(c) > min_area:
            return True, gray
    return False, gray


def motion_detection_function(folder_name):
    if not os.path.exists(folder_name):
        print(f"Folder {folder_name} does not exist!")
        return None

    # Motion detection specific parameters
    min_area = 10  # if 10% of the frame was changed, motion happens
    last_gray = None

    pics = sorted(os.listdir(folder_name))
    for pic in pics:
        path = os.path.join(folder_name, pic)
        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        if frame is None:
            print("failed to open picture %s" % path)
            return None

        if last_gray is None:
            frame = imutils.resize(frame, width=320)
            last_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_gray = cv2.GaussianBlur(last_gray, (21, 21), 0)
            continue

        detected, gray = detect(last_gray, frame, min_area)
        if detected:
            break
        else:
            last_gray = gray
            os.remove(path)
    return folder_name


def handler(event, context):
    try:
        # download s3 video
        s3_input_bucket = event['Records'][0]['s3']['bucket']['name']
        s3_input_key = event['Records'][0]['s3']['object']['key']

        # process folder once it is completely uploaded
        if not is_folder_uploded_completeley(s3_input_key):
            return
        base_folder = s3_input_key.split("/")[0]
        input_path = f"/tmp/input/{base_folder}"
        pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
        download_folder_from_s3(s3_input_bucket, base_folder, input_path)
        # feed local path to video splitting function
        outdir = motion_detection_function(input_path)
        # get output and  save to output bucket
        upload_frames(outdir, S3_STAGE_2_BUCKET_NAME)
    except Exception as e:
        print(e)

# local testing
# def main():
#     # download s3 video
#     s3_input_bucket = S3_STAGE_1_BUCKET_NAME
#     s3_input_key = "test_01/output_09.jpg"
#
#     # process folder once it is completely uploaded
#     if not is_folder_uploded_completeley(s3_input_key):
#         return
#     base_folder = s3_input_key.split("/")[0]
#     input_path = f"/tmp/input/{base_folder}"
#     pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
#     download_folder_from_s3(s3_input_bucket, base_folder, input_path)
#     # feed local path to video splitting function
#     outdir = motion_detection_function(input_path)
#     # get output and  save to output bucket
#     upload_frames(outdir, S3_STAGE_2_BUCKET_NAME)
#
# if __name__ == "__main__":
#     main()
