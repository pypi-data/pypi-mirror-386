# sage_setup: distribution = sagemath-cmr
from sage.libs.cmr.cmr cimport CMR_SEYMOUR_NODE, CMR_ELEMENT
from sage.structure.sage_object cimport SageObject


cdef class DecompositionNode(SageObject):
    cdef object _base_ring
    cdef object _matrix
    cdef CMR_SEYMOUR_NODE *_dec
    cdef object _row_keys
    cdef object _column_keys
    cdef object _child_nodes
    cdef object _minors

    cdef _set_dec(self, CMR_SEYMOUR_NODE *dec)
    cdef _set_root_dec(self)
    cdef _set_row_keys(self, row_keys)
    cdef _set_column_keys(self, column_keys)

    cdef _CMRelement_to_key(self, CMR_ELEMENT element)


cdef class BaseGraphicNode(DecompositionNode):
    cdef object _graph
    cdef object _forest_edges
    cdef object _coforest_edges


cdef class GraphicNode(BaseGraphicNode):
    pass


cdef class CographicNode(BaseGraphicNode):
    pass


cdef class PlanarNode(BaseGraphicNode):
    cdef object _cograph
    cdef object _cograph_forest_edges
    cdef object _cograph_coforest_edges


cdef create_DecompositionNode(CMR_SEYMOUR_NODE *dec,
                              matrix=?,
                              row_keys=?, column_keys=?,
                              base_ring=?)
