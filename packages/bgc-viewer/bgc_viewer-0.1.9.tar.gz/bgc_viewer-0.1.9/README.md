# BGC Viewer

A viewer for biosynthetic gene cluster (BGC) data.


## Installation & run

Using Python 3.11 or higher, install and run the BGC Viewer as follows:

```bash
pip install bgc-viewer
bgc-viewer
```

This will start the BGC Viewer server, to which you can connect with your web browser.


## Configuration

Environment variables can be set to change the configuration of the viewer.
A convenient way to change them is to put a file called `.env` in the directory from
which you are running the application.

```bash
BGCV_HOST=localhost       # Server host (default: localhost)
BGCV_PORT=5005            # Server port (default: 5005)
BGCV_DEBUG_MODE=False     # Enable dev/debug mode (default: False)
BGCV_PUBLIC_MODE=False    # In public mode, there won't be an option to access the
                          # file system; the data directory will be fixed (default: False)
BGCV_DATA_DIR=/data_dir/  # In public mode, this data directory will be used
BGCV_ALLOWED_ORIGINS=https://yourdomain.com # Allowed CORS origins, relevant for public mode
```

## Development

See the repository [main README](../README.md#backend-python-package-development) for development details.

```bash
uv run python -m bgc_viewer.app
```

## License

Apache 2.0
