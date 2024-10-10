from marshmallow import Schema, fields, ValidationError
from bson import ObjectId

# Custom validator for ObjectId (MongoDB format)
def validate_object_id(value):
    if not ObjectId.is_valid(value):
        raise ValidationError("Invalid user_id format.")

# Marshmallow schema for user_id validation
class ObjectIdSchema(Schema):
    id = fields.Str(required=True, validate=validate_object_id)