from marshmallow import Schema, fields
from app.schemas.object_schema import validate_object_id

class EventFeedbackSchema(Schema):
    child_id = fields.Str(required=True, validate=validate_object_id)