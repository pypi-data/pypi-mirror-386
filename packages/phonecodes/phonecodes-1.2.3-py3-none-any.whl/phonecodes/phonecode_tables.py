"""
Tables mapping other phonecodes to/from IPA
"""

import re

###############################################################
# X-SAMPA

_xsampa2ipa = {
    k: re.sub(r"◌", "", v)
    for (k, v) in {
        "#": "#",
        "=": "◌̩",
        ">": "◌ʼ",
        "`": "◌˞",
        "~": "◌̃",
        "a": "a",
        "b": "b",
        "b_<": "ɓ",
        "c": "c",
        "d": "d",
        "d`": "ɖ",
        "d_<": "ɗ",
        "e": "e",
        "f": "f",
        "g": "ɡ",
        "g_<": "ɠ",
        "h": "h",
        "h\\": "ɦ",
        "i": "i",
        "j": "j",
        "j\\": "ʝ",
        "k": "k",
        "l": "l",
        "l`": "ɭ",
        "l\\": "ɺ",
        "m": "m",
        "n": "n",
        "n_d": "nd",
        "n`": "ɳ",
        "o": "o",
        "p": "p",
        "p\\": "ɸ",
        "p_<": "ɓ̥",
        "q": "q",
        "r": "r",
        "r`": "ɽ",
        "r\\": "ɹ",
        "r\\`": "ɻ",
        "s": "s",
        "s`": "ʂ",
        "s\\": "ɕ",
        "t": "t",
        "t`": "ʈ",
        "u": "u",
        "v": "v",
        "v\\": "ʋ",
        "w": "w",
        "x": "x",
        "x\\": "ɧ",
        "y": "y",
        "z": "z",
        "z`": "ʐ",
        "z\\": "ʑ",
        "A": "ɑ",
        "B": "β",
        "B\\": "ʙ",
        "C": "ç",
        "D": "ð",
        "E": "ɛ",
        "F": "ɱ",
        "G": "ɣ",
        "G\\": "ɢ",
        "G\\_<": "ʛ",
        "H": "ɥ",
        "H\\": "ʜ",
        "I": "ɪ",
        "I\\": "ɪ̈ ",
        "J": "ɲ",
        "J\\": "ɟ",
        "J\\_<": "ʄ",
        "K": "ɬ",
        "K\\": "ɮ",
        "L": "ʎ",
        "L\\": "ʟ",
        "M": "ɯ",
        "M\\": "ɰ",
        "N": "ŋ",
        "N_g": "ŋɡ",
        "N\\": "ɴ",
        "O": "ɔ",
        "O\\": "ʘ",
        "P": "ʋ",
        "Q": "ɒ",
        "R": "ʁ",
        "R\\": "ʀ",
        "S": "ʃ",
        "T": "θ",
        "U": "ʊ",
        "U\\": "ʊ̈ ",
        "V": "ʌ",
        "W": "ʍ",
        "X": "χ",
        "X\\": "ħ",
        "Y": "ʏ",
        "Z": "ʒ",
        ".": ".",
        '"': "ˈ",
        "%": "ˌ",
        "'": "ʲ",
        ":": "ː",
        ":\\": "ˑ",
        "-": "",
        "@": "ə",
        "@\\": "ɘ",
        "{": "æ",
        "}": "ʉ",
        "1": "ɨ",
        "2": "ø",
        "3": "ɜ",
        "3\\": "ɞ",
        "4": "ɾ",
        "5": "ɫ",
        "6": "ɐ",
        "7": "ɤ",
        "8": "ɵ",
        "9": "œ",
        "&": "ɶ",
        "?": "ʔ",
        "?\\": "ʕ",
        "*": "",
        "/": "",
        "<\\": "ʢ",
        ">\\": "ʡ",
        "^": "ꜛ",
        "!": "ꜜ",
        "!\\": "ǃ",
        "|": "|",
        "|\\": "ǀ",
        "||": "‖",
        "|\\|\\": "ǁ",
        "=\\": "ǂ",
        "-\\": "‿",
    }.items()
}

_xsampa_vowels = set("aeiouyAEIOUYQV@123}{6789&") | set(("I\\", "U\\", "@\\", "3\\"))

_xdiacritics2ipa = {
    k: re.sub(r"◌", "", v)
    for (k, v) in {
        '"': "◌̈",
        "+": "◌̟",
        "-": "◌̠",
        "/": "◌̌",
        "0": "◌̥",
        "=": "◌̩",
        ">": "◌ʼ",
        "?\\": "◌ˤ",
        "\\": "◌̂",
        "^": "◌̯",
        "}": "◌̚",
        "`": "◌˞",
        "~": "◌̃",
        "A": "◌̘",
        "a": "◌̺",
        "B": "◌̏",
        "B_L": "◌᷅",
        "c": "◌̜",
        "d": "◌̪",
        "e": "◌̴",
        "F": "◌̂",
        "G": "◌ˠ",
        "H": "◌́",
        "H_T": "◌᷄",
        "h": "◌ʰ",
        "j": "◌ʲ",
        "k": "◌̰",
        "L": "◌̀",
        "l": "◌ˡ",
        "M": "◌̄",
        "m": "◌̻",
        "N": "◌̼",
        "n": "◌ⁿ",
        "O": "◌̹",
        "o": "◌̞",
        "q": "◌̙",
        "R": "◌̌",
        "R_F": "◌᷈",
        "r": "◌̝",
        "T": "◌̋",
        "t": "◌̤",
        "v": "◌̬",
        "w": "◌ʷ",
        "X": "◌̆",
        "x": "◌̽",
        "1": "˥",
        "2": "˦",
        "3": "˧",
        "4": "˨",
        "5": "˩",
    }.items()
}

# Create and _xsampa2ipa with '_'+k for each diacritic
_xsampa_and_diac2ipa = _xsampa2ipa.copy()
_xsampa_and_diac2ipa.update({("_" + k): v for (k, v) in _xdiacritics2ipa.items()})

_ipa2xsampa = {v: k for (k, v) in _xsampa_and_diac2ipa.items()}

##################################################################
# Language-dependent tone numbers

_tone2ipa = {
    "arz": {"0": "", "1": "ˈ", "2": "ˌ"},
    "eng": {"0": "", "1": "ˈ", "2": "ˌ"},
    "yue": {"0": "", "1": "˥", "2": "˧˥", "3": "˧", "4": "˨˩", "5": "˩˧", "6": "˨"},
    "lao": {"0": "", "1": "˧", "2": "˥˧", "3": "˧˩", "4": "˥", "5": "˩˧", "6": "˩"},
    "cmn": {"0": "", "1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""},
    "spa": {"0": "", "1": "ˈ", "2": "ˌ"},
    "vie": {
        "0": "",
        "1": "˧",
        "2": "˨˩h",
        "3": "˧˥",
        "4": "˨˩˨",
        "5": "˧ʔ˥",
        "6": "˧˨ʔ",
    },
}

#####################################################################
# DISC, the code used by CELEX,
# is a kind of modified X-SAMPA,
# modified to include a lot of one-character shortcuts for phones
# that would require two characters in X-SAMPA.
# Some of the one-character shortcuts are language-dependent,
# in the sense that the same ASCII character is re-used for different IPA
# symbols in different languages.
# The language-independent table, below, includes only the symbols that
# are not part of X-SAMPA.

_disc2ipa = {
    k: re.sub(r"◌", "", v)
    for (k, v) in {
        "_": "dʒ",
        "a": "aː",
        "b": "b",
        "c": "æ◌̃",
        "d": "d",
        "e": "eː",
        "f": "f",
        "g": "ɡ",
        "h": "h",
        "i": "iː",
        "j": "j",
        "k": "k",
        "l": "l",
        "m": "m",
        "n": "n",
        "o": "oː",
        "p": "p",
        "q": "ɑ◌̃ː",
        "r": "r",
        "s": "s",
        "t": "t",
        "u": "uː",
        "v": "v",
        "w": "w",
        "x": "x",
        "y": "y",
        "A": "ɑ",
        "B": "au",
        "C": "ŋ◌̩",
        "D": "ð",
        "E": "ɛ",
        "F": "m◌̩",
        "G": "ɣ",
        "H": "n◌̩",
        "I": "ɪ",
        "J": "ɲ",
        "K": "ɛɪ",
        "L": "œɪ",
        "M": "ɯ",
        "N": "ŋ",
        "O": "ɔ",
        # TODO: resolve this duplication more carefully, since we cannot have duplicate keys.
        # This appears to be X-SAMPA only according to https://wellformedness.com/papers/codes/ and https://en.wikipedia.org/wiki/X-SAMPA, but it may be language specific.
        # Likely need to review https://catalog.ldc.upenn.edu/LDC96L14 to resolve this.
        # "P": "ʋ",
        "P": "l◌̩",
        "Q": "ɒ",
        "R": "ɜ◌˞",
        "S": "ʃ",
        "T": "θ",
        "U": "ʊ",
        "V": "ʌ",
        "W": "ai",
        "X": "ɔy",
        "Y": "ʏ",
        "Z": "ʒ",
        "0": "æ◌̃ː",
        "1": "eɪ",
        "2": "aɪ",
        "3": "ɜː",
        "4": "ɔɪ",
        "5": "əʊ",
        "6": "aʊ",
        "7": "ɪə",
        "8": "ɛə",
        "9": "ʊə",
        "|": "øː",
        "!": "iːː",
        "(": "yːː",
        ")": "ɛː",
        "*": "œː",
        "<": "ɒː",
        "+": "pf",
        "=": "ts",
        "-": ".",
        "#": "ɑː",
        "$": "ɔː",
        "&": "a",
        "^": "œ◌̃",
        "~": "ɔ◌̃ː",
        "'": "ˈ",
        "@": "ə",
        "{": "æ",
        "}": "ʉ",
    }.items()
}

_disc_vowels = _xsampa_vowels | set("|!()*KL#$WBX^46cq~CFHPR5789")
_ipa2disc = {v: k for (k, v) in _disc2ipa.items()}
_ipa2disc["#"] = ""

_disc2ipa_dutch = _disc2ipa.copy()
_disc2ipa_dutch["w"] = "ʋ"
_ipa2disc["ʋ"] = "w"
_disc2ipa_english = _disc2ipa.copy()
_disc2ipa_english["r"] = "ɻ"
_ipa2disc["ɻ"] = "r"

#######################################################################
# Callhome phone codes are completely language-dependent.
# I know of three: Egyptian Arabic, Mandarin, and Spanish

_callhome2ipa = {}
_callhome2ipa["arz"] = {
    "C": "ʔ",
    "b": "b",
    "t": "t",
    "g": "ɡ",
    "H": "ħ",
    "x": "x",
    "d": "d",
    "r": "ɾ",
    "z": "z",
    "s": "s",
    "$": "ʃ",
    "S": "sˤ",
    "D": "dˤ",
    "T": "tˤ",
    "Z": "ðˤ",
    "c": "ʕ",
    "G": "ɣ",
    "f": "f",
    "q": "ʔ",
    "Q": "q",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "h": "h",
    "w": "w",
    "y": "j",
    "v": "v",
    "j": "dʒ",
    "@": "æ",
    "a": "a",
    "B": "a",
    "i": "i",
    "u": "u",
    "%": "æː",
    "A": "aː",
    "I": "iː",
    "O": "oː",
    "U": "uː",
    "E": "eː",
    "ay": "aj",
    "aw": "aw",
}
_callhome2ipa["arz"].update(_tone2ipa["arz"])
_callhome_vowels = dict()
_callhome_vowels["arz"] = set("@aBiu%AIOUE") | set(("ay", "aw"))

_callhome2ipa["cmn"] = {
    "b": "p",
    "p": "pʰ",
    "m": "m",
    "d": "t",
    "t": "tʰ",
    "l": "l",
    "n": "n",
    "g": "k",
    "k": "kʰ",
    "h": "h",
    "N": "ŋ",
    "z": "ts",
    "c": "tsʰ",
    "s": "s",
    "j": "tɕ",
    "q": "tɕʰ",
    "x": "ɕ",
    "r": "ɻ",
    "Z": "ʈʂ",
    "C": "ʈʂʰ",
    "S": "ʂ",
    "f": "f",
    "y": "j",
    "w": "w",
    "W": "ɥ",
    "i": "i",
    "I": "ɨ",
    "%": "ɯ",
    "e": "e",
    "E": "ɛ",
    "U": "y",
    "&": "ə",
    "a": "ɑ",
    "@": "a",
    "o": "o",
    ">": "ɔ",
    "u": "u",
    "R": "ɚ",
}
_callhome2ipa["cmn"].update(_tone2ipa["cmn"])
_callhome_vowels["cmn"] = set("iI%eEU&a@o>uR")

_callhome2ipa["spa"] = {
    "a": "a",
    "i": "i",
    "e": "e",
    "o": "o",
    "u": "u",
    "h": "h",
    "p": "p",
    "b": "b",
    "B": "β",
    "f": "f",
    "v": "v",
    "l": "l",
    "m": "m",
    "w": "w",
    "t": "t",
    "d": "d",
    "D": "ð",
    "s": "s",
    "S": "ʃ",
    "C": "tʃ",
    "J": "dʒ",
    "n": "n",
    "y": "j",
    "r": "ɾ",
    "R": "r",
    "x": "x",
    "N": "ɲ",
    "k": "k",
    "g": "ɡ",
    "G": "ɣ",
    "9": "ŋ",
    "z": "z",
}
_callhome2ipa["spa"].update(_tone2ipa["spa"])
_callhome_vowels["spa"] = set("aieou")

_ipa2callhome = {symbol: {v: k for (k, v) in d.items()} for (symbol, d) in _callhome2ipa.items()}
# special cases, e.g., define best choice for ambiguous mappings
_ipa2callhome["arz"]["a"] = "a"


########################################################################
# ARPABET was invented for English.
# The standard dictionary written in ARPABET is the CMU dictionary.
_arpabet2ipa = {
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ʌ",
    "AH0": "ə",
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "EH": "ɛ",
    "ER": "ɝ",
    "ER0": "ɚ",
    "EY": "eɪ",
    "IH": "ɪ",
    "IH0": "ɨ",
    "IY": "i",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "UH": "ʊ",
    "UW": "u",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "EL": "l̩",
    "EM": "m̩",
    "EN": "n̩",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "P": "p",
    "Q": "ʔ",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "V": "v",
    "W": "w",
    "WH": "ʍ",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}
_arpabet2ipa.update(_tone2ipa["eng"])  # Add the English stress labels
_arpabet_vowels = set((k for k in _arpabet2ipa.keys() if k[0] in "AEIOU"))

_ipa2arpabet = {v: k for k, v in _arpabet2ipa.items()}
_ipa2tone = {symbol: {v: k for k, v in d.items()} for symbol, d in _tone2ipa.items()}

# TIMIT is written in a variant of ARPABET that includes a couple
# of non-standard allophones, and most significantly, includes
# separate symbols for the closure and release portions of each stop and affricate.
# Because the TIMIT corpus has separate symbols for closure and release,
# but IPA only has one corresponding symbol, we need to map all
# possibilities for inputs with and without spaces.
# This words because the search algorithm is greedy and matches the longest
# substrings with closure first if they are present.
_timit2ipa = _arpabet2ipa.copy()
_timit2ipa.pop("WH")
_timit2ipa.pop("ER0")
_timit2ipa.pop("IH0")
_timit2ipa.pop("AH0")
_timit2ipa.update(
    {
        "AX": "ə",
        "AX-H": "ə̥",
        "AXR": "ɚ",
        "BCL": "b",
        "BCLB": "b",
        "BCL B": "b",
        "DCL": "d",
        "DCLD": "d",
        "DCLJH": "dʒ",
        "DCL D": "d",
        "DCL JH": "dʒ",
        "DX": "ɾ",
        "ENG": "ŋ̩",
        "ER": "ɹ̩",
        "EPI": "",
        "GCL": "ɡ",
        "GCLG": "ɡ",
        "GCL G": "ɡ",
        "HV": "ɦ",
        "H#": "",
        "IX": "ɨ",
        "KCL": "k",
        "KCLK": "k",
        "KCL K": "k",
        "NX": "ɾ̃",
        "PAU": "",
        "PCL": "p",
        "PCLP": "p",
        "PCL P": "p",
        "TCL": "t",
        "TCLT": "t",
        "TCLCH": "tʃ",
        "TCL T": "t",
        "TCL CH": "tʃ",
        "UX": "ʉ",
    }
)


# The Buckeye alphabet is a version of ARPABET used to transcribe the Ohio State Buckeye corpus.
# The major differences are in nasalized vowels and some syllabic consonants
_buckeye2ipa = _arpabet2ipa.copy()
_buckeye2ipa.pop("ER0")
_buckeye2ipa.pop("WH")
_buckeye2ipa.pop("IH0")
_buckeye2ipa.pop("Q")
_buckeye2ipa.pop("AH0")
_buckeye2ipa.update(
    {
        "ER": "ɹ̩",
        "AEN": "æ̃",
        "AON": "ɔ̃",
        "AXN": "ə̃",
        "IYN": "ĩ",
        "EYN": "ẽɪ̃",
        "OWN": "õʊ̃",
        "DX": "ɾ",
        "AYN": "ãɪ̃",
        "AAN": "ɑ̃",
        "UWN": "ũ",
        "NX": "ɾ̃",
        "AX": "ə",
        "EHN": "ɛ̃",
        "UHN": "ʊ̃",
        "AWN": "ãʊ̃",
        "AHN": "ʌ̃",
        "TQ": "ʔ",
        "IHN": "ɪ̃",
        "ERN": "ɹ̩̃",
        "OYN": "ɔ̃ɪ̃",
        "BF": "β",
    }
)
# Remove tone2ipa keys for Buckeye
for tone_key in _tone2ipa["eng"].keys():
    _buckeye2ipa.pop(tone_key)


_ipa2buckeye = {v: k for k, v in _buckeye2ipa.items()}


#######################################################################
# IPA
_ipa_vowels = set("aeiouyɑɒɛɪɔʘʊʌʏəɘæʉɨøɜɞɐɤɵœɶ") | set(("ɪ̈", "ʊ̈"))
_ipa_consonants = set("bɓcdɖɗfɡɠhɦjʝklɭɺmnɳpɸqrɽɹɻsʂɕtʈvʋwxɧzʐʑβʙçðɱɣɢʛɥʜɲɟʄɬɮʎʟɯɰŋɴʋɒʁʀʃθʍχħʒɾɫʔʕʢʡꜛꜜǃ|ǀ‖ǁǂ")
_ipa_diacritics = set(re.sub(r"◌", "", "◌̈◌̟◌̠◌̌◌̥◌̩◌◌◌̂◌̯◌̚◌◌̃◌̘◌̺◌̏◌◌̜◌̪◌̴◌̂◌◌́◌◌◌◌̰◌̀◌◌̄◌̻◌̼◌◌̹◌̞◌̙◌̌◌◌̝◌̋◌̤◌̬◌◌̆◌̽ːʰˀʷʱʼʲˤ"))
_ipa_stressmarkers = set("ˈˌ")
_ipa_tonecharacters = set("˥˦˧˨˩˥˧")

# A bit of recursion to generate all tones of up to 4 components
_ipa_tones = _ipa_tonecharacters.copy()
_ipa_tones |= set(x + y for x in _ipa_tones for y in _ipa_tones)
_ipa_tones |= set(x + y for x in _ipa_tones for y in _ipa_tones)

_ipa_symbols = _ipa_vowels | _ipa_consonants | _ipa_diacritics
