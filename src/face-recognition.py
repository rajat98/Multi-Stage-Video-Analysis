__copyright__ = "Copyright 2024, VISA Lab"
__license__ = "MIT"

import os
import pathlib

import cv2
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

from s3_utils import S3_OUTPUT_BUCKET_NAME, save_prediction_to_s3, \
    download_folder_from_s3, is_folder_uploded_completeley, S3_STAGE_3_BUCKET_NAME, S3_STAGE_1_BUCKET_NAME, \
    download_from_s3

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20)  # initializing mtcnn for face detection
resnet = InceptionResnetV1(pretrained='vggface2').eval()  # initializing resnet for face img to embeding conversion


def face_recognition_function(folder_name):
    if not os.path.exists(folder_name):
        print(f"Folder {folder_name} does not exist!")
        return None
    name = ""
    # pics = sorted(os.listdir(folder_name))
    return_names = dict()
    # for pic in pics:
    #     path = os.path.join(folder_name, pic)
    path = folder_name
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    face, prob = mtcnn(img, return_prob=True, save_path=None)
    saved_data = torch.load('tmp/data.pt')  # loading data.pt file
    if face != None:
        emb = resnet(face.unsqueeze(0)).detach()  # detech is to make required gradient false
        embedding_list = saved_data[0]  # getting embedding data
        name_list = saved_data[1]  # getting list of names
        dist_list = []  # list of matched distances, minimum distance is used to identify the person
        for idx, emb_db in enumerate(embedding_list):
            dist = torch.dist(emb, emb_db).item()
            dist_list.append(dist)
        idx_min = dist_list.index(min(dist_list))
        input_name = path.split("/")[-1].split(".")[0]
        return_names[input_name] = name_list[idx_min]
    return return_names


def handler(event, context):
    try:
        # download s3 video
        s3_input_bucket = event['Records'][0]['s3']['bucket']['name']
        s3_input_key = event['Records'][0]['s3']['object']['key']

        # process folder once it is completely uploaded
        # if not is_folder_uploded_completeley(s3_input_key):
        #     return
        base_folder = s3_input_key.split("/")[0]
        input_path = f"/tmp/input/{base_folder}"
        pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
        # download_folder_from_s3(s3_input_bucket, base_folder, input_path)
        download_from_s3(s3_input_bucket, base_folder, input_path)
        # feed local path to video splitting function
        results = face_recognition_function(input_path)
        # get output and  save to output bucket
        upload_files(results, S3_OUTPUT_BUCKET_NAME)
    except Exception as e:
        print(e)


def upload_files(results, s3_output_bucket):
    for input_key, result in results.items():
        input_key += ".txt"
        save_prediction_to_s3(s3_output_bucket, input_key, result)


# local testing
# def main():
#     # download s3 video
#     s3_input_bucket = S3_STAGE_1_BUCKET_NAME
#     s3_input_key = "test_4.jpg"
#
#     # process folder once it is completely uploaded
#     # if not is_folder_uploded_completeley(s3_input_key):
#     #     return
#     base_folder = s3_input_key.split("/")[0]
#     input_path = f"/tmp/input/{base_folder}"
#     pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
#     # download_folder_from_s3(s3_input_bucket, base_folder, input_path)
#     download_from_s3(s3_input_bucket, base_folder, input_path)
#     # feed local path to video splitting function
#     results = face_recognition_function(input_path)
#     # get output and  save to output bucket
#     upload_files(results, S3_OUTPUT_BUCKET_NAME)
#
#
# if __name__ == "__main__":
#     main()
