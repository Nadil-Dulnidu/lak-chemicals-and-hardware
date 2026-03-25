import uvicorn


def get_config_value(*keys, default=None):
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=get_config_value("server", "host"),
        port=get_config_value("server", "port"),
        reload=get_config_value("server", "reload"),
    )
