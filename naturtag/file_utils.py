"""File operations that don't fit anywhere else"""


def format_file_size(value):
    """Convert a file size in bytes into a human-readable format"""
    for unit in ['B','KB','MB','GB']:
        if abs(value) < 1024.0:
            return f'{value:.2f}{unit}'
        value /= 1024.0
    return f'{value:.2f}TB'
