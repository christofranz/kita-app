from marshmallow import Schema, fields, validate

class FcmTokenSchema(Schema):
    fcm_token = fields.Str(required=True, validate=validate.Length(min=140, max=200)) # typical range for fcm token


class FcmMessageSchema(Schema):
    fcm_token = fields.Str(required=True, validate=validate.Length(min=140, max=200)) # typical range for fcm token
    titel = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    body = fields.Str(required=True)

    class Meta:
        ordered = True  # This ensures that the fields are serialized in the order they are defined