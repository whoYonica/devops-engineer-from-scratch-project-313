from urllib.parse import urlparse

from pydantic import BaseModel, ValidationError, field_validator


class LinkSchema(BaseModel):
    original_url: str
    short_name: str

    @field_validator("original_url", mode="before")
    @classmethod
    def validate_original_url(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("URL is required")

        parsed_url = urlparse(value)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError("Invalid URL")

        return value

    @field_validator("short_name", mode="before")
    @classmethod
    def validate_short_name(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Short name is required")

        return value

def validate_link_data(data):
    try:
        link_data = LinkSchema.model_validate(data)
        return link_data, None

    except ValidationError as exc:
        errors = {}

        for error in exc.errors():
            field = error["loc"][0]

            if error["type"] == "missing":
                if field == "original_url":
                    errors[field] = "URL is required"
                else:
                    errors[field] = "Short name is required"

            elif error["type"] == "value_error":
                errors[field] = str(error["ctx"]["error"])

            else:
                errors[field] = error["msg"]

        return None, errors