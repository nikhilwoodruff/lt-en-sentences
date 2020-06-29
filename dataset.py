import requests
import xml.etree.ElementTree as et
import argparse
import os
import shutil
from tqdm import tqdm

def get_safe_dir(*path_components):
    path = os.path.join(*path_components)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path

def download_data():
    url = "https://raw.githubusercontent.com/PerseusDL/dynamic-lexicon/master/data/auto-aligned-parallel-txts/latinParallelText/Perseus-text-1999.02.{:04}.xml"
    folder = get_safe_dir("texts", "xml")
    t = 1
    for i in tqdm(range(40), desc="Requesting text XML", position=0):
        text = requests.get(url.format(i), stream=True)
        if text.status_code == 200:
            with open(os.path.join(folder, "text_{}.xml".format(t)), mode="wb+") as f:
                chunk_size = 8192
                for chunk in tqdm(text.iter_content(chunk_size=chunk_size), total=int(text.headers['Content-Length']) // chunk_size, desc="Saving XML file", leave=False):
                    f.write(chunk)
            t += 1

def extract_sentences():
    source_folder = os.path.join("texts", "xml")
    target_folder = get_safe_dir("texts", "sentences")
    with open(os.path.join(target_folder, "latin.txt"), "w+", encoding="utf-8") as lt, open(os.path.join(target_folder, "english.txt"), "w+", encoding="utf-8") as en:
        for filename in tqdm(os.listdir(source_folder), desc="Extracting sentences"):
            with open(os.path.join(source_folder, filename), mode="rb") as xml:
                i = 0
                for event, element in tqdm(et.iterparse(xml, events=["start", "end"]), desc="Parsing XML", leave=False):
                    if event == "end" and element.tag == "wds":
                        i += 1
                        sentence = []
                        for word in element.findall("w"):
                            sentence.append(word[0].text)
                        if element.attrib["lnum"] == "L1":
                            lt.write(" ".join(sentence) + "\n")
                        else:
                            en.write(" ".join(sentence) + "\n")
                        element.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Retrieve and format data for use in Latin-English translation models.")
    parser.add_argument("mode", nargs="?", choices=["download", "extract"], help="Data function to execute")
    args = parser.parse_args()
    if args.mode is None:
        download_data()
        extract_sentences()
    elif args.mode == "download":
        download_data()
    elif args.mode == "extract":
        extract_sentences()