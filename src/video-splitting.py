# __copyright__   = "Copyright 2024, VISA Lab"
# __license__     = "MIT"
import os
import pathlib
import subprocess

from s3_utils import download_from_s3, S3_STAGE_1_BUCKET_NAME, S3_IN_BUCKET_NAME, upload_to_s3


def handler(event, context):
    try:
        # download s3 video
        s3_input_bucket = event['Records'][0]['s3']['bucket']['name']
        s3_input_key = event['Records'][0]['s3']['object']['key']
        input_path = f"/tmp/input/{s3_input_key}"
        pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
        download_from_s3(s3_input_bucket, s3_input_key, input_path)
        # feed local path to video splitting function
        s3_upload_key, local_output_path = video_splitting_cmdline(input_path)
        # get output and  save to output bucket
        upload_to_s3(S3_STAGE_1_BUCKET_NAME, s3_upload_key, local_output_path)
    except Exception as e:
        print(e)


def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    filename_without_extension = filename.split(".")[0]
    # outdir = os.path.splitext(filename)[0]
    # outdir = os.path.join("/tmp/output/", outdir)
    outdir = os.path.abspath("/tmp/output")
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # split_cmd = 'ffmpeg -ss 0 -r 1 -i ' + video_filename + ' -vf fps=1/10 -start_number 0 -vframes 10 ' + outdir + "/" + 'output-%02d.jpg -y'
    split_cmd = 'ffmpeg -i ' + video_filename + ' -vframes 1 ' + outdir+'/' + filename_without_extension + '.jpg -y'
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    # fps_cmd = 'ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    # fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    # fps = math.ceil(float(fps))
    return filename_without_extension + '.jpg', outdir+'/' + filename_without_extension + '.jpg'


# def main():
#     # download s3 video
#     s3_input_bucket = S3_IN_BUCKET_NAME
#     s3_input_key = "test_4.mp4"
#     input_path = f"/tmp/input/{s3_input_key}"
#     pathlib.Path(input_path).parent.mkdir(parents=True, exist_ok=True)
#     download_from_s3(s3_input_bucket, s3_input_key, input_path)
#     # feed local path to video splitting function
#     s3_upload_key, local_output_path = video_splitting_cmdline(input_path)
#     # get output and  save to output bucket
#     upload_to_s3(S3_STAGE_1_BUCKET_NAME, s3_upload_key, local_output_path)
#
#
# if __name__ == "__main__":
#     main()
