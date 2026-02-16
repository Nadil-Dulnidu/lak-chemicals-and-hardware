from imagekitio import ImageKit


def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


imagekit = ImageKit(
    private_key=get_config_value("imagekit", "private_key"),
    public_key=get_config_value("imagekit", "public_key"),
    url_endpoint=get_config_value("imagekit", "url_endpoint"),
)
