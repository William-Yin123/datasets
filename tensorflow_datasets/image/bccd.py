"""
BCCD (Blood Cell Count and Detection) Dataset is a small-scale dataset for blood cells detection.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow_datasets.public_api as tfds
import tensorflow as tf
import xml.etree.ElementTree as ET

_CITATION = """
@misc{shenggan_2019,
    title={Shenggan/BCCD_Dataset},
    url={https://github.com/Shenggan/BCCD_Dataset},
    journal={GitHub},
    author={Shenggan},
    year={2019},
    month={Nov}}
"""

_DESCRIPTION = """
BCCD (Blood Cell Count and Detection) Dataset is a small-scale dataset for blood cells detection.
12,500 augmented images of blood cells (JPEG) with accompanying cell type labels (CSV).
There are approximately 3,000 images for each of 4 different cell types grouped into 4 different folders (according to cell type).
The cell types are Eosinophil, Lymphocyte, Monocyte, and Neutrophil.
"""

_URL = "https://github.com/Shenggan/BCCD_Dataset"
_URL_BCCD = "https://raw.githubusercontent.com/Shenggan/BCCD_Dataset/master/BCCD"
_URL_TRAIN_TXT = _URL_BCCD + "/ImageSets/Main/train.txt"
_URL_Val_TXT = _URL_BCCD + "/ImageSets/Main/val.txt"
_URL_TEST_TXT = _URL_BCCD + "/ImageSets/Main/test.txt"
_URL_IMG = _URL_BCCD + "/JPEGImages"
_URL_XML = _URL_BCCD + "/Annotations"

def parse_annotations(annotation_path):
  root = ET.parse(annotation_path).getroot()
  cell_types, xmins, ymins, xmaxes, ymaxes = [], [], [], [], []
  for _object in root.findall("object"):
    cell_types.append(_object.find("name").text)
    xmins.append(int(_object.find("bndbox/xmin").text))
    ymins.append(int(_object.find("bndbox/ymin").text))
    xmaxes.append(int(_object.find("bndbox/xmax").text))
    ymaxes.append(int(_object.find("bndbox/ymax").text))
  return cell_types, xmins, ymins, xmaxes, ymaxes


class BCCD(tfds.core.GeneratorBasedBuilder):
  """
  BCCD Dataset
  """

  VERSION = tfds.core.Version('0.1.0')

  def _info(self):
    return tfds.core.DatasetInfo(
      builder=self,
      description=_DESCRIPTION,
      features=tfds.features.FeaturesDict({
        "name": tfds.features.Text(),
        "image": tfds.features.Image(shape=(480, 640, 3), encoding_format="jpeg"),
        "cell_type": tfds.features.Sequence(tfds.features.ClassLabel(names=["RBC", "WBC", "Platelets"])),
        "bbox_xmin": tfds.features.Sequence(tf.int32),
        "bbox_ymin": tfds.features.Sequence(tf.int32),
        "bbox_xmax": tfds.features.Sequence(tf.int32),
        "bbox_ymax": tfds.features.Sequence(tf.int32),
      }),
      citation=_CITATION,
      homepage=_URL
    )

  def _split_generators(self, dl_manager):
    url_txt_files = {
      "train": _URL_TRAIN_TXT,
      "val": _URL_Val_TXT,
      "test": _URL_TEST_TXT
    }
    txt_files = dl_manager.download(url_txt_files)

    splits = {
      "train": [],
      "val": [],
      "test": []
    }
    img_urls, xml_urls = {}, {}
    for split, txt_file in txt_files.items():
      with tf.io.gfile.GFile(txt_file, "r") as f:
        for name in f:
          name = name.strip()
          img_urls[name] = _URL_IMG + "/" + name + ".jpg"
          xml_urls[name] = _URL_XML + "/" + name + ".xml"
          splits[split].append({"name": name})
    img_downloads = dl_manager.download(img_urls)
    xml_downloads = dl_manager.download(xml_urls)
    for split, examples in splits.items():
      for example in examples:
        example["image"] = img_downloads[example["name"]]
        example["xml"] = xml_downloads[example["name"]]

    return [
      tfds.core.SplitGenerator(
        name=tfds.Split.TRAIN,
        gen_kwargs={"dataset": splits["train"]},
      ),
      tfds.core.SplitGenerator(
        name=tfds.Split.VALIDATION,
        gen_kwargs={"dataset": splits["val"]},
      ),
      tfds.core.SplitGenerator(
        name=tfds.Split.TEST,
        gen_kwargs={"dataset": splits["test"]},
      ),
    ]

  def _generate_examples(self, dataset):
    for example in dataset:
      cell_types, xmins, ymins, xmaxes, ymaxes = parse_annotations(example["xml"])
      yield example["name"], {
        "name": example["name"],
        "image": example["image"],
        "cell_type": cell_types,
        "bbox_xmin": xmins,
        "bbox_ymin": ymins,
        "bbox_xmax": xmaxes,
        "bbox_ymax": ymaxes
      }
