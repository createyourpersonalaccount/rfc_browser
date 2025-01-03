from . import load_xml
import argparse


def parse_rfc_name(s):
    s = s.upper()
    if s.startswith("RFC"):
        s = s[3:]
    if not s.isdigit():
        return None
    return "RFC%.4d" % int(s)


class ParseRFCName(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        del option_string
        acc = [parse_rfc_name(v) for v in values]
        if not all(acc):
            raise argparse.ArgumentError(self, f"An argument does not refer to an RFC.")
        setattr(namespace, self.dest, acc)


def main():
    parser = argparse.ArgumentParser(
        prog="rfc-browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""An RFC browser that generates SVG maps.

Prints a graph in DOT language format.
""",
        epilog="More on <https://github.com/createyourpersonalaccount/rfc_browser>.",
    )
    parser.add_argument(
        "RFC",
        nargs="+",
        action=ParseRFCName,
        help="Should be given in the format RFCN (or just N); e.g. RFC1234.",
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="The full graph instead of the transitive reduction.",
    )
    args = parser.parse_args()
    load_xml.produce_svg(args.RFC, args.full)
