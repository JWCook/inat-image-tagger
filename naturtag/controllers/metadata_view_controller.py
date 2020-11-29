import json


# TODO: This screen is pretty ugly. Ideally this would be a collection of DataTables.
class MetadataViewController:
    """ Controller class to manage image metadata screen """

    def __init__(self, screen, **kwargs):
        self.combined = screen.combined
        self.exif = screen.exif
        self.iptc = screen.iptc
        self.xmp = screen.xmp
        self.keywords = screen.keywords

    def select_metadata(self, metadata):
        self.combined.text = json.dumps(metadata.combined, indent=4)
        self.keywords.text = (
            'Normal Keywords:\n'
            + json.dumps(metadata.keyword_meta.flat_keywords, indent=4)
            + '\n\n\nHierarchical Keywords:\n'
            + metadata.keyword_meta.hier_keyword_tree_str
        )
        self.exif.text = json.dumps(metadata.exif, indent=4)
        self.iptc.text = json.dumps(metadata.iptc, indent=4)
        self.xmp.text = json.dumps(metadata.xmp, indent=4)
