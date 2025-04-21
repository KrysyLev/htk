import os
import shutil
from viphoneme import vi2IPA
import random

# === Base paths ===
VIVOS_PATH = "/home/celsius/Documents/NLP/vivos"
BASE_DIR = "/home/celsius/Documents/NLP/HTK-VIVOS"
WAV_LIST = os.path.join(BASE_DIR, "wav_list.txt")
WAV_DIR = os.path.join(BASE_DIR, "wav")
LAB_DIR = os.path.join(BASE_DIR, "lab")
MFC_DIR = os.path.join(BASE_DIR, "mfc")
SCP_DIR = os.path.join(BASE_DIR, "scp")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DICT_DIR = os.path.join(BASE_DIR, "dict")
PROMPTS_FILE = os.path.join(VIVOS_PATH, "prompts.txt")
GENDER_DIR = os.path.join(VIVOS_PATH, "genders/txt")

# === Init directories ===
for folder in [WAV_DIR, LAB_DIR, MFC_DIR, SCP_DIR, CONFIG_DIR, DICT_DIR]:
    os.makedirs(folder, exist_ok=True)

# === Step 1: Select 1000 WAV files ===
all_wavs = []
for root, _, files in os.walk(os.path.join(VIVOS_PATH, "train/waves")):
    for file in files:
        if file.endswith(".wav"):
            all_wavs.append(os.path.join(root, file))

selected_wavs = random.sample(all_wavs, 1000)

with open(WAV_LIST, "w", encoding="utf-8") as f:
    for path in selected_wavs:
        f.write(f"{path}\n")

# === Step 2: Copy selected WAV files ===
for path in selected_wavs:
    shutil.copy(path, WAV_DIR)

# === Step 3: Generate .lab files with gender info ===
for path in selected_wavs:
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    speaker = name.split("_")[0]
    gender_file = os.path.join(GENDER_DIR, f"{speaker}.txt")
    gender = "unknown"
    if os.path.exists(gender_file):
        with open(gender_file, "r", encoding="utf-8") as f:
            gender = f.read().strip()

    with open(os.path.join(LAB_DIR, f"{name}.lab"), "w", encoding="utf-8") as f:
        f.write(f"{name} {gender}\n")

# === Step 4: Prepare Dictionary and Phoneme List ===
dictionary_src = os.path.join(VIVOS_PATH, "dictionary.txt")
dictionary_dst = os.path.join(DICT_DIR, "words.dic")
shutil.copy(dictionary_src, dictionary_dst)

with open(dictionary_dst, "r", encoding="utf-8") as f:
    lines = f.readlines()

phonemes = set()
for line in lines:
    parts = line.strip().split()[1:]
    phonemes.update(parts)

with open(os.path.join(DICT_DIR, "monophones.txt"), "w", encoding="utf-8") as f:
    for p in sorted(phonemes):
        f.write(f"{p}\n")

# === Step 5: Create hcopy.conf ===
with open(os.path.join(CONFIG_DIR, "hcopy.conf"), "w", encoding="utf-8") as f:
    f.write("""SOURCEFORMAT = WAV
TARGETKIND = MFCC_0_D_A
TARGETRATE = 100000.0
NUMCEPS = 12
NUMCHANS = 26
WINDOWSIZE = 250000.0
USEHAMMING = T
PREEMCOEF = 0.97
CEPLIFTER = 22
ENORMALISE = T
""")

# === Step 6: Generate SCP and MLF ===
with open(os.path.join(SCP_DIR, "wav2mfc.scp"), "w", encoding="utf-8") as f:
    for path in os.listdir(WAV_DIR):
        if path.endswith(".wav"):
            base = os.path.splitext(path)[0]
            f.write(f"{os.path.join(WAV_DIR, path)} {os.path.join(MFC_DIR, base)}.mfc\n")

with open(os.path.join(SCP_DIR, "train.scp"), "w", encoding="utf-8") as f:
    for path in os.listdir(WAV_DIR):
        if path.endswith(".wav"):
            base = os.path.splitext(path)[0]
            f.write(f"{os.path.join(MFC_DIR, base)}.mfc\n")

with open(os.path.join(SCP_DIR, "train.mlf"), "w", encoding="utf-8") as f:
    f.write("#!MLF!#\n")
    for path in os.listdir(LAB_DIR):
        if path.endswith(".lab"):
            base = os.path.splitext(path)[0]
            f.write(f"\"*/{base}.lab\"\n")
            with open(os.path.join(LAB_DIR, path), "r", encoding="utf-8") as lab_f:
                f.write(lab_f.read())
            f.write(".\n")

# === Step 7: Generate placeholder MFC files ===
for path in os.listdir(WAV_DIR):
    if path.endswith(".wav"):
        base = os.path.splitext(path)[0]
        with open(os.path.join(MFC_DIR, f"{base}.mfc"), "w") as f:
            f.write("")

print("\n🎉 All preprocessing steps completed successfully!")
