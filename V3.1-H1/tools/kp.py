"""pcbnew helper: fix the SWIG iterator under Python 3.14 and expose ToMM."""
import pcbnew
if not hasattr(pcbnew.SwigPyIterator, 'next'):
    pcbnew.SwigPyIterator.next = pcbnew.SwigPyIterator.__next__
mm = pcbnew.ToMM


def _items(getter):
    v = getter()
    try:
        return [v[i].Cast() if hasattr(v[i], "Cast") else v[i] for i in range(v.size())]
    except Exception:
        return list(v)


def drawings(b):
    return _items(b.Drawings)


def tracks(b):
    return _items(b.Tracks)


def zones(b):
    return _items(b.Zones)
