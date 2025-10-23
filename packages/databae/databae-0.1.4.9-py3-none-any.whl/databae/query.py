from sqlalchemy.sql import func, elements
from fyg.util import log, start_timer, end_timer
from fyg import config as confyg
from six import string_types
from .properties import *
from .getters import *
from .setters import *
from .session import session, seshman, testSession, metadata, Session, handle_error, set_scoper, indexer

_passthru = ["count", "all"]
_qmod = ["filter", "limit", "offset", "join"]

class Query(object):
    def __init__(self, mod, *args, **kwargs):
        self.mod = mod
        self.schema = get_schema(mod)
        self.cols = kwargs.pop("cols", None)
        if self.cols and type(self.cols[0]) is str:
            self.cols = [getattr(self.mod, c) for c in self.cols]
        self.session = kwargs.pop("session", None) or seshman.get()
        sq = self.session.query
        self.query = kwargs.pop("query", None) or (self.cols and sq(*self.cols) or sq(mod))
        for fname in _passthru:
            setattr(self, fname, self._qpass(fname))
        for fname in _qmod:
            setattr(self, fname, self._qmlam(fname))
        self.get = self._qpass("first")
        self._order = self._qmlam("order_by")
        self.filter(*args, **kwargs)

    def order(self, prop):
        if type(prop) == elements.UnaryExpression and "count" not in prop.element.description:
            prop = "-%s"%(prop.element.description,)
        if isinstance(prop, string_types):
            asc = False
            if prop.startswith("-"):
                prop = prop[1:]
            else:
                asc = True
            if "." in prop: # foreignkey reference from another table
                from .lookup import refcount_subq
                sub = refcount_subq(prop, self.session)
                order = sub.c.count
                if not asc:
                    order = -sub.c.count
                return self.join(sub, self.mod.key == sub.c.target).order(order)
            prop = getattr(self.mod, prop)
            if not asc:
                prop = prop.desc()
        return self._order(prop)

    def _qpass(self, fname):
        def qp(*args, **kwargs):
            qkey = "Query.%s: %s %s (%s)"%(fname, args, kwargs, self.query)
            if "query" in confyg.log.allow:
                start_timer(qkey)
            try:
                res = getattr(self.query, fname)(*args, **kwargs)
            except Exception as e:
                handle_error(e, self.session)
                log("retrying query operation")
                res = getattr(self.query, fname)(*args, **kwargs)
            if "query" in confyg.log.allow:
                end_timer(qkey)
            return res
        return qp

    def _qmlam(self, fname):
        return lambda *a, **k : self._qmod(fname, *a, **k)

    def _qmod(self, modname, *args, **kwargs):
        self.query = getattr(self.query, modname)(*args, **kwargs)
        return self

    def copy(self, *args, **kwargs):
        kwargs["query"] = self.query
        return Query(self.mod, *args, **kwargs)

    def fetch(self, limit=None, offset=0, keys_only=False):
        if limit:
            self.limit(limit)
        if offset:
            self.offset(offset)
        res = self.all()
        if keys_only: # best way?
            return [r.key for r in res]
        return res