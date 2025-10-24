from pyoxigraph import Store, Quad, Triple
from typing import Iterable

from rdf_engine.rules import Rule
from bim2rdf.core.rdf import Prefix
class Rule(Rule):
    meta_prefix =    Prefix('meta',    'urn:meta:bim2rdf:') # https://www.iana.org/assignments/urn-formal/meta legit!
    # shouldn need bc <<data >>  meta:key literal(value).
    _metaid_prefix =  Prefix('meta.id', 'urn:meta:id:')     # https://www.iana.org/assignments/urn-formal/meta legit!

    @property
    def spec(self) -> dict:
        return {'class': self.__class__.__name__}

    @classmethod
    def repr(cls, **kw):
        nm = cls.__name__
        kw = {k:v for k,v in kw.items()
            # dont need to repr this
            if k not in {'class'} }
        from types import SimpleNamespace as NS
        _ = repr(NS(**kw)).replace('namespace', nm)
        return _
    def __repr__(self):
        return self.repr(**self.spec)
    
    from functools import cache, cached_property
    @cached_property
    def meta(self) -> tuple[Triple]: # NOT a function of data
        from json2rdf import j2r
        from boltons.iterutils import remap
        def json(p,k,v):
            err = ValueError(f'only simple key:value meta data allowed. got {repr({k:v})} ')
            if not isinstance(v, (list, dict)):
                if not isinstance(v, (bool, str, float, int, type(None) )):
                    return k, str(v) # coerce to str
            else: raise err
            if not isinstance(k, str): raise err
            return k,v
        _ = remap(self.spec, visit=json)
        _ = j2r(_,
                id_prefix=  (self._metaid_prefix.name, self._metaid_prefix.uri),
                key_prefix= (self.meta_prefix   .name, self.meta_prefix.   uri),
                )
        from pyoxigraph import parse, RdfFormat
        _ = parse(_, format=RdfFormat.TURTLE)
        _ = (q.triple for q in _)
        return tuple(_)

    def data(self, db: Store) -> Iterable[Triple]:
        #yield from [] # be nice ?
        raise NotImplementedError

    def meta_and_data(self, db: Store) ->Iterable[Quad]:
        rdf = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        data = Store()
        data.bulk_extend(Quad(*t) for t in self.data(db))
        mv = ((m.predicate, m.object) for m in self.meta )
        mv = map(lambda a: f"({a[0]} {a[1]})", mv)
        mv = '\n'.join(mv)
        q  = """
        construct {
        ?s ?p ?o.
        <<?s ?p ?o>> ?mp ?mo.
        }
        where {
        ?s ?p ?o.
          VALUES (?mp ?mo) {
            mv
        } }
        """
        q = q.replace('mv', mv)
        yield from (Quad(*t) for t in data.query(q))
    def __call__(self, db): yield from self.meta_and_data(db)


# class PyRule(Rule): need this?
