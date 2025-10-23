from collections.abc import Iterable
from itertools import count

from heyfastqlib.pipelines import filter_reads, map_reads
from heyfastqlib.read import Read, trim, length_ok
from heyfastqlib.util import subsample as util_subsample


def iter_pipe(items: Iterable):
    for item in items:
        yield item


def make_counter() -> dict[str, int]:
    return {
        "input_reads": 0,
        "input_bases": 0,
        "output_reads": 0,
        "output_bases": 0,
    }


def test_filter_reads_filters_and_tracks_counts():
    reads = [
        Read("r1", "ATCG", "!!!!"),
        Read("r2", "AT", "!!!!"),
        Read("r3", "ATGGC", "!!!!!"),
    ]
    counter = make_counter()

    kept = list(
        filter_reads(
            iter_pipe(reads),
            lambda r, min_len: len(r.seq) >= min_len,
            counter,
            min_len=4,
        )
    )

    assert kept == [reads[0], reads[2]]
    assert counter == {
        "input_reads": 3,
        "input_bases": 11,
        "output_reads": 2,
        "output_bases": 9,
    }


def test_filter_reads_supports_pairs():
    pair1 = (
        Read("r1/1", "ACGTA", "!!!!!"),
        Read("r1/2", "TGCAT", "!!!!!"),
    )
    pair2 = (
        Read("r2/1", "TCG", "!!!"),
        Read("r2/2", "GCA", "!!!"),
    )
    counter = make_counter()

    kept_pairs = list(
        filter_reads(
            iter_pipe([pair1, pair2]),
            lambda rp, min_len: all(len(read.seq) >= min_len for read in rp),
            counter,
            min_len=4,
        )
    )

    assert kept_pairs == [pair1]
    assert counter == {
        "input_reads": 2,
        "input_bases": 8,
        "output_reads": 1,
        "output_bases": 5,
    }


def test_filter_reads_multiprocess_matches_single_thread():
    reads = [
        Read("r1", "ATCG", "!!!!"),
        Read("r2", "AT", "!!!!"),
        Read("r3", "ATGGC", "!!!!!"),
    ]
    counter = make_counter()

    kept = list(
        filter_reads(
            iter_pipe(reads),
            length_ok,
            counter,
            threshold=4,
            threads=2,
            chunk_size=1,
        )
    )

    assert kept == [reads[0], reads[2]]
    assert counter == {
        "input_reads": 3,
        "input_bases": 11,
        "output_reads": 2,
        "output_bases": 9,
    }


def test_map_reads_applies_function_and_counts():
    reads = [
        Read("r1", "ACGT", "!!!!"),
        Read("r2", "GGGTT", "!!!!!"),
    ]
    counter = make_counter()

    mapped = list(
        map_reads(
            iter_pipe(reads),
            lambda r, end: trim(r, end_idx=end),
            counter,
            end=3,
        )
    )

    assert [r.seq for r in mapped] == ["ACG", "GGG"]
    assert counter == {
        "input_reads": 2,
        "input_bases": 9,
        "output_reads": 2,
        "output_bases": 6,
    }


def test_map_reads_supports_pairs():
    pair = (
        Read("r1/1", "AACGT", "!!!!!"),
        Read("r1/2", "TTGCA", "!!!!!"),
    )
    counter = make_counter()

    mapped_pairs = list(
        map_reads(
            iter_pipe([pair]),
            lambda rp, end: trim(rp, end_idx=end),
            counter,
            end=4,
        )
    )

    assert mapped_pairs[0][0].seq == "AACG"
    assert mapped_pairs[0][1].seq == "TTGC"
    assert counter == {
        "input_reads": 1,
        "input_bases": 5,
        "output_reads": 1,
        "output_bases": 4,
    }


def test_map_reads_multiprocess_matches_single_thread():
    reads = [
        Read("r1", "ACGT", "!!!!"),
        Read("r2", "GGGTT", "!!!!!"),
    ]
    counter = make_counter()

    mapped = list(
        map_reads(
            iter_pipe(reads),
            trim,
            counter,
            end_idx=3,
            threads=2,
            chunk_size=1,
        )
    )

    assert [r.seq for r in mapped] == ["ACG", "GGG"]
    assert counter == {
        "input_reads": 2,
        "input_bases": 9,
        "output_reads": 2,
        "output_bases": 6,
    }


def test_filter_reads_supports_subsampling():
    reads = [
        Read("r0", "AAA", "!!!"),
        Read("r1", "CCC", "!!!"),
        Read("r2", "GGG", "!!!"),
        Read("r3", "TTT", "!!!"),
        Read("r4", "ACG", "!!!"),
    ]
    length = len(reads)
    sample_size = 3
    seed = 13
    expected_indexes = util_subsample(list(range(length)), sample_size, seed)
    indexes = set(expected_indexes)
    index_counter = count()
    counter = make_counter()
    total_bases = sum(len(r.seq) for r in reads)
    sampled_bases = sum(len(reads[i].seq) for i in expected_indexes)

    def keep_read(_: Read, *, _indexes=indexes, _counter=index_counter) -> bool:
        return next(_counter) in _indexes

    sampled = list(filter_reads(iter_pipe(reads), keep_read, counter))

    assert sampled == [reads[i] for i in expected_indexes]
    assert len(sampled) == sample_size
    assert counter == {
        "input_reads": length,
        "input_bases": total_bases,
        "output_reads": sample_size,
        "output_bases": sampled_bases,
    }
