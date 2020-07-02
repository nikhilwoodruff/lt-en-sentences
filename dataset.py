import requests
import xml.etree.ElementTree as et
import argparse
import os
import shutil
from tqdm import tqdm
import unicodedata
import re

class DatasetConstructor:    
    def run(self, mode):
        if mode == "download" or mode is None:
            self.download_data()
        if mode == "extract" or mode is None:
            self.extract_sentences()
        if mode == "preprocess" or mode is None:
            self.preprocess()

    def _get_safe_dir(self, *path_components):
        path = os.path.join(*path_components)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        return path

    def download_data(self):
        url = "https://raw.githubusercontent.com/PerseusDL/dynamic-lexicon/master/data/auto-aligned-parallel-txts/latinParallelText/Perseus-text-1999.02.{:04}.xml"
        folder = self._get_safe_dir("texts", "xml")
        t = 1
        for i in tqdm(range(40), desc="Requesting text XML", position=0):
            text = requests.get(url.format(i), stream=True)
            if text.status_code == 200:
                with open(os.path.join(folder, "text_{}.xml".format(t)), mode="wb+") as f:
                    chunk_size = 8192
                    for chunk in tqdm(text.iter_content(chunk_size=chunk_size), total=int(text.headers['Content-Length']) // chunk_size, desc="Saving XML file", leave=False):
                        f.write(chunk)
                t += 1

    def extract_sentences(self):
        source_folder = os.path.join("texts", "xml")
        target_folder = self._get_safe_dir("texts", "sentences")
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
    
    def _unicode_to_ascii(self, string):
        return ''.join(c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn')

    def _preprocess_sentence(self, sentence):
        w = self._unicode_to_ascii(sentence.lower().strip())
        w = re.sub(r"([?.!,¿])", r" \1 ", w)
        w = re.sub(r'[" "]+', " ", w)
        w = re.sub(r"[^a-zA-Z?.!,¿]+", " ", w)
        w = w.strip()
        w = "<start> {} <end>".format(w)
        return w
    
    def _preprocess_file(self, input_file, output_file, language=""):
        with open(input_file, "r") as f, open(output_file, "w+") as g:
            for line in tqdm(f, desc="Preprocessing {}".format(language), total=49800):
                g.write(self._preprocess_sentence(line) + "\n")
    
    def preprocess(self):
        self._preprocess_file(os.path.join("texts", "sentences", "english.txt"), os.path.join("texts", "sentences", "english_formatted.txt"), "english")
        self._preprocess_file(os.path.join("texts", "sentences", "latin.txt"), os.path.join("texts", "sentences", "latin_formatted.txt"), "latin")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Retrieve and format data for use in Latin-English translation models.")
    parser.add_argument("mode", nargs="?", choices=["download", "extract", "preprocess"], help="Data function to execute")
    args = parser.parse_args()
    dataset = DatasetConstructor()
    dataset.run(args.mode)