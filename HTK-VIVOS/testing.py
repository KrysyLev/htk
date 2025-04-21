import os
import random
import shutil
from viphoneme import vi2IPA

# === Paths ===
VIVOS_PATH = "/home/celsius/Documents/NLP/vivos"
HTK_VIVOS_PATH = "/home/celsius/Documents/NLP/HTK-VIVOS"

WAV_SRC_PATH = os.path.join(VIVOS_PATH, "train/waves")
GENDER_DIR = os.path.join(VIVOS_PATH, "genders/txt")

WAV_LIST = os.path.join(HTK_VIVOS_PATH, "wav_list.txt")
WAV_DIR = os.path.join(HTK_VIVOS_PATH, "wav")
LAB_DIR = os.path.join(HTK_VIVOS_PATH, "lab")
MFC_DIR = os.path.join(HTK_VIVOS_PATH, "mfc")
SCP_DIR = os.path.join(HTK_VIVOS_PATH, "scp")
DICT_DIR = os.path.join(HTK_VIVOS_PATH, "dict")
CONFIG_DIR = os.path.join(HTK_VIVOS_PATH, "config")

WORD_LIST_PATH = os.path.join(DICT_DIR, "word_list.txt")
WORDS_DIC_PATH = os.path.join(DICT_DIR, "words.dic")
MONO_LIST_PATH = os.path.join(DICT_DIR, "monophones.txt")

# === Step 1: Create folders ===
for folder in [WAV_DIR, LAB_DIR, MFC_DIR, SCP_DIR, DICT_DIR, CONFIG_DIR]:
    os.makedirs(folder, exist_ok=True)

# === Step 2: Select 1000 random WAV files from VIVOS ===
all_wav_files = []
for root, _, files in os.walk(WAV_SRC_PATH):
    for file in files:
        if file.endswith(".wav"):
            all_wav_files.append(os.path.join(root, file))

selected_files = random.sample(all_wav_files, 1000)
with open(WAV_LIST, "w", encoding="utf-8") as f:
    for path in selected_files:
        f.write(f"{path}\n")

# === Step 3: Copy selected files to working dir ===
for path in selected_files:
    shutil.copy(path, WAV_DIR)

print(f"✅ Created: {WAV_LIST} with {len(selected_files)} files.")

# === Step 4: Extract words from filenames ===
word_set = set()
for path in selected_files:
    filename = os.path.splitext(os.path.basename(path))[0]

    # If the filename format is 'SPK001_word1_word2.wav', split by underscores
    parts = filename.split("_")[1:]  # Skip the first part (speaker ID)

    # Ensure that we only extract the words (if they exist)
    words = [part for part in parts if part.isalpha()]
    word_set.update(words)

with open(WORD_LIST_PATH, "w", encoding="utf-8") as f:
    for word in sorted(word_set):
        f.write(f"{word}\n")

print(f"✅ Created: {WORD_LIST_PATH} with {len(word_set)} unique words.")

# === Step 5: Generate words.dic and monophones.txt ===
phoneme_set = set()
with (
    open(WORD_LIST_PATH, "r", encoding="utf-8") as fin,
    open(WORDS_DIC_PATH, "w", encoding="utf-8") as fout,
):
    for word in fin:
        word = word.strip()
        if word:
            phonemes = vi2IPA(word)
            phoneme_set.update(phonemes.split())
            fout.write(f"{word} {phonemes} .\n")

with open(MONO_LIST_PATH, "w", encoding="utf-8") as f:
    for p in sorted(phoneme_set):
        f.write(f"{p}\n")

print(f"✅ Created: {WORDS_DIC_PATH}")
print(f"✅ Created: {MONO_LIST_PATH}")

# === Step 6: Create .lab files with gender ===
for path in selected_files:
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    speaker = name.split("_")[0]
    words = name.split("_")[1:]

    # Gender lookup
    gender_path = os.path.join(GENDER_DIR, f"{speaker}.txt")
    gender = "unknown"
    if os.path.exists(gender_path):
        with open(gender_path, "r", encoding="utf-8") as gfile:
            gender = gfile.read().strip()

    phoneme_line = " ".join(vi2IPA(w) for w in words)

    with open(os.path.join(LAB_DIR, f"{name}.lab"), "w", encoding="utf-8") as f:
        f.write(f"{phoneme_line} ; {gender}\n")

print(f"✅ Created .lab files in: {LAB_DIR}")

# === Step 7: Create SCP and MLF files ===
wav2mfc_path = os.path.join(SCP_DIR, "wav2mfc.scp")
train_scp_path = os.path.join(SCP_DIR, "train.scp")
mlf_path = os.path.join(SCP_DIR, "train.mlf")

with (
    open(wav2mfc_path, "w", encoding="utf-8") as f1,
    open(train_scp_path, "w", encoding="utf-8") as f2,
):
    for path in selected_files:
        base = os.path.basename(path)
        name = os.path.splitext(base)[0]
        f1.write(f"{WAV_DIR}/{base} {MFC_DIR}/{name}.mfc\n")
        f2.write(f"{MFC_DIR}/{name}.mfc\n")

with open(mlf_path, "w", encoding="utf-8") as f:
    f.write("#!MLF!#\n")
    for path in selected_files:
        base = os.path.basename(path)
        name = os.path.splitext(base)[0]
        lab_file = os.path.join(LAB_DIR, f"{name}.lab")
        f.write(f'"*/{name}.lab"\n')
        with open(lab_file, "r", encoding="utf-8") as lab:
            f.write(lab.read())
        f.write(".\n")

print(f"✅ Created SCP and MLF files in: {SCP_DIR}")

# === Step 8: Create hcopy.conf ===
hcopy_conf_path = os.path.join(CONFIG_DIR, "hcopy.conf")
with open(hcopy_conf_path, "w") as f:
    f.write(
        "\n".join(
            [
                "SOURCEFORMAT = WAV",
                "TARGETKIND = MFCC_0_D_A",
                "TARGETRATE = 100000.0",
                "NUMCEPS = 12",
                "NUMCHANS = 26",
                "WINDOWSIZE = 250000.0",
                "USEHAMMING = T",
                "PREEMCOEF = 0.97",
                "CEPLIFTER = 22",
                "ENORMALISE = T",
            ]
        )
    )
print(f"✅ Created: {hcopy_conf_path}")

# === Step 9: (Optional) Create placeholder MFC files ===
for path in selected_files:
    name = os.path.splitext(os.path.basename(path))[0]
    mfc_path = os.path.join(MFC_DIR, f"{name}.mfc")
    with open(mfc_path, "w") as f:
        f.write("")  # Empty placeholder

print(f"✅ (Placeholder) MFC files created in: {MFC_DIR}")
print("🎉 All preprocessing steps completed!")
