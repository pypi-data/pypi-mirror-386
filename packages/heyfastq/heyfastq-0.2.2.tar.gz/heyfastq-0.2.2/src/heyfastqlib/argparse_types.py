import argparse
import gzip
import io
import os
import shutil
import subprocess as sp
import sys


class GzipFileType(object):
    """Factory for creating optionally gzipped file object types

    Taken from https://github.com/python/cpython/blob/05a370abd6cdfe4b54be60b3b911f3a441026bb2/Lib/argparse.py

    Instances of GzipFileType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.

    Keyword Arguments:
        - mode -- A string indicating how the file is to be opened. Accepts the
            same values as the builtin open() function.
        - bufsize -- The file's desired buffer size. Accepts the same values as
            the builtin open() function.
        - encoding -- The file's encoding. Accepts the same values as the
            builtin open() function.
        - errors -- A string indicating how encoding and decoding errors are to
            be handled. Accepts the same value as the builtin open() function.
    """

    def __init__(self, mode="r", bufsize=-1, encoding=None, errors=None):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors

    def open_gzip(self, filename):
        compression = os.environ.get("HFQ_GZIP_COMPRESSION", "4")
        if not compression.isdigit() or not (0 <= int(compression) <= 9):
            print(f"Invalid HFQ_GZIP_COMPRESSION value{(compression)}, using default 4")
            compression = "4"
        pigz = shutil.which("pigz")

        if pigz is not None:
            binary_mode = "b" in self._mode

            if "r" in self._mode:
                p = sp.Popen(
                    [pigz, f"-{compression}", "-dc", filename],
                    stdout=sp.PIPE,
                    bufsize=self._bufsize,
                )

                raw_stdout = p.stdout
                if raw_stdout is None:
                    raise ValueError("pigz stdout unavailable")

                if binary_mode:
                    stream = raw_stdout
                else:
                    stream = io.TextIOWrapper(
                        raw_stdout,
                        encoding=self._encoding,
                        errors=self._errors,
                    )

                def close():
                    if binary_mode:
                        raw_stdout.close()
                    else:
                        stream.close()
                    p.wait()

                return stream, close
            elif any(c in self._mode for c in "wax"):
                p = sp.Popen(
                    [pigz, f"-{compression}", "-c"],
                    stdin=sp.PIPE,
                    stdout=open(
                        filename,
                        "wb",
                        self._bufsize,
                    ),
                    bufsize=self._bufsize,
                )

                raw_stdin = p.stdin
                if raw_stdin is None:
                    raise ValueError("pigz stdin unavailable")

                if binary_mode:
                    stream = raw_stdin
                else:
                    stream = io.TextIOWrapper(
                        raw_stdin,
                        encoding=self._encoding,
                        errors=self._errors,
                    )

                def close():
                    if binary_mode:
                        raw_stdin.close()
                    else:
                        stream.close()
                    p.wait()

                return stream, close
            else:
                raise ValueError(f"invalid mode for gzip file: {self._mode}")
        else:
            f = gzip.open(
                filename,
                self._mode + "t",
                int(compression),
                self._encoding,
                self._errors,
            )

            return f, f.close

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == "-":
            if "r" in self._mode:
                return sys.stdin.buffer, None if "b" in self._mode else sys.stdin, None
            elif any(c in self._mode for c in "wax"):
                return (
                    sys.stdout.buffer,
                    None if "b" in self._mode else sys.stdout,
                    None,
                )
            else:
                msg = f'argument "-" with mode {self._mode}'
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            try:
                with open(string, "rb") as test_f:
                    gzipped = test_f.read(2) == b"\x1f\x8b"
            except FileNotFoundError:
                gzipped = string.endswith(".gz")

            if gzipped:
                f, close = self.open_gzip(string)
            else:
                f = open(
                    string, self._mode, self._bufsize, self._encoding, self._errors
                )
                close = f.close

            if f is None:
                raise argparse.ArgumentTypeError(
                    f"can't open {string} with mode {self._mode}"
                )

            return f, close
        except OSError as e:
            args = {"filename": string, "error": e}
            message = f"can't open {args['filename']}: {args['error']}"
            raise argparse.ArgumentTypeError(message % args)

    def __repr__(self):
        args = self._mode, self._bufsize
        kwargs = [("encoding", self._encoding), ("errors", self._errors)]
        args_str = ", ".join(
            [repr(arg) for arg in args if arg != -1]
            + ["%s=%r" % (kw, arg) for kw, arg in kwargs if arg is not None]
        )
        return "%s(%s)" % (type(self).__name__, args_str)


class HFQFormatter(argparse.HelpFormatter):
    def __init__(self, prog, indent_increment=2, max_help_position=25, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)

    # based on ArgumentDefaultsHelpFormatter but with a different search string
    def _get_help_string(self, action):
        help = action.help
        if help is None:
            help = ""

        if "default" not in help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += " (default: %(default)s)"
        return help
