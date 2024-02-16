import boto3
import mimetypes
import requests
import io
import random
import string

def generate_random_string(length):
    characters = string.ascii_letters + string.digits  # include letters and digits
    return ''.join(random.choice(characters) for i in range(length))

class DigitalOcean:
    def __init__(self, **kwargs):
        self.client = self.get_spaces_client(
        region_name="sgp1",
        endpoint_url="https://goodchoice.sgp1.digitaloceanspaces.com",
        key_id="DO00BKPK4G69QBWTTHYV",
        secret_access_key="rUMWLzoaGRIIHzmtVYWjBPPx9lJ2VQd5gAdmMbZpcI0"
        )
        
    def get_spaces_client(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        region_name = kwargs.get("region_name")
        endpoint_url = kwargs.get("endpoint_url")
        key_id = kwargs.get("key_id")
        secret_access_key = kwargs.get("secret_access_key")

        session = boto3.session.Session()

        return session.client(
            's3',
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret_access_key
        )


    def upload_file_to_space(self, space_name, filestream, save_as, **kwargs):
        """
        :param spaces_client: Your DigitalOcean Spaces client from get_spaces_client()
        :param space_name: Unique name of your space. Can be found at your digitalocean panel
        :param file_src: File location on your disk
        :param save_as: Where to save your file in the space
        :param kwargs
        :return:
        """

        is_public = kwargs.get("is_public", False)

        extra_args = {
            'ACL': "public-read" if is_public else "private",
            "ContentType": "image/jpeg"
        }

        return self.client.upload_fileobj(
            filestream,
            space_name,
            save_as,
            # boto3.s3.transfer.S3Transfer.ALLOWED_UPLOAD_ARGS
            ExtraArgs=extra_args
        )

    
    def upload_img(self, imgurl, folder="goodchoice", filename=None):
        imgsrc = requests.get(imgurl).content
        if "jpg" not in filename:
            filename = filename + "/" + generate_random_string(20) + ".jpg"
        self.upload_file_to_space(
                folder,
                io.BytesIO(imgsrc),
                filename,
                is_public=True
            )
        #return f"https://goodchoice.sgp1.cdn.digitaloceanspaces.com/{folder}/{filename}"
        return f"https://goodchoice.sgp1.digitaloceanspaces.com/{folder}/{filename}"
    
    def upload_imgpil(self, imgpil, folder="goodchoice", filename=None):
        img_bytes = io.BytesIO()
        imgpil = imgpil.convert("RGB")
        imgpil.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()
        if "jpg" not in filename:
            filename = filename + "/" + generate_random_string(20) + ".jpg"
        self.upload_file_to_space(
                folder,
                io.BytesIO(img_bytes),
                filename,
                is_public=True
            )
        #return f"https://goodchoice.sgp1.cdn.digitaloceanspaces.com/{folder}/{filename}"
        return f"https://goodchoice.sgp1.digitaloceanspaces.com/{folder}/{filename}"

if __name__ == "__main__":
    do = DigitalOcean()
    print(do.upload_img("https://www.travelandleisure.com/thmb/SPUPzO88ZXq6P4Sm4mC5Xuinoik=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/eiffel-tower-paris-france-EIFFEL0217-6ccc3553e98946f18c893018d5b42bde.jpg",
                        "afdfa",
                        "test"))