from django.core.exceptions import ValidationError


def validate_max_size(value, max_mb):
    """Reject an uploaded file larger than max_mb. Requires
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE >= the largest limit used here,
    or Django rejects the request before this validator ever runs."""
    if value and value.size > max_mb * 1024 * 1024:
        raise ValidationError(
            f"File too large ({value.size / 1024 / 1024:.1f} MB). "
            f"Maximum is {max_mb} MB."
        )


def validate_image_10mb(value):
    """For photos: gallery images, testimonials, ads, trekking package images."""
    validate_max_size(value, 10)


def validate_document_20mb(value):
    """For brochure PDFs and other downloadable documents."""
    validate_max_size(value, 20)


def validate_video_50mb(value):
    """For hero slide videos."""
    validate_max_size(value, 50)