# cython: profile=False, emit_code_comments=False, language_level=3
from cpython.ref cimport PyObject
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AS_STRING
from cpython.mem cimport PyMem_Malloc, PyMem_Free, PyMem_Realloc
from cpython.unicode cimport PyUnicode_GET_LENGTH
from libc.string cimport memcpy, memset

from ._match_tables import _upper_table, _acgt_table, _iupac_table

cdef extern from "Python.h":
    unsigned char * PyUnicode_1BYTE_DATA(object o)
    void * PyUnicode_DATA(object o)
    bint PyUnicode_IS_COMPACT_ASCII(object o)
    object PyUnicode_New(Py_ssize_t size, Py_UCS4 maxchar)

DEF MATCH_SCORE = +1
DEF MISMATCH_SCORE = -1
DEF INSERTION_SCORE = -2
DEF DELETION_SCORE = -2


# structure for a DP matrix entry
ctypedef struct _Entry:
    int cost
    int score    # score for this alignment (mostly keeps track of matches)
    int origin   # where the alignment originated: negative for positions within seq1, positive for pos. within seq2


ctypedef struct _Match:
    int origin
    int cost
    int score
    int ref_stop
    int query_stop


cdef:
    bytes ACGT_TABLE = _acgt_table()
    bytes IUPAC_TABLE = _iupac_table()
    bytes UPPER_TABLE = _upper_table()


cdef translate(object string, bytes table):
    if not PyUnicode_IS_COMPACT_ASCII(string):
        raise ValueError("String must contain only ASCII characters")
    cdef:
        unsigned char * string_chars = <unsigned char *>PyUnicode_DATA(string)
        Py_ssize_t string_length = PyUnicode_GET_LENGTH(string)
        char * char_table = PyBytes_AS_STRING(table)
        object retval = PyBytes_FromStringAndSize(NULL, string_length)
        char * translated_chars = PyBytes_AS_STRING(retval)
        Py_ssize_t i

    for i in range(string_length):
        translated_chars[i] = char_table[string_chars[i]]
    return retval


class DPMatrix:
    """
    Representation of the dynamic-programming matrix.

    This is used only when debugging is enabled in the Aligner class since the
    matrix is normally not stored in full.

    Entries in the matrix may be None, in which case that value was not
    computed.
    """
    def __init__(self, reference, query):
        m = len(reference)
        n = len(query)
        self._rows = [ [None] * (n+1) for _ in range(m + 1) ]
        self.reference = reference
        self.query = query

    def set_entry(self, int i, int j, cost):
        """
        Set an entry in the dynamic programming matrix.
        """
        self._rows[i][j] = cost

    def __str__(self):
        """
        Return a representation of the matrix as a string.
        """
        rows = ['     ' + ' '.join(c.rjust(2) for c in self.query)]
        for c, row in zip(' ' + self.reference, self._rows):
            r = c + ' ' + ' '.join('  ' if v is None else '{:2d}'.format(v) for v in row)
            rows.append(r)
        return '\n'.join(rows)


cdef class Aligner:
    """
    Find a full or partial occurrence of a query string in a reference string
    allowing errors (mismatches, insertions, deletions).

    This is a hybrid alignment algorithm that uses both costs and scores.

    By default, unit costs are used, meaning that mismatches, insertions and
    deletions are counted as one error (edit distance).

    Semi-global alignments allow skipping a suffix and/or prefix of query or
    reference at no cost. Combining semi-global alignment with edit distance is
    a bit unusual because the trivial “optimal” solution at edit distance 0
    would be to skip all of the reference and all of the query, like this:

        REFERENCE-----
        ---------QUERY

    Conceptually, the algorithm used here instead tests all possible overlaps
    between the two sequences and chooses the overlap which maximizes the
    score in the overlapping part, while the error rate must not
    go above a threshold.

    TODO working here

    To allow skipping of a prefix of the reference at no cost, set the
    START_IN_REFERENCE flag.
    To allow skipping of a prefix of the query at no cost, set the
    START_IN_QUERY flag.
    If both are set, a prefix of the reference or the query is skipped,
    never both.
    Similarly, set STOP_IN_REFERENCE and STOP_IN_QUERY to
    allow skipping of suffixes of the reference or of the query. Again, it
    is never the case that both suffixes are skipped.
    If all flags are set, this results in standard semiglobal alignment.

    The aligned parts are described with two intervals
    (ref_start, ref_stop),
    (query_start, query_stop).

    For example, an optimal semiglobal alignment of MISSISSIPPI and SISSI looks like this:

    MISSISSIPPI (reference)
    ---SISSI--- (query)

    query_start, query_stop = 0, 5
    ref_start, ref_stop = 3, 8
    (with zero errors)

    The aligned parts are reference[ref_start:ref_stop] and query[query_start:query_stop].

    The error rate is: errors / length where length is (reference_stop - reference_start).

    An optimal alignment fulfills all of these criteria:

    - its error_rate is at most max_error_rate
    - Among those alignments with error_rate <= max_error_rate, the alignment has
      highest score
    - If there are multiple alignments with the same score, then one that
      has minimal no. of errors is chosen.
    - If there are still multiple candidates, choose the alignment that starts at the
      leftmost position within the read.

    The alignment itself is not returned, only the tuple
    (ref_start, ref_stop, query_start, query_stop, score, errors).
    score is the total score and errors is the number of
    errors in the alignment.

    It is always the case that at least one of query_start and reference_start is zero.

    IUPAC wildcard characters can be allowed in the reference and the query
    by setting the appropriate flags.

    If neither flag is set, the full ASCII alphabet is used for comparison.
    If any of the flags is set, all non-IUPAC characters in the sequences
    compare as 'not equal'.
    """
    cdef:
        int m
        _Entry* column  # one column of the DP matrix
        double max_error_rate
        bint start_in_reference
        bint start_in_query
        bint stop_in_reference
        bint stop_in_query
        int _insertion_cost
        int _deletion_cost
        int _min_overlap
        bint wildcard_ref
        bint wildcard_query
        bint debug
        object _dpmatrix
        object _scorematrix
        str reference  # reference as set by the user (as str)
        bytes _reference  # internal, bytes version of reference (possibly translated to a non-ASCII representation)
        readonly int effective_length
        int* n_counts  # n_counts[i] == number of N characters in reference[:i]
        int _match_score
        int _mismatch_score
        int _insertion_score
        int _deletion_score

    def __cinit__(
        self,
        str reference,
        double max_error_rate,
        int flags=15,
        bint wildcard_ref=False,
        bint wildcard_query=False,
        int indel_cost=1,
        int min_overlap=1,
    ):
        self.max_error_rate = max_error_rate
        self.start_in_reference = flags & 1
        self.start_in_query = flags & 2
        self.stop_in_reference = flags & 4
        self.stop_in_query = flags & 8
        self.wildcard_ref = wildcard_ref
        self.wildcard_query = wildcard_query
        self._set_reference(reference)
        self._min_overlap = min_overlap
        self.debug = False
        self._dpmatrix = None
        self._scorematrix = None
        if indel_cost < 1:
            raise ValueError('indel_cost must be at least 1')
        self._insertion_cost = indel_cost
        self._deletion_cost = indel_cost

        self._match_score = MATCH_SCORE
        self._mismatch_score = MISMATCH_SCORE
        self._insertion_score = INSERTION_SCORE
        self._deletion_score = DELETION_SCORE

    def _compute_flags(self):
        cdef int flags = 0
        if self.start_in_reference:
            flags |= 1
        if self.start_in_query:
            flags |= 2
        if self.stop_in_reference:
            flags |= 4
        if self.stop_in_query:
            flags |= 8
        return flags

    def __reduce__(self):
        return (Aligner, (self.reference, self.max_error_rate, self._compute_flags(), self.wildcard_ref, self.wildcard_query, self._insertion_cost, self._min_overlap))

    def __repr__(self):
        return (
            f"Aligner(reference='{self.reference}', max_error_rate={self.max_error_rate}, "
            f"flags={self._compute_flags()}, wildcard_ref={self.wildcard_ref}, "
            f"wildcard_query={self.wildcard_query}, indel_cost={self._insertion_cost}, "
            f"min_overlap={self._min_overlap})"
        )

    def _set_reference(self, str reference):
        mem = <_Entry*> PyMem_Realloc(self.column, (len(reference) + 1) * sizeof(_Entry))
        if not mem:
            raise MemoryError()
        mem_nc = <int*> PyMem_Realloc(self.n_counts, (len(reference) + 1) * sizeof(int))
        if not mem_nc:
            raise MemoryError()
        self.column = mem
        self.n_counts = mem_nc
        self.m = len(reference)
        self.effective_length = self.m
        n_count = 0
        for i in range(self.m):
            self.n_counts[i] = n_count
            if reference[i] == 'n' or reference[i] == 'N':
                n_count += 1
        self.n_counts[self.m] = n_count
        assert self.n_counts[self.m] == reference.count('N') + reference.count('n')
        if self.wildcard_ref:
            self.effective_length = self.m - self.n_counts[self.m]
            if self.effective_length == 0:
                raise ValueError("Cannot have only N wildcards in the sequence")
            self._reference = translate(reference, IUPAC_TABLE)
        elif self.wildcard_query:
            self._reference = translate(reference, ACGT_TABLE)
        else:
            self._reference = reference.encode('ascii')
        self.reference = reference

    property dpmatrix:
        """
        The dynamic programming matrix as a DPMatrix object. This attribute is
        usually None, unless debugging has been enabled with enable_debug().
        """
        def __get__(self):
            return self._dpmatrix

    property scorematrix:
        def __get__(self):
            return self._scorematrix

    def enable_debug(self):
        """
        Store the dynamic programming matrices while running the locate() method
        and make them available in the .dpmatrix and .scorematrix attributes.
        """
        self.debug = True

    def locate(self, str query):
        """
        locate(query) -> (refstart, refstop, querystart, querystop, score, errors)

        Find the query within the reference associated with this aligner. The
        intervals (querystart, querystop) and (refstart, refstop) give the
        location of the match.

        That is, the substrings query[querystart:querystop] and
        self.reference[refstart:refstop] were found to align best to each other.

        The alignment itself is not returned.
        """
        cdef:
            const char* s1 = PyBytes_AS_STRING(self._reference)
            bytes query_bytes
            const char* s2
            int m = self.m
            int n = len(query)
            _Entry* column = self.column  # Current column of the DP matrix
            double max_error_rate = self.max_error_rate
            bint stop_in_query = self.stop_in_query
            bint compare_ascii = False

        if self.wildcard_query:
            query_bytes = translate(query, IUPAC_TABLE)
        elif self.wildcard_ref:
            query_bytes = translate(query, ACGT_TABLE)
        else:
            query_bytes = translate(query, UPPER_TABLE)
            compare_ascii = True
        s2 = query_bytes
        """
        DP Matrix:
                   query (j)
                 ----------> n
                |
        ref (i) |
                |
                V
               m
        """
        cdef int i, j

        # maximum no. of errors
        cdef int k = <int> (max_error_rate * m)

        # Determine largest and smallest column we need to compute
        cdef int max_n = n
        cdef int min_n = 0
        if not self.start_in_query:
            # costs can only get worse after column m
            max_n = min(n, m + k)
        if not self.stop_in_query:
            min_n = max(0, n - m - k)

        # Fill column min_n.
        #
        # Four cases:
        # not startin1, not startin2: c(i,j) = max(i,j); origin(i, j) = 0
        #     startin1, not startin2: c(i,j) = j       ; origin(i, j) = min(0, j - i)
        # not startin1,     startin2: c(i,j) = i       ; origin(i, j) =
        #     startin1,     startin2: c(i,j) = min(i,j)

        # TODO (later)
        # fill out columns only until 'last'
        if not self.start_in_reference and not self.start_in_query:
            for i in range(m + 1):
                column[i].score = i * self._deletion_score
                column[i].cost = max(i, min_n) * self._deletion_cost
                column[i].origin = 0
        elif self.start_in_reference and not self.start_in_query:
            for i in range(m + 1):
                column[i].score = 0
                column[i].cost = min_n * self._deletion_cost
                column[i].origin = min(0, min_n - i)
        elif not self.start_in_reference and self.start_in_query:
            for i in range(m + 1):
                column[i].score = i * self._deletion_score
                column[i].cost = i * self._deletion_cost
                column[i].origin = max(0, min_n - i)
        else:
            for i in range(m + 1):
                column[i].score = 0
                column[i].cost = min(i, min_n) * self._deletion_cost
                column[i].origin = min_n - i

        if self.debug:
            self._dpmatrix = DPMatrix(self.reference, query)
            self._scorematrix = DPMatrix(self.reference, query)
            for i in range(m + 1):
                self._dpmatrix.set_entry(i, min_n, column[i].cost)
                self._scorematrix.set_entry(i, min_n, column[i].score)
        cdef _Match best
        best.ref_stop = m
        best.query_stop = n
        best.cost = m + n + 1
        best.origin = 0
        best.score = 0

        # Ukkonen's trick: index of the last cell that is at most k
        cdef int last = min(m, k + 1)
        if self.start_in_reference:
            last = m

        cdef:
            int cost_diag
            int cost_deletion
            int cost_insertion
            int origin, cost, score
            int length
            int ref_start
            int cur_effective_length
            int last_filled_i = 0
            int best_length
            int origin_increment = 1 if self.start_in_query else 0
            int insertion_cost_increment = 0 if self.start_in_query else self._insertion_cost
            int insertion_score_increment = 0 if self.start_in_query else self._insertion_score
            bint characters_equal
            bint is_acceptable
            int insertion_cost = self._insertion_cost
            int deletion_cost = self._deletion_cost
            int match_score = self._match_score
            int mismatch_score = self._mismatch_score
            int insertion_score = self._insertion_score
            int deletion_score = self._deletion_score
            # We keep only a single column of the DP matrix in memory.
            # To access the diagonal cell to the upper left,
            # we store it here before overwriting it.
            _Entry diag_entry
            _Entry current_entry
            _Entry previous_entry

        with nogil:
            # iterate over columns
            for j in range(min_n + 1, max_n + 1):
                # remember first entry before overwriting
                diag_entry = column[0]

                # fill in first entry in this column
                column[0].origin += origin_increment
                column[0].cost += insertion_cost_increment
                column[0].score += insertion_score_increment
                for i in range(1, last + 1):
                    if compare_ascii:
                        characters_equal = (s1[i-1] == s2[j-1])
                    else:
                        characters_equal = (s1[i-1] & s2[j-1]) != 0
                    if characters_equal:
                        # If the characters match, we can skip computing costs for
                        # insertion and deletion as they are at least as high.
                        cost = diag_entry.cost
                        origin = diag_entry.origin
                        # Among the optimal alignments whose edit distance is within the
                        # maximum allowed error rate, we prefer those with maximal score.
                        score = diag_entry.score + match_score
                    else:
                        # Characters do not match.
                        current_entry = column[i]
                        previous_entry = column[i-1]
                        cost_diag = diag_entry.cost + 1
                        cost_insertion = current_entry.cost + insertion_cost
                        cost_deletion = previous_entry.cost + deletion_cost

                        if cost_diag <= cost_deletion and cost_diag <= cost_insertion:
                            # MISMATCH
                            cost = cost_diag
                            origin = diag_entry.origin
                            score = diag_entry.score + mismatch_score
                        elif cost_deletion <= cost_insertion:
                            # DELETION
                            cost = cost_deletion
                            origin = previous_entry.origin
                            score = previous_entry.score + deletion_score
                        else:
                            # INSERTION
                            cost = cost_insertion
                            origin = current_entry.origin
                            score = current_entry.score + insertion_score

                    # Remember the current cell for next iteration
                    diag_entry = column[i]

                    column[i].cost = cost
                    column[i].origin = origin
                    column[i].score = score
                last_filled_i = last
                if self.debug:
                    with gil:
                        for i in range(last + 1):
                            self._dpmatrix.set_entry(i, j, column[i].cost)
                            self._scorematrix.set_entry(i, j, column[i].score)
                while last >= 0 and column[last].cost > k:
                    last -= 1
                # last can be -1 here, but will be incremented next.
                # TODO if last is -1, can we stop searching?
                if last < m:
                    last += 1
                elif stop_in_query:
                    # Found a match. If requested, find best match in last row.
                    # length of the aligned part of the reference
                    cost = column[m].cost
                    score = column[m].score
                    origin = column[m].origin
                    length = m + min(origin, 0)
                    cur_effective_length = length
                    if self.wildcard_ref:
                        if length < m:
                            # Recompute effective length so that it only takes into
                            # account the matching part of the reference
                            cur_effective_length = length - (self.n_counts[m] - self.n_counts[m - length])
                        else:
                            cur_effective_length = self.effective_length
                    is_acceptable = (
                        length >= self._min_overlap
                        and cost <= cur_effective_length * max_error_rate
                    )
                    best_length = m + min(best.origin, 0)

                    # Update if
                    # - this is the first occurrence
                    # - or this occurrence is longer
                    # - or if this occurrence overlaps the previous best one and has a higher score
                    if is_acceptable and (
                        (best.cost == m + n + 1)  # No best match recorded so far, this is the first one
                        or (origin <= best.origin + m // 2 and score > best.score)  # This match overlaps the previous best one sufficiently (and has higher score)
                        or (length > best_length and score > best.score)  # Length is greater than best length so far
                    ):
                        best.score = score
                        best.cost = cost
                        best.origin = origin
                        best.ref_stop = m
                        best.query_stop = j
                        if cost == 0 and origin >= 0:
                            # exact match, stop early
                            break
                # column finished

        if max_n == n:
            first_i = 0 if self.stop_in_reference else m
            # search in last column
            for i in reversed(range(first_i, last_filled_i + 1)):
                length = i + min(column[i].origin, 0)
                cost = column[i].cost
                score = column[i].score
                if self.wildcard_ref:
                    if length < m:
                        # Recompute effective length so that it only takes into
                        # account the matching part of the reference
                        ref_start = -min(column[i].origin, 0)
                        assert 0 <= ref_start <= m
                        cur_effective_length = length - (self.n_counts[i] - self.n_counts[ref_start])
                    else:
                        cur_effective_length = self.effective_length
                else:
                    cur_effective_length = length
                assert 0 <= cur_effective_length and cur_effective_length <= length
                assert cur_effective_length <= self.effective_length

                is_acceptable = (
                    length >= self._min_overlap
                    and cost <= cur_effective_length * max_error_rate
                )
                best_length = best.ref_stop + min(best.origin, 0)

                if is_acceptable and (
                    (best.cost == m + n + 1)
                    or (origin <= best.origin + m // 2 and score > best.score)
                    or (length > best_length and score > best.score)
                ):
                    best.score = score
                    best.cost = cost
                    best.origin = column[i].origin
                    best.ref_stop = i
                    best.query_stop = n
        if best.cost == m + n + 1:
            # best.cost was initialized with this value.
            # If it is unchanged, no alignment was found that has
            # an error rate within the allowed range.
            return None

        cdef int query_start
        if best.origin >= 0:
            ref_start = 0
            query_start = best.origin
        else:
            ref_start = -best.origin
            query_start = 0

        return (ref_start, best.ref_stop, query_start, best.query_stop, best.score, best.cost)

    def __dealloc__(self):
        PyMem_Free(self.column)
        PyMem_Free(self.n_counts)


cdef class PrefixComparer:
    """
    A version of the Aligner that is specialized in the following way:

    - it does not allow indels
    - it allows only 5' anchored adapters

    This is a separate class, not simply a function, in order to be able
    to cache the reference (avoiding to convert it from str to bytes on
    every invocation)
    """
    cdef:
        bytes reference
        bint wildcard_ref
        bint wildcard_query
        int m
        int max_k  # max. number of errors
        readonly int effective_length
        int min_overlap

    # __init__ instead of __cinit__ because we need to override this in SuffixComparer
    def __init__(
        self,
        str reference,
        double max_error_rate,
        bint wildcard_ref=False,
        bint wildcard_query=False,
        int min_overlap=1,
    ):
        self.wildcard_ref = wildcard_ref
        self.wildcard_query = wildcard_query
        self.m = len(reference)
        self.effective_length = self.m
        if self.wildcard_ref:
            self.effective_length -= reference.count('N') - reference.count('n')
            if self.effective_length == 0:
                raise ValueError("Cannot have only N wildcards in the sequence")
        if not (0 <= max_error_rate <= 1.):
            raise ValueError("max_error_rate must be between 0 and 1")
        self.max_k = int(max_error_rate * self.effective_length)
        if min_overlap < 1:
            raise ValueError("min_overlap must be at least 1")
        self.min_overlap = min_overlap
        if self.wildcard_ref:
            self.reference = translate(reference, IUPAC_TABLE)
        elif self.wildcard_query:
            self.reference = translate(reference, ACGT_TABLE)
        else:
            self.reference = translate(reference, UPPER_TABLE)

    def __repr__(self):
        return "{}(reference={!r}, max_k={}, wildcard_ref={}, "\
            "wildcard_query={})".format(
                self.__class__.__name__,
                self.reference, self.max_k, self.wildcard_ref,
                self.wildcard_query)

    def locate(self, str query):
        """
        Find out whether one string is the prefix of the other one, allowing
        IUPAC wildcards in ref and/or query if the appropriate flag is set.

        This is used to find an anchored 5' adapter (type 'FRONT') in the 'no indels' mode.
        This is very simple as only the number of errors needs to be counted.

        This function returns a tuple compatible with what Aligner.locate returns.
        """
        cdef:
            bytes query_bytes
            char* r_ptr = self.reference
            char* q_ptr
            int i
            int n = len(query)
            int length = min(self.m, n)
            bint compare_ascii = False
            int errors = 0
            int score

        if self.wildcard_query:
            query_bytes = translate(query, IUPAC_TABLE)
        elif self.wildcard_ref:
            query_bytes = translate(query, ACGT_TABLE)
        else:
            query_bytes = translate(query, UPPER_TABLE)
            compare_ascii = True
        q_ptr = query_bytes

        if compare_ascii:
            for i in range(length):
                if r_ptr[i] != q_ptr[i]:
                    errors += 1
        else:
            for i in range(length):
                if (r_ptr[i] & q_ptr[i]) == 0:
                    errors += 1

        if errors > self.max_k or length < self.min_overlap:
            return None
        score = (length - errors) * MATCH_SCORE + errors * MISMATCH_SCORE
        return (0, length, 0, length, score, errors)


cdef class SuffixComparer(PrefixComparer):

    def __init__(
        self,
        str reference,
        double max_error_rate,
        bint wildcard_ref=False,
        bint wildcard_query=False,
        int min_overlap=1,
    ):
        super().__init__(reference[::-1], max_error_rate, wildcard_ref, wildcard_query, min_overlap)

    def locate(self, str query):
        cdef int n = len(query)
        result = super().locate(query[::-1])
        if result is None:
            return None
        _, length, _, _, score, errors = result
        return (self.m - length, self.m, n - length, n, score, errors)


def hamming_sphere(str s, int k):
    """
    Yield all strings t for which the hamming distance between s and t is exactly k,
    assuming the alphabet is A, C, G, T.
    """
    if k == 0:
        yield s
        return

    if not PyUnicode_IS_COMPACT_ASCII(s):
        raise ValueError("String must contain only ASCII characters")

    cdef:
        Py_ssize_t n = PyUnicode_GET_LENGTH(s)
        unsigned char* s_ptr = <unsigned char*>PyUnicode_DATA(s)
        Py_ssize_t i, j
        #str prefix, prefix2
        unsigned char ch, ch1, ch2
        unsigned char* result_ptr

    if k == 1:
        for i in range(n):
            for ch in "ACGT":
                if s_ptr[i] == ch:
                    continue
                result = PyUnicode_New(n, 255)
                if <PyObject*>result == NULL:
                    raise MemoryError()
                result_ptr = <unsigned char*>PyUnicode_1BYTE_DATA(result)
                memcpy(result_ptr, s_ptr, n)
                result_ptr[i] = ch
                yield result
        return

    if k == 2:
        for i in range(n):
            for ch1 in "ACGT":
                if s_ptr[i] == ch1:
                    continue

                for j in range(i + 1, n):
                    for ch2 in "ACGT":
                        if s[j] == ch2:
                            continue

                        result = PyUnicode_New(n, 255)
                        if <PyObject*>result == NULL:
                            raise MemoryError()
                        result_ptr = <unsigned char*>PyUnicode_1BYTE_DATA(result)
                        memcpy(result_ptr, s_ptr, n)
                        result_ptr[i] = ch1
                        result_ptr[j] = ch2
                        yield result
        return

    # Recursive solution for k > 2
    # i is the first position that is varied
    for i in range(n - k + 1):
        prefix = s[:i]
        c = s[i]
        suffix = s[i + 1 :]
        for pch in "ACGT":
            if pch == c:
                continue
            for t in hamming_sphere(suffix, k - 1):
                yield prefix + pch + t


def edit_environment(str t_str, int k):
    """
    Find all strings s for which the edit distance between s and t is at most k,
    assuming the alphabet is A, C, G, T.

    Yield tuples (s, e, m), where e is the edit distance between s and t and
    m is the number of matches in the optimal alignment.
    """

    cdef bytes t = t_str.encode().translate(bytes.maketrans(b"ACGTacgt", b"\0\1\2\3\0\1\2\3"))
    cdef unsigned char* t_ptr = t

    # len(s) = m, indexed by i
    # len(t) = n, indexed by j
    cdef:
        int j, match, diag, left, up, c, m
        int i = 0
        int n = len(t)
        char ch
        int min_cost

    cdef int* costs = <int*> PyMem_Malloc((n + 1) * (n + k + 1) * sizeof(int))

    if not costs:
        raise MemoryError()
    memset(costs, k+1, (n+1) * (n+k+1) * sizeof(int))
    for i in range(n + k + 1):
        costs[i*(n+1)] = i
    for j in range(n + 1):
        costs[j] = j

    cdef int* matches = <int*> PyMem_Malloc((n + 1) * (n + k + 1) * sizeof(int))
    if not matches:
        raise MemoryError()
    memset(matches, 0, (n+1) * (n+k+1) * sizeof(int))

    trans = bytes.maketrans(b"\0\1\2\3", b"ACGT")

    cdef char* s = <char*>PyMem_Malloc((n + k + 1) * sizeof(char))
    i = 0
    if not s:
        raise MemoryError()
    while True:
        # Fill in row i (unless it is row 0, which is already filled in)
        if i > 0:
            ch = s[i - 1]
            min_cost = 999999999
            for j in range(max(1, i - k), min(n + 1, i + k + 1)):
                match = 0 if t_ptr[j - 1] == ch else 1

                diag = costs[(i - 1) * (n+1) + j - 1] + match
                left = costs[i * (n+1) + j - 1] + 1
                up = costs[(i - 1) * (n+1) + j] + 1
                if diag <= left and diag <= up:
                    c = diag
                    m = matches[(i - 1) * (n+1) + j - 1] + (1 - match)
                elif left <= up:
                    c = left
                    m = matches[i * (n+1) + j - 1]
                else:
                    c = up
                    m = matches[(i - 1) * (n+1) + j]
                costs[i*(n+1) + j] = c
                matches[i*(n+1) + j] = m
                min_cost = min(min_cost, c)
        else:
            min_cost = 0

        if costs[i * (n+1) + n] <= k:
            # The costs of an optimal alignment of t against s are at most k,
            # so s is within the edit environment.
            result = PyBytes_FromStringAndSize(s, i)
            if <PyObject*>result == NULL:
                raise MemoryError()

            yield result.translate(trans).decode(), costs[i * (n+1) + n], matches[i * (n+1) + n]

        # Next string
        if min_cost <= k and i < n + k:
            # When all entries are greater than k, we can skip remaining prefixes since costs in
            # subsequent rows cannot get lower
            s[i] = 0
            i += 1
        else:
            while True:
                if i == 0:
                    PyMem_Free(costs)
                    PyMem_Free(matches)
                    return
                i -= 1
                ch = s[i]
                if ch < 3:
                    break

            s[i] = ch + 1
            i += 1

    assert False
