from logging import getLogger
from os.path import isfile, splitext

from pyexiv2 import Image

# Minimal XML content needed to create a new XMP file; exiv2 can handle the rest
NEW_XMP_CONTENTS = """
<?xpacket?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="">
</x:xmpmeta>
<?xpacket?>
"""

logger = getLogger().getChild(__name__)


class ImageMetadata:
    """ Class for reading & writing basic image metadata """

    def __init__(self, image_path):
        self.image_path = image_path.decode() if isinstance(image_path, bytes) else image_path
        self.xmp_path = splitext(self.image_path)[0] + '.xmp'
        self.exif, self.iptc, self.xmp = self.read_metadata()

    def read_metadata(self):
        """ Read all formats of metadata from image + sidecar file """
        exif, iptc, xmp = self._safe_read_metadata(self.image_path)
        if isfile(self.xmp_path):
            s_exif, s_iptc, s_xmp = self._safe_read_metadata(self.xmp_path)
            exif.update(s_exif)
            iptc.update(s_iptc)
            xmp.update(s_xmp)

        paths = self.image_path + (f' + {self.xmp_path}' if isfile(self.xmp_path) else '')
        counts = ' | '.join([f'EXIF: {len(exif)}', f'IPTC: {len(iptc)}', f'XMP: {len(xmp)}'])
        logger.info(f'Total tags found in {paths}: {counts}')

        return exif, iptc, xmp

    def _safe_read_metadata(self, path, encoding='utf-8'):
        """ Attempt to read metadata, with error handling """
        logger.info(f'Reading metadata from: {path} ({encoding})')
        img = self.read_exiv2_image(path)
        if not img:
            return {}, {}, {}

        try:
            exif = img.read_exif(encoding=encoding)
            iptc = img.read_iptc(encoding=encoding)
            xmp = img.read_xmp(encoding=encoding)
        except UnicodeDecodeError:
            logger.warning(f'Non-UTF-encoded metadata in {path}')
            return self._safe_read_metadata(path, encoding='unicode_escape')
        finally:
            img.close()

        return exif, iptc, xmp

    @property
    def has_sidecar(self):
        return isfile(self.xmp_path)

    @staticmethod
    def read_exiv2_image(path):
        """
        Read an image with basic error handling. Note: Exiv2 ``RuntimeError`` usually means
        corrupted metadata. See: https://dev.exiv2.org/issues/637#note-1
        """
        try:
            return Image(path)
        except RuntimeError as exc:
            logger.error(f'Failed to read corrupted metadata from {path}:\n  {str(exc)}')
            return None

    def create_xmp_sidecar(self):
        """ Create a new XMP sidecar file if one does not already exist """
        if isfile(self.xmp_path):
            return
        logger.info(f'Creating new XMP sidecar file: {self.xmp_path}')
        with open(self.xmp_path, 'w') as f:
            f.write(NEW_XMP_CONTENTS.strip())

    def update(self, new_metadata):
        """ Update arbitrary EXIF, IPTC, and/or XMP metadata """
        logger.info(f'Updating with {len(new_metadata)} tags')

        def _filter_tags(prefix):
            return {k: v for k, v in new_metadata.items() if k.startswith(prefix)}

        # Split combined metadata into individual formats
        self.exif.update(_filter_tags('Exif.'))
        self.iptc.update(_filter_tags('Iptc.'))
        self.xmp.update(_filter_tags('Xmp.'))

    def write(self, create_xmp_sidecar=True):
        """ Write current metadata to image and sidecar """
        self._write(self.image_path)
        if create_xmp_sidecar:
            self.create_xmp_sidecar()
        if isfile(self.xmp_path):
            self._write(self.xmp_path)
        else:
            logger.info(f'No existing XMP sidecar file found for {self.image_path}; skipping')

    def _write(self, path):
        """ Write current metadata to a single path """
        logger.info(f'Writing tags to {path}')
        img = self.read_exiv2_image(path)
        # TODO: Possible workaround to enable overwriting corrupted metadata?
        if img:
            img.modify_exif(self.exif)
            img.modify_iptc(self.iptc)
            img.modify_xmp(self.xmp)
            img.close()
