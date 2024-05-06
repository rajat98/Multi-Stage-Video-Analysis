__copyright__ = "Copyright 2024, VISA Lab"
__license__ = "MIT"

import os
import pathlib
from shutil import rmtree

import cv2
from facenet_pytorch import MTCNN

from s3_utils import upload_frames, download_folder_from_s3, \
    is_folder_uploded_completeley, S3_STAGE_3_BUCKET_NAME

mtcnn = MTCNN(keep_all=True, device='cpu')


def face_extraction_function(folder_name):
    if not os.path.exists(folder_name):
        print(f"Folder {folder_name} does not exist!")
        return None

    pics = sorted(os.listdir(folder_name))
    for pic in pics:
        path = os.path.join(folder_name, pic)
        frame = cv2.imread(path, cv2.IMREAD_COLOR)
        boxes, _ = mtcnn.detect(frame)

        if boxes is None:
            rmtree(folder_name)
            return

        for box in boxes:
            cv2.rectangle(frame,
                          (int(box[0]), int(box[1])),
                          (int(box[2]), int(box[3])),
                          (0, 255, 0),
                          2)
            cv2.imwrite(path, frame)
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
        outdir = face_extraction_function(input_path)
        # get output and  save to output bucket
        upload_frames(outdir, S3_STAGE_3_BUCKET_NAME)
    except Exception as e:
        print(e)


# local testing
# def main():
#     # download s3 video
#     s3_input_bucket = S3_STAGE_2_BUCKET_NAME
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
#     outdir = face_extraction_function(input_path)
#     # get output and  save to output bucket
#     upload_frames(outdir, S3_STAGE_3_BUCKET_NAME)
#
#
# if __name__ == "__main__":
#     main()
