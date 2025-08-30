import facebook


class FaceAPI:
    def __init__(self, token):
        self.token = token
        self.graph = facebook.GraphAPI(access_token=token, version="2.12")

    def post(self, message, image):
        response = self.graph.put_photo(image=open(image, 'rb'), message=message)
        return response['post_id']

    def comment_post(self, post_id, message):
        self.graph.put_object(parent_object=f"{post_id}", connection_name='comments', message=message)