from marshmallow import Schema, fields, validate

class SetRoleSchema(Schema):
    target_username = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    new_role = fields.Str(required=True, validate=validate.OneOf(["parent", "teacher", "admin"]))

    class Meta:
        ordered = True  # This ensures that the fields are serialized in the order they are defined