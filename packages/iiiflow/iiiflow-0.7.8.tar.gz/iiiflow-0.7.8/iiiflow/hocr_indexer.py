import os
import yaml
import pysolr
from lxml import etree
from lxml import html
from .utils import validate_config_and_paths

def index_hocr_to_solr(collection_id, object_id, skip_if_indexed=False, config_path="~/.iiiflow.yml"):
    """
    Parses hOCR files and indexes them into Solr for IIIF Content Search.

    Args:
        collection_id (str): The collection ID.
        object_id (str): The object ID.
        config_path (str): Path to the configuration YAML file.
        skip_if_indexed (bool): If True, skips indexing if object is already in Solr.
    """

    NS = {'x': 'http://www.w3.org/1999/xhtml'}

    # Resolve and load config
    if config_path.startswith("~"):
        config_path = os.path.expanduser(config_path)
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    lang_code = config.get("lang_code", "eng")
    solr_url = config.get("solr_url").rstrip("/")
    solr_core = config.get("solr_core")

    if not solr_core:
        raise ValueError("Missing 'solr_core' in config")

    solr_endpoint = f"{solr_url}/{solr_core}"
    solr = pysolr.Solr(solr_endpoint, always_commit=False, timeout=600)

    # Check if object is already indexed
    if skip_if_indexed:
        object_id_val = f"{collection_id}/{object_id}"
        results = solr.search(f"object_id_ssi:{object_id_val}", rows=1)
        if results.hits > 0:
            print(f"Skipping already-indexed object: {object_id_val}")
            return

    # Get paths
    discovery_storage_root, log_file_path, object_path = validate_config_and_paths(
        config_path, collection_id, object_id
    )
    obj_url_root = "https://media.archives.albany.edu"
    ocr_dir = os.path.join(object_path, "hocr")

    docs = []

    if not os.path.isdir(ocr_dir):
        print(f"hOCR directory not found: {ocr_dir}")
    else:

        print(f"Indexing OCR for {collection_id}/{object_id} into core '{solr_core}'...")
            
        page_count = 0

        #for hocr in sorted(os.scandir(ocr_dir), key=lambda x: x.name):
        for hocr in os.scandir(ocr_dir):
            page_count += 1
            canvas_id = f"{obj_url_root}/{collection_id}/{object_id}/canvas/p{page_count}"

            with open(hocr.path, 'r', encoding='utf-8') as f:
                tree = html.parse(f)

            words = []
            bboxes = []
            for word_span in tree.xpath("//span[contains(@class, 'ocrx_word')]", namespaces=NS):
                word = word_span.text or ''
                title = word_span.attrib.get("title", "")
                if 'bbox' in title:
                    bbox = title.split('bbox')[1].split(';')[0].strip()
                    bboxes.append({'word': word, 'bbox': bbox})
                words.append(word)

            full_text = ' '.join(words)

            doc = {
                'id': f"{collection_id}_{object_id}_p{page_count}",
                'canvas_id_ssi': canvas_id,
                'object_id_ssi': f"{collection_id}/{object_id}",
                f'ocr_text_{lang_code}_tsimv': full_text,
                f'ocr_hitbox_{lang_code}_tsm': [
                    f"{b['word']}|{b['bbox']}" for b in bboxes
                ],
                f'ocr_word_{lang_code}_ssim': [w.lower() for w in words],
            }

            docs.append(doc)

    if docs:
        BATCH_SIZE = 100
        for i in range(0, len(docs), BATCH_SIZE):
            solr.add(docs[i:i+BATCH_SIZE])
        solr.commit()
        print(f"Successfully indexed {page_count} pages for {object_id}")
    else:
        print("No hOCR documents found to index.")
