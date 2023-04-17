from rest_framework.renderers import JSONRenderer

class CustomJSONRenderer(JSONRenderer):
    charset = 'utf-8'
    json_dumps_params = {'ensure_ascii': False, 'indent': 2}
