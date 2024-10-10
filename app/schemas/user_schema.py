from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    firebase_id_token = fields.Str(required=True, validate=validate.Length(min=1))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    role = fields.Str(required=True, validate=validate.OneOf(["parent", "teacher"]))

    class Meta:
        ordered = True  # This ensures that the fields are serialized in the order they are defined


class LoginSchema(Schema):
    firebase_id_token = fields.Str(required=True, validate=validate.Length(min=1))


class PasswordResetSchema(Schema):
    email = fields.Email(required=True)