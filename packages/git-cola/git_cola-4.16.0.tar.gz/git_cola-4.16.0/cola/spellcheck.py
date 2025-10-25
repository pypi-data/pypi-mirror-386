import codecs
import collections
import os

from . import core
from . import resources

__copyright__ = """
2012 Peter Norvig (http://norvig.com/spell-correct.html)
2013-2018 David Aguilar <davvid@gmail.com>
"""

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'


def train(features, model, all_train_words):
    for f in features:
        if f not in all_train_words:
            all_train_words.add(f)
            model[f] += 1
    return model


def edits1(word):
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits for c in ALPHABET if b]
    inserts = [a + c + b for a, b in splits for c in ALPHABET]
    return set(deletes + transposes + replaces + inserts)


def known_edits2(word, words):
    return {e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in words}


def known(word, words):
    return {w for w in word if w in words}


def suggest(word, words):
    candidates = (
        known([word], words)
        or known(edits1(word), words)
        or known_edits2(word, words)
        or [word]
    )
    return candidates


def correct(word, words):
    candidates = suggest(word, words)
    return max(candidates, key=words.get)


class NorvigSpellCheck:
    def __init__(
        self,
        words='dict/words',
        propernames='dict/propernames',
    ):
        data_dirs = resources.xdg_data_dirs()
        self.dictwords = resources.find_first(words, data_dirs)
        self.propernames = resources.find_first(propernames, data_dirs)
        self.words = collections.defaultdict(lambda: 1)
        self.extra_words = set()
        self.extra_dictionaries = set()
        self.initialized = False
        self.all_words = set()
        self.aspell_enabled = False
        self.aspell_langs = set()
        self.aspell_ok = False

    def add_dictionaries(self, dictionaries):
        """Add additional dictionaries to the spellcheck engine"""
        self.extra_dictionaries.update(dictionaries)

    def init(self):
        if self.initialized:
            return
        self.initialized = True
        all_train_words = set()
        if self.aspell_enabled:
            train(self.read_aspell_words(), self.words, all_train_words)
        if not self.aspell_ok:
            train(self.read(), self.words, all_train_words)

        train(self.extra_words, self.words, all_train_words)

    def set_aspell_enabled(self, enabled):
        """Enable aspell support"""
        self.aspell_enabled = enabled

    def set_aspell_langs(self, langs):
        """Set the aspell languages to query"""
        self.aspell_langs = set(langs)

    def add_word(self, word):
        self.extra_words.add(word)

    def suggest(self, word):
        self.init()
        return suggest(word, self.words)

    def check(self, word):
        self.init()
        return word.replace('.', '') in self.words

    def read(self, use_common_files=True):
        """Read dictionary words"""
        paths = []
        words = self.dictwords
        propernames = self.propernames

        if use_common_files and words and os.path.exists(words):
            paths.append((words, True))

        if use_common_files and propernames and os.path.exists(propernames):
            paths.append((propernames, False))

        for path in self.extra_dictionaries:
            paths.append((path, True))

        all_words = self.all_words
        for path, title in paths:
            try:
                with codecs.open(
                    path, 'r', encoding='utf-8', errors='ignore'
                ) as words_file:
                    for line in words_file:
                        word = line.rstrip()
                        if word not in all_words:
                            all_words.add(word)
                            yield word
                        if title:
                            title_word = word.title()
                            if title_word not in all_words:
                                all_words.add(title_word)
                                yield title_word
            except OSError:
                pass

    def read_aspell_words(self):
        """Read words from aspell"""
        # First, determine the languages to query.
        # Use "aspell dicts" and filter out any strings that are longer than 2
        # characters. This should leave *just* the main language names.
        if self.aspell_langs:
            aspell_langs = self.aspell_langs
        else:
            aspell_langs = _get_default_aspell_langs()

        ok = False
        all_words = self.all_words
        for lang in aspell_langs:
            cmd = ['aspell', 'dump', 'master', f'--lang={lang}']
            status, out, _ = core.run_command(cmd)
            if status == 0:
                for line in out.splitlines():
                    # Strip "/A" "/LR", "/H" and other suffixes from the
                    # output produced by "aspell dump master --lang=ru".
                    line = line.strip().split('/', 1)[0]
                    if not line:
                        continue
                    ok = True
                    if line not in all_words:
                        all_words.add(line)
                        yield line

        # Read extra dictionaries configured using `cola.dictionary`.
        self.aspell_ok = ok
        if ok:
            yield from self.read(use_common_files=False)


def _get_default_aspell_langs():
    cmd = ['aspell', 'dicts']
    status, out, _ = core.run_command(cmd)
    if status != 0:
        return []
    return [line for line in out.splitlines() if len(line) == 2]
