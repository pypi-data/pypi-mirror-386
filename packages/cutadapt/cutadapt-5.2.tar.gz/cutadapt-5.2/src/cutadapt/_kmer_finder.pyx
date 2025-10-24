# cython: profile=False, emit_code_comments=False, language_level=3

from cpython.mem cimport PyMem_Realloc, PyMem_Free
from libc.string cimport memcpy, memset, strlen

from cpython.unicode cimport PyUnicode_CheckExact, PyUnicode_GET_LENGTH
from libc.stdint cimport uint8_t, uint64_t

from ._match_tables import matches_lookup

"""
Kmer finder that works using an enhanced shift-and algorithm. 

Shift-and works by using a bitmatrix to determine matches in words. For the
four-letter alphabet we can make the following bitmatrix for the word ACGTA

                                                                    ATGCA
0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00010001  A
0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000010  C
0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000100  G
0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00001000  T

However, this leaves a lot of bits unused in the machine word. It is also
possible to use as many bits in a bitmask as possible simply concatenating
all the words together. For example here, with appended GATTACA.

                                                            ACAT_TAGATGCA
0b00000000_00000000_00000000_00000000_00000000_00000000_00001010_01010001  A
0b00000000_00000000_00000000_00000000_00000000_00000000_00000100_00000010  C
0b00000000_00000000_00000000_00000000_00000000_00000000_00000000_00100100  G
0b00000000_00000000_00000000_00000000_00000000_00000000_00000001_10001000  T

Normal shift-and starts with initializing a 1 in bit 1. The same can be 
achieved for multiword by multiplying with a initmask with a one at each
word start position.
Normal shift-and only checks a single bit. The bit that is at exactly the
length of the word. We can check multiple bits simultaneously by using a
mask that checks for each bit that is at the end of a word.

This way we can check for multiple words simultaneously. It does not scale
if the combined length of the words exceeds a machine integer, but for 
cutadapt the words that are searched are usually smaller. (Illumina adapter
is 33 bases for example).

"""
# Dnaio conveniently ensures that all sequences are ASCII only.
DEF BITMASK_INDEX_SIZE = 128

ctypedef uint64_t bitmask_t

DEF MAX_WORD_SIZE = 64  # "sizeof(bitmask_t) * 8" does not work for some reason
MAXIMUM_WORD_SIZE = MAX_WORD_SIZE

cdef extern from "Python.h":
    void *PyUnicode_DATA(object o)
    bint PyUnicode_IS_COMPACT_ASCII(object o)

ctypedef struct KmerSearchEntry:
    size_t mask_offset
    ssize_t search_start
    ssize_t search_stop  # 0 if going to end of sequence.
    bitmask_t init_mask
    bitmask_t found_mask


cdef class KmerFinder:
    """
    Find kmers in strings. Allows case-independent and IUPAC matching.
    ``ref_wildcards=True`` allows IUPAC characters in the kmer sequences.
    ``query_wildcards=True`` allows IUPAC characters in the sequences fed to
    the ``kmers_present`` method.

    Replaces the following code:

        kmers_and_positions = [("AGA", -10, None), ("AGCATGA", 0, None)]
        for sequence in sequences:
            for kmer, start, stop in kmers_and_positions:
                if sequence.find(kmer, start, stop) != -1:
                    # do something
                    pass

    This has a lot of python overhead. The following code accomplishes the
    same task and allows for case-independent matching:

        positions_and_kmers = [(-10, None, ["AGA"]), (0, None, ["AGCATGA"])]
        kmer_finder = KmerFinder(positions_and_kmers)
        for sequence in sequences:
            if kmer_finder.kmers_present(sequence):
                # do something
                continue

    This is more efficient as the kmers_present method can be applied to a lot
    of sequences and all the necessary unpacking for each kmer into C variables
    happens only once.
    Note that multiple kmers can be given per position. Kmerfinder finds
    all of these simultaneously using a multiple pattern matching algorithm.
    """
    cdef:
        KmerSearchEntry *search_entries
        bitmask_t *search_masks
        size_t number_of_searches
        readonly object positions_and_kmers
        readonly bint ref_wildcards
        readonly bint query_wildcards

    def __cinit__(self, positions_and_kmers, ref_wildcards=False, query_wildcards=False):
        cdef char[64] search_word
        self.search_masks = NULL
        self.search_entries = NULL
        self.number_of_searches = 0
        self.ref_wildcards = ref_wildcards
        self.query_wildcards = query_wildcards
        self.number_of_searches = 0
        cdef size_t mask_offset = 0
        cdef char *kmer_ptr
        cdef size_t offset
        cdef bitmask_t init_mask, found_mask
        cdef Py_ssize_t kmer_length

        match_lookup = matches_lookup(ref_wildcards, query_wildcards)
        for (start, stop, kmers) in positions_and_kmers:
            index = 0 
            while index < len(kmers):
                memset(search_word, 0, 64)
                offset = 0
                init_mask = 0
                found_mask = 0
                # Run an inner loop in case all words combined are larger than
                # the maximum bitmask size. In that case we create multiple
                # bitmasks to hold all the words.
                while index < len(kmers):
                    kmer = kmers[index]
                    if not PyUnicode_CheckExact(kmer):
                        raise TypeError(f"Kmer should be a string not {type(kmer)}")
                    if not PyUnicode_IS_COMPACT_ASCII(kmer):
                        raise ValueError("Only ASCII strings are supported")
                    kmer_length = PyUnicode_GET_LENGTH(kmer)
                    if kmer_length > MAX_WORD_SIZE:
                        raise ValueError(f"{kmer} of length {kmer_length} is longer "
                                         f"than the maximum of {MAX_WORD_SIZE}.")
                    if (offset + kmer_length) > MAX_WORD_SIZE:
                        break
                    init_mask |= <bitmask_t>1ULL << offset
                    kmer_ptr = <char *> PyUnicode_DATA(kmer)
                    memcpy(search_word + offset, kmer_ptr, kmer_length)
                    # Set the found bit at the last character.
                    found_mask |= <bitmask_t>1ULL << (offset + kmer_length - 1)
                    offset = offset + kmer_length
                    index += 1
                i = self.number_of_searches  # Save the index position for the mask and entry
                self.number_of_searches += 1
                self.search_entries = <KmerSearchEntry *>PyMem_Realloc(self.search_entries, self.number_of_searches * sizeof(KmerSearchEntry))
                self.search_masks = <bitmask_t *>PyMem_Realloc(self.search_masks, self.number_of_searches * sizeof(bitmask_t) * BITMASK_INDEX_SIZE)
                mask_offset = i * BITMASK_INDEX_SIZE
                self.search_entries[i].search_start  = start
                if stop is None:  # Encode 'end of sequence' as 0.
                    stop = 0
                self.search_entries[i].search_stop = stop
                self.search_entries[i].mask_offset = mask_offset
                self.search_entries[i].init_mask = init_mask
                self.search_entries[i].found_mask = found_mask
                # Offset -1 because we don't count the last NULL byte
                populate_needle_mask(self.search_masks + mask_offset, search_word, offset,
                                     match_lookup)
        self.positions_and_kmers = positions_and_kmers

    def __reduce__(self):
        return KmerFinder, (self.positions_and_kmers, self.ref_wildcards, self.query_wildcards)

    def kmers_present(self, str sequence):
        cdef:
            KmerSearchEntry entry
            size_t i
            size_t kmer_offset
            bitmask_t init_mask
            bitmask_t found_mask
            ssize_t start, stop
            const bitmask_t *mask_ptr
            const char *search_ptr
            bint search_result
            ssize_t search_length
        if not PyUnicode_IS_COMPACT_ASCII(sequence):
            raise ValueError("Only ASCII strings are supported")
        cdef const char *seq = <char *>PyUnicode_DATA(sequence)
        cdef Py_ssize_t seq_length = PyUnicode_GET_LENGTH(sequence)
        for i in range(self.number_of_searches):
            entry = self.search_entries[i]
            start = entry.search_start 
            stop = entry.search_stop
            if start < 0:
                start = seq_length + start
                if start < 0:
                    start = 0
            elif start > seq_length:
                continue
            if stop < 0:
                stop = seq_length + stop
                if stop <= 0:  # No need to search
                    continue
            elif stop == 0:  # stop == 0 means go to end of sequence.
                stop = seq_length
            search_length = stop - start
            if search_length <= 0:
                continue
            search_ptr = seq + start
            init_mask = entry.init_mask
            found_mask = entry.found_mask
            mask_ptr = self.search_masks + entry.mask_offset
            search_result = shift_and_multiple_is_present(
                search_ptr, search_length, mask_ptr, init_mask, found_mask)
            if search_result:
                return True
        return False

    def __dealloc__(self):
        PyMem_Free(self.search_masks)
        PyMem_Free(self.search_entries)


cdef void set_masks(bitmask_t *needle_mask, size_t pos, const char *chars):
    cdef char c
    cdef size_t i
    for i in range(strlen(chars)):
        needle_mask[<uint8_t>chars[i]] |= <bitmask_t>1ULL << pos

cdef populate_needle_mask(bitmask_t *needle_mask, const char *needle, size_t needle_length,
                          match_lookup):
    cdef size_t i
    cdef char c
    cdef uint8_t j
    if needle_length > MAX_WORD_SIZE:
        raise ValueError("The pattern is too long!")
    memset(needle_mask, 0, sizeof(bitmask_t) * BITMASK_INDEX_SIZE)
    for i in range(needle_length):
        c = needle[i]
        if c == 0:
            continue
        set_masks(needle_mask, i, match_lookup[c])


cdef bint shift_and_multiple_is_present(
    const char *haystack,
    size_t haystack_length,
    const bitmask_t *needle_mask,
    bitmask_t init_mask,
    bitmask_t found_mask):
    cdef:
        bitmask_t R = 0
        size_t i

    for i in range(haystack_length):
        R <<= 1
        R |= init_mask
        R &= needle_mask[<uint8_t>haystack[i]]
        if (R & found_mask):
            return True
    return False
