# sage_setup: distribution = sagemath-cmr
# -*- python -*-
# distutils: libraries = cmr

# (progn (replace-regexp "/[*]\\(.\\|\n\\)*?[*]/" "" nil (point) (point-max)) (replace-regexp "[;{}]" ""  nil (point) (point-max)) (replace-regexp "CMR_EXPORT *" ""  nil (point) (point-max)) (replace-regexp "bool" "bint" nil (point) (point-max)))

from libc.stdint cimport int8_t, uint32_t, int64_t

cdef extern from "stdbool.h":

    ctypedef bint bool

cdef extern from "cmr/env.h":
    const int CMR_OKAY
    const int CMR_ERROR_INPUT
    const int CMR_ERROR_OUTPUT
    const int CMR_ERROR_MEMORY
    const int CMR_ERROR_INVALID
    const int CMR_ERROR_OVERFLOW
    const int CMR_ERROR_TIMEOUT
    const int CMR_ERROR_STRUCTURE
    const int CMR_ERROR_INCONSISTENT
    const int CMR_ERROR_PARAMS

    ctypedef int CMR_ERROR

    ctypedef struct CMR

    int CMRcreateEnvironment(CMR** pcmr)
    int CMRfreeEnvironment(CMR** pcmr)

    char* CMRgetErrorMessage(CMR* cmr)
    void CMRclearErrorMessage(CMR* cmr)

    CMR_ERROR _CMRallocBlock(CMR* cmr, void** ptr, size_t size)
    CMR_ERROR _CMRfreeBlock(CMR* cmr, void** ptr, size_t size)
    CMR_ERROR _CMRallocBlockArray(CMR* cmr, void** ptr, size_t size, size_t length)
    CMR_ERROR _CMRreallocBlockArray(CMR* cmr, void** ptr, size_t size, size_t length)
    CMR_ERROR _CMRduplicateBlockArray(CMR* cmr, void** ptr, size_t size, size_t length, void* source)
    CMR_ERROR _CMRfreeBlockArray(CMR* cmr, void** ptr)

cdef extern from "cmr/matrix.h":

    ctypedef struct CMR_SUBMAT:
        size_t numRows
        size_t* rows
        size_t numColumns
        size_t* columns

    CMR_ERROR CMRsubmatCreate(CMR* cmr, size_t numRows, size_t numColumns, CMR_SUBMAT** psubmatrix)
    CMR_ERROR CMRsubmatCreate1x1(CMR* cmr, size_t row, size_t column, CMR_SUBMAT** psubmatrix)
    CMR_ERROR CMRsubmatCreate2x2(CMR* cmr, size_t row1, size_t row2, size_t column1, size_t column2, CMR_SUBMAT** psubmatrix)
    CMR_ERROR CMRsubmatFree(CMR* cmr, CMR_SUBMAT** psubmatrix)
    # CMR_ERROR CMRsubmatPrint(CMR* cmr, CMR_SUBMAT* submatrix, size_t numRows, size_t numColumns, FILE* stream)

    ctypedef struct CMR_INTMAT:
        size_t numRows
        size_t numColumns
        size_t numNonzeros
        size_t* rowSlice
        size_t* entryColumns
        int* entryValues

    CMR_ERROR CMRintmatCreate(CMR* cmr, CMR_INTMAT** presult, int numRows, int numColumns, int numNonzeros)
    CMR_ERROR CMRintmatSortNonzeros(CMR* cmr, CMR_INTMAT* matrix)
    # CMR_ERROR CMRintmatPrintDense(CMR* cmr, CMR_INTMAT* matrix, FILE* stream, char zeroChar, bint header)
    CMR_ERROR CMRintmatFindEntry(CMR_INTMAT* matrix, size_t row, size_t column, size_t* pentry)
    CMR_ERROR CMRintmatSlice(CMR* cmr, CMR_INTMAT* matrix, CMR_SUBMAT* submatrix, CMR_INTMAT** presult)
    CMR_ERROR CMRintmatFree(CMR* cmr, CMR_INTMAT** pmatrix)

    ctypedef struct CMR_CHRMAT:
        size_t numRows
        size_t numColumns
        size_t numNonzeros
        size_t* rowSlice
        size_t* entryColumns
        signed char* entryValues

    CMR_ERROR CMRchrmatCreate(CMR* cmr, CMR_CHRMAT** presult, int numRows, int numColumns, int numNonzeros)
    CMR_ERROR CMRchrmatSortNonzeros(CMR* cmr, CMR_CHRMAT* matrix)
    # CMR_ERROR CMRchrmatPrintDense(CMR* cmr, CMR_CHRMAT* matrix, FILE* stream, char zeroChar, bint header)
    CMR_ERROR CMRchrmatFindEntry(CMR_CHRMAT* matrix, size_t row, size_t column, size_t* pentry)
    CMR_ERROR CMRchrmatSlice(CMR* cmr, CMR_CHRMAT* matrix, CMR_SUBMAT* submatrix, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatFree(CMR* cmr, CMR_CHRMAT** pmatrix)
    CMR_ERROR CMRchrmatTranspose(CMR* cmr, CMR_CHRMAT* matrix, CMR_CHRMAT** presult)

    CMR_ERROR CMRchrmatToInt(CMR* cmr, CMR_CHRMAT* matrix, CMR_INTMAT** presult)
    CMR_ERROR CMRintmatToChr(CMR* cmr, CMR_INTMAT* matrix, CMR_CHRMAT** presult)

cdef extern from "cmr/camion.h":

    ctypedef struct CMR_CAMION_STATISTICS:
        uint32_t generalCount
        double generalTime
        uint32_t graphCount
        double graphTime
        uint32_t totalCount
        double totalTime

    CMR_ERROR CMRcamionStatsInit(CMR_CAMION_STATISTICS* stats)
    # CMR_ERROR CMRstatsCamionPrint(FILE* stream, CMR_CAMION_STATISTICS* stats, const char* prefix)
    CMR_ERROR CMRcamionTestSigns(CMR* cmr, CMR_CHRMAT* matrix, bool* pisCamionSigned, CMR_SUBMAT** psubmatrix, CMR_CAMION_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRcamionComputeSigns(CMR* cmr, CMR_CHRMAT* matrix, bool* pwasCamionSigned, CMR_SUBMAT** psubmatrix, CMR_CAMION_STATISTICS* stats, double timeLimit)

cdef extern from "cmr/element.h":

    ctypedef int CMR_ELEMENT

    const char* CMRelementString(CMR_ELEMENT element, char* buffer)
    bint CMRelementIsValid(CMR_ELEMENT element)
    CMR_ELEMENT CMRrowToElement(size_t row)
    CMR_ELEMENT CMRcolumnToElement(size_t column)
    bint CMRelementIsRow(CMR_ELEMENT element)
    size_t CMRelementToRowIndex(CMR_ELEMENT element)
    bint CMRelementIsColumn(CMR_ELEMENT element)
    size_t CMRelementToColumnIndex(CMR_ELEMENT element)
    CMR_ELEMENT CMRelementTranspose(CMR_ELEMENT element)

cdef extern from "cmr/graph.h":

    ctypedef int CMR_GRAPH_NODE
    ctypedef int CMR_GRAPH_EDGE
    ctypedef int CMR_GRAPH_ITER

    ctypedef struct CMR_GRAPH_NODE_DATA:
        int prev
        int next
        int firstOut

    ctypedef struct CMR_GRAPH_ARC_DATA:
        int target
        int prev
        int next

    ctypedef struct CMR_GRAPH:
        size_t numNodes
        size_t memNodes
        CMR_GRAPH_NODE_DATA* nodes
        int firstNode
        int freeNode
        size_t numEdges
        size_t memEdges
        CMR_GRAPH_ARC_DATA* arcs
        int freeEdge

    size_t CMRgraphMemNodes(CMR_GRAPH* graph)
    size_t CMRgraphNumNodes(CMR_GRAPH* graph)
    size_t CMRgraphMemEdges(CMR_GRAPH* graph)
    size_t CMRgraphNumEdges(CMR_GRAPH* graph)
    CMR_GRAPH_NODE CMRgraphEdgeU(CMR_GRAPH* graph, CMR_GRAPH_EDGE e)
    CMR_GRAPH_NODE CMRgraphEdgeV(CMR_GRAPH* graph, CMR_GRAPH_EDGE e)
    CMR_ERROR CMRgraphCreateEmpty(CMR* cmr, CMR_GRAPH** pgraph, int memNodes, int memEdges)
    CMR_ERROR CMRgraphFree(CMR* cmr, CMR_GRAPH** pgraph)
    CMR_ERROR CMRgraphClear(CMR* cmr, CMR_GRAPH* graph)
    CMR_ERROR CMRgraphAddNode(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH_NODE* pnode)
    CMR_ERROR CMRgraphAddEdge(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH_NODE u, CMR_GRAPH_NODE v, CMR_GRAPH_EDGE* pedge)
    CMR_ERROR CMRgraphDeleteNode(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH_NODE v)
    CMR_ERROR CMRgraphDeleteEdge(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH_EDGE e)
    CMR_GRAPH_NODE CMRgraphNodesFirst(CMR_GRAPH* graph)
    bint CMRgraphNodesValid(CMR_GRAPH* graph, CMR_GRAPH_NODE v)
    CMR_GRAPH_NODE CMRgraphNodesNext(CMR_GRAPH* graph, CMR_GRAPH_NODE v)
    CMR_GRAPH_ITER CMRgraphIncFirst(CMR_GRAPH* graph, CMR_GRAPH_NODE v)
    bint CMRgraphIncValid(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_ITER CMRgraphIncNext(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_EDGE CMRgraphIncEdge(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_NODE CMRgraphIncSource(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_NODE CMRgraphIncTarget(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_ITER CMRgraphEdgesFirst(CMR_GRAPH* graph)
    CMR_GRAPH_ITER CMRgraphEdgesNext(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    bint CMRgraphEdgesValid(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    CMR_GRAPH_EDGE CMRgraphEdgesEdge(CMR_GRAPH* graph, CMR_GRAPH_ITER i)
    # CMR_ERROR CMRgraphPrint(CMR_GRAPH* graph, FILE* stream)
    CMR_ERROR CMRgraphMergeNodes(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH_NODE u, CMR_GRAPH_NODE v)
    # CMR_ERROR CMRgraphCreateFromEdgeList(CMR* cmr, CMR_GRAPH** pgraph, CMR_ELEMENT** pedgeElements, char*** pnodeLabels, FILE* stream)
    # CMR_ERROR CMRgraphCopy(CMR* cmr, CMR_GRAPH* graph, CMR_GRAPH** pcopy)

cdef extern from "cmr/matroid.h":

    CMR_ERROR CMRchrmatBinaryPivot(CMR* cmr, CMR_CHRMAT* matrix, size_t pivotRow, size_t pivotColumn, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatTernaryPivot(CMR* cmr, CMR_CHRMAT* matrix, size_t pivotRow, size_t pivotColumn, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatRegularPivot(CMR* cmr, CMR_CHRMAT* matrix, size_t pivotRow, size_t pivotColumn, CMR_SUBMAT** pviolator, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatBinaryPivots(CMR* cmr, CMR_CHRMAT* matrix, size_t numPivots, size_t* pivotRows, size_t* pivotColumns, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatTernaryPivots(CMR* cmr, CMR_CHRMAT* matrix, size_t numPivots, size_t* pivotRows, size_t* pivotColumns, CMR_CHRMAT** presult)
    CMR_ERROR CMRchrmatRegularPivots(CMR* cmr, CMR_CHRMAT* matrix, size_t numPivots, size_t* pivotRows, size_t* pivotColumns, CMR_SUBMAT** pviolator, CMR_CHRMAT** presult)

    ctypedef int CMR_MINOR_TYPE

    const int CMR_MINOR_TYPE_DETERMINANT
    const int CMR_MINOR_TYPE_ENTRY
    const int CMR_MINOR_TYPE_CUSTOM
    const int CMR_MINOR_TYPE_U24
    const int CMR_MINOR_TYPE_FANO
    const int CMR_MINOR_TYPE_FANO_DUAL
    const int CMR_MINOR_TYPE_K5
    const int CMR_MINOR_TYPE_K5_DUAL
    const int CMR_MINOR_TYPE_K33
    const int CMR_MINOR_TYPE_K33_DUAL

    ctypedef struct CMR_MINOR:
        size_t numPivots
        size_t* pivotRows
        size_t* pivotColumns
        CMR_SUBMAT* remainingSubmatrix
        CMR_MINOR_TYPE type

    CMR_ERROR CMRminorCreate(CMR* cmr, CMR_MINOR** pminor, size_t numPivots, CMR_SUBMAT* submatrix, CMR_MINOR_TYPE type)
    CMR_ERROR CMRminorFree(CMR* cmr, CMR_MINOR** pminor)
    CMR_MINOR_TYPE CMRminorType(CMR_MINOR* minor)
    size_t CMRminorNumPivots(CMR_MINOR* minor)
    size_t* CMRminorPivotRows(CMR_MINOR* minor)
    size_t* CMRminorPivotColumns(CMR_MINOR* minor)
    CMR_SUBMAT* CMRminorSubmatrix(CMR_MINOR* minor)
    # CMR_ERROR CMRminorWriteToFile(CMR* cmr, CMR_MINOR* minor, size_t numRows, size_t numColumns, const char* fileName)

cdef extern from "cmr/separation.h":

    ctypedef int CMR_SEPA_FLAGS

    const int CMR_SEPA_FIRST
    const int CMR_SEPA_SECOND
    const int CMR_SEPA_FLAG_RANK1
    const int CMR_SEPA_FLAG_RANK2
    const int CMR_SEPA_MASK_CHILD
    const int CMR_SEPA_MASK_EXTRA

    ctypedef int CMR_SEPA_TYPE

    const int CMR_SEPA_TYPE_TWO
    const int CMR_SEPA_TYPE_THREE_DISTRIBUTED_RANKS
    const int CMR_SEPA_TYPE_THREE_CONCENTRATED_RANK

    ctypedef struct CMR_SEPA:
        size_t numRows
        size_t numColumns
        int* rowsFlags
        int* columnsFlags
        CMR_SEPA_TYPE type

    CMR_ERROR CMRsepaCreate(CMR* cmr, size_t numRows, size_t numColumns, CMR_SEPA** psepa)
    CMR_ERROR CMRsepaFree(CMR* cmr, CMR_SEPA** psepa)
    CMR_ERROR CMRsepaTranspose(CMR* cmr, CMR_SEPA* sepa, CMR_SEPA** ptransposed)
    CMR_ERROR CMRsepaComputeSizes(CMR_SEPA* sepa, size_t* pnumRowsTopLeft, size_t* pnumColumnsTopLeft, size_t* pnumRowsBottomRight, size_t* pnumColumnsBottomRight)
    CMR_ERROR CMRsepaFindBinaryRepresentatives(CMR* cmr, CMR_SEPA* sepa, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, bool* pswapped, CMR_SUBMAT** pviolator)
    CMR_ERROR CMRsepaFindBinaryRepresentativesSubmatrix(CMR* cmr, CMR_SEPA* sepa, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, CMR_SUBMAT* submatrix, bool* pswapped, CMR_SUBMAT** pviolator)
    CMR_ERROR CMRsepaGetRepresentatives(CMR_SEPA* sepa, size_t reprRows[2][3], size_t reprColumns[2][3])
    CMR_ERROR CMRsepaGetProjection(CMR_SEPA* sepa, size_t part, size_t* rowsToPart, size_t* columnsToPart, size_t* pnumPartRows, size_t* pnumPartColumns)
    CMR_ERROR CMRsepaCheckTernary(CMR* cmr, CMR_SEPA* sepa, CMR_CHRMAT* matrix, bool* pisTernary, CMR_SUBMAT** pviolator)
    CMR_ERROR CMRsepaCheckTernarySubmatrix(CMR* cmr, CMR_SEPA* sepa, CMR_CHRMAT* matrix, CMR_SUBMAT* submatrix, bool* pisTernary, CMR_SUBMAT** pviolator)
    CMR_ERROR CMRonesumCompose(CMR* cmr, size_t numMatrices, CMR_CHRMAT** matrices, CMR_CHRMAT** presult)
    CMR_ERROR CMRtwosumCompose(CMR* cmr, CMR_CHRMAT* first, CMR_CHRMAT* second, size_t* firstSpecialRows, size_t* firstSpecialColumns, size_t* secondSpecialRows, size_t* secondSpecialColumns, int8_t characteristic, CMR_CHRMAT** presult)
    CMR_ERROR CMRtwosumDecomposeFirst(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, CMR_CHRMAT** pfirst, size_t* firstRowsOrigin, size_t* firstColumnsOrigin, size_t* rowsToFirst, size_t* columnsToFirst, size_t* firstSpecialRows, size_t* firstSpecialColumns)
    CMR_ERROR CMRtwosumDecomposeSecond(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, CMR_CHRMAT** psecond, size_t* secondRowsOrigin, size_t* secondColumnsOrigin, size_t* rowsToSecond, size_t* columnsToSecond, size_t* secondSpecialRows, size_t* secondSpecialColumns)
    CMR_ERROR CMRdeltasumCompose(CMR* cmr, CMR_CHRMAT* first, CMR_CHRMAT* second, size_t* firstSpecialRows, size_t* firstSpecialColumns, size_t* secondSpecialRows, size_t* secondSpecialColumns, int8_t characteristic, CMR_CHRMAT** presult)
    CMR_ERROR CMRdeltasumDecomposeEpsilon(CMR* cmr, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, CMR_SEPA* sepa, signed char* pepsilon)
    CMR_ERROR CMRdeltasumDecomposeFirst(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, signed char epsilon, CMR_CHRMAT** pfirst, size_t* firstRowsOrigin, size_t* firstColumnsOrigin, size_t* rowsToFirst, size_t* columnsToFirst, size_t* firstSpecialRows, size_t* firstSpecialColumns)
    CMR_ERROR CMRdeltasumDecomposeSecond(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, signed char epsilon, CMR_CHRMAT** psecond, size_t* secondRowsOrigin, size_t* secondColumnsOrigin, size_t* rowsToSecond, size_t* columnsToSecond, size_t* secondSpecialRows, size_t* secondSpecialColumns)

    CMR_ERROR CMRysumCompose(CMR* cmr, CMR_CHRMAT* first, CMR_CHRMAT* second, size_t* firstSpecialRows, size_t* firstSpecialColumns, size_t* secondSpecialRows, size_t* secondSpecialColumns, int8_t characteristic, CMR_CHRMAT** presult)
    CMR_ERROR CMRysumDecomposeEpsilon(CMR* cmr, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, CMR_SEPA* sepa, signed char* pepsilon)
    CMR_ERROR CMRysumDecomposeFirst(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, signed char epsilon, CMR_CHRMAT** pfirst, size_t* firstRowsOrigin, size_t* firstColumnsOrigin, size_t* rowsToFirst, size_t* columnsToFirst, size_t* firstSpecialRows, size_t* firstSpecialColumns)
    CMR_ERROR CMRysumDecomposeSecond(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, signed char epsilon, CMR_CHRMAT** psecond, size_t* secondRowsOrigin, size_t* secondColumnsOrigin, size_t* rowsToSecond, size_t* columnsToSecond, size_t* secondSpecialRows, size_t* secondSpecialColumns)

    CMR_ERROR CMRthreesumCompose(CMR* cmr, CMR_CHRMAT* first, CMR_CHRMAT* second, size_t* firstSpecialRows, size_t* firstSpecialColumns, size_t* secondSpecialRows, size_t* secondSpecialColumns, int8_t characteristic, CMR_CHRMAT** presult)
    CMR_ERROR CMRthreesumDecomposeSearchConnecting(CMR* cmr, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, CMR_SEPA* sepa, size_t* specialRows, size_t* specialColumns, signed char* pgamma, signed char* pbeta)
    CMR_ERROR CMRthreesumDecomposeSignConnecting(CMR* cmr, CMR_CHRMAT* matrix, CMR_CHRMAT* transpose, CMR_SEPA* sepa, size_t* specialRows, size_t* specialColumns, signed char* pgamma, signed char* pbeta)
    CMR_ERROR CMRthreesumDecomposeFirst(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, size_t* specialRows, size_t* specialColumns, signed char beta, CMR_CHRMAT** pfirst, size_t* firstRowsOrigin, size_t* firstColumnsOrigin, size_t* rowsToFirst, size_t* columnsToFirst, size_t* firstSpecialRows, size_t* firstSpecialColumns)
    CMR_ERROR CMRthreesumDecomposeSecond(CMR* cmr, CMR_CHRMAT* matrix, CMR_SEPA* sepa, size_t* specialRows, size_t* specialColumns, signed char gamma, CMR_CHRMAT** psecond, size_t* secondRowsOrigin, size_t* secondColumnsOrigin, size_t* rowsToSecond, size_t* columnsToSecond, size_t* secondSpecialRows, size_t* secondSpecialColumns)

cdef extern from "cmr/graphic.h":

    ctypedef struct CMR_GRAPHIC_STATISTICS:
        uint32_t totalCount
        double totalTime
        uint32_t checkCount
        double checkTime
        uint32_t applyCount
        double applyTime
        uint32_t transposeCount
        double transposeTime

    CMR_ERROR CMRgraphicStatsInit(CMR_GRAPHIC_STATISTICS* stats)
    # CMR_ERROR CMRgraphicStatsPrint(FILE* stream, CMR_GRAPHIC_STATISTICS* stats, const char* prefix)
    CMR_ERROR CMRgraphicComputeMatrix(CMR* cmr, CMR_GRAPH* graph, CMR_CHRMAT** pmatrix, CMR_CHRMAT** ptranspose, int numForestEdges, CMR_GRAPH_EDGE* forestEdges, int numCoforestEdges, CMR_GRAPH_EDGE* coforestEdges, bool* pisCorrectForest)
    CMR_ERROR CMRgraphicTestMatrix(CMR* cmr, CMR_CHRMAT* matrix, bool* pisGraphic, CMR_GRAPH** pgraph, CMR_GRAPH_EDGE** pforestEdges, CMR_GRAPH_EDGE** pcoforestEdges, CMR_SUBMAT** psubmatrix, CMR_GRAPHIC_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRgraphicTestTranspose(CMR* cmr, CMR_CHRMAT* matrix, bool* pisCographic, CMR_GRAPH** pgraph, CMR_GRAPH_EDGE** pforestEdges, CMR_GRAPH_EDGE** pcoforestEdges, CMR_SUBMAT** psubmatrix, CMR_GRAPHIC_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRgraphicTestColumnSubmatrixGreedy(CMR* cmr, CMR_CHRMAT* transpose, size_t* orderedColumns, CMR_SUBMAT** psubmatrix)

cdef extern from "cmr/series_parallel.h":

    ctypedef struct CMR_SP_STATISTICS:
        uint32_t totalCount
        double totalTime
        uint32_t reduceCount
        double reduceTime
        uint32_t wheelCount
        double wheelTime
        uint32_t nonbinaryCount
        double nonbinaryTime

    CMR_ERROR CMRspStatsInit(CMR_SP_STATISTICS* stats)

    # CMR_ERROR CMRspStatsPrint(FILE* stream, CMR_SP_STATISTICS* stats, const char* prefix)

    ctypedef struct CMR_SP_REDUCTION:
        CMR_ELEMENT element
        CMR_ELEMENT mate

    char* CMRspReductionString(CMR_SP_REDUCTION reduction, char* buffer)

    bint CMRspIsRow(CMR_SP_REDUCTION reduction)
    bint CMRspIsColumn(CMR_SP_REDUCTION reduction)
    bint CMRspIsZero(CMR_SP_REDUCTION reduction)
    bint CMRspIsUnit(CMR_SP_REDUCTION reduction)
    bint CMRspIsCopy(CMR_SP_REDUCTION reduction)
    bint CMRspIsValid(CMR_SP_REDUCTION reduction)

    CMR_ERROR CMRspTestBinary(CMR* cmr, CMR_CHRMAT* matrix, bool* pisSeriesParallel, CMR_SP_REDUCTION* reductions, size_t* pnumReductions, CMR_SUBMAT** preducedSubmatrix, CMR_SUBMAT** pviolatorSubmatrix, CMR_SP_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRspTestTernary(CMR* cmr, CMR_CHRMAT* matrix, bool* pisSeriesParallel, CMR_SP_REDUCTION* reductions, size_t* pnumReductions, CMR_SUBMAT** preducedSubmatrix, CMR_SUBMAT** pviolatorSubmatrix, CMR_SP_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRspDecomposeBinary(CMR* cmr, CMR_CHRMAT* matrix, bool* pisSeriesParallel, CMR_SP_REDUCTION* reductions, size_t maxNumReductions, size_t* pnumReductions, CMR_SUBMAT** preducedSubmatrix, CMR_SUBMAT** pviolatorSubmatrix, CMR_SEPA** pseparation, CMR_SP_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRspDecomposeTernary(CMR* cmr, CMR_CHRMAT* matrix, bool* pisSeriesParallel, CMR_SP_REDUCTION* reductions, size_t maxNumReductions, size_t* pnumReductions, CMR_SUBMAT** preducedSubmatrix, CMR_SUBMAT** pviolatorSubmatrix, CMR_SEPA** pseparation, CMR_SP_STATISTICS* stats, double timeLimit)

cdef extern from "cmr/network.h":

    ctypedef struct CMR_NETWORK_STATISTICS:
        uint32_t totalCount
        double totalTime
        CMR_CAMION_STATISTICS camion
        CMR_GRAPHIC_STATISTICS graphic

    CMR_ERROR CMRnetworkStatsInit(CMR_NETWORK_STATISTICS* stats)
    # CMR_ERROR CMRstatsNetworkPrint(FILE* stream, CMR_NETWORK_STATISTICS* stats, const char* prefix)
    CMR_ERROR CMRnetworkComputeMatrix(CMR* cmr, CMR_GRAPH* digraph, CMR_CHRMAT** pmatrix, CMR_CHRMAT** ptranspose, bool* arcsReversed, int numForestArcs, CMR_GRAPH_EDGE* forestArcs, int numCoforestArcs, CMR_GRAPH_EDGE* coforestArcs, bool* pisCorrectForest)
    CMR_ERROR CMRnetworkTestMatrix(CMR* cmr, CMR_CHRMAT* matrix, bool* pisNetwork, bool* psupportIsGraphic, CMR_GRAPH** pdigraph, CMR_GRAPH_EDGE** pforestArcs, CMR_GRAPH_EDGE** pcoforestArcs, bool** parcsReversed, CMR_SUBMAT** psubmatrix, CMR_NETWORK_STATISTICS* stats, double timeLimit)
    CMR_ERROR CMRnetworkTestTranspose(CMR* cmr, CMR_CHRMAT* matrix, bool* pisConetwork, bool* psupportIsCographic, CMR_GRAPH** pdigraph, CMR_GRAPH_EDGE** pforestArcs, CMR_GRAPH_EDGE** pcoforestArcs, bool** parcsReversed, CMR_SUBMAT** psubmatrix, CMR_NETWORK_STATISTICS* stats, double timeLimit)


cdef extern from "cmr/seymour.h":

    ctypedef int CMR_SEYMOUR_DECOMPOSE_FLAG

    const int CMR_SEYMOUR_DECOMPOSE_FLAG_DISTRIBUTED_MASK
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_DISTRIBUTED_PIVOT
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_DISTRIBUTED_DELTASUM
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_DISTRIBUTED_YSUM
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_CONCENTRATED_MASK
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_CONCENTRATED_PIVOT
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_CONCENTRATED_THREESUM
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_SEYMOUR
    const int CMR_SEYMOUR_DECOMPOSE_FLAG_TRUEMPER

    ctypedef struct CMR_SEYMOUR_PARAMS:
        bool stopWhenIrregular
        bool stopWhenNongraphic
        bool stopWhenNoncographic
        bool stopWhenNeitherGraphicNorCoGraphic
        bool seriesParallel
        bool planarityCheck
        bool directGraphicness
        bool preferGraphicness
        int decomposeStrategy
        bool constructLeafGraphs
        bool constructAllGraphs

    CMR_ERROR CMRseymourParamsInit(CMR_SEYMOUR_PARAMS* params)

    ctypedef struct CMR_SEYMOUR_STATS:
        uint32_t totalCount
        double totalTime
        CMR_SP_STATISTICS seriesParallel
        CMR_GRAPHIC_STATISTICS graphic
        CMR_NETWORK_STATISTICS network
        uint32_t sequenceExtensionCount
        double sequenceExtensionTime
        uint32_t sequenceGraphicCount
        double sequenceGraphicTime
        uint32_t enumerationCount
        double enumerationTime
        uint32_t enumerationCandidatesCount

    CMR_ERROR CMRseymourStatsInit(CMR_SEYMOUR_STATS* stats)
    # CMR_ERROR CMRseymourStatsPrint(FILE* stream, CMR_SEYMOUR_STATS* stats, const char* prefix)

    ctypedef struct CMR_SEYMOUR_NODE

    ctypedef int CMR_SEYMOUR_NODE_TYPE

    const int CMR_SEYMOUR_NODE_TYPE_IRREGULAR
    const int CMR_SEYMOUR_NODE_TYPE_UNKNOWN
    const int CMR_SEYMOUR_NODE_TYPE_SERIES_PARALLEL
    const int CMR_SEYMOUR_NODE_TYPE_PIVOTS
    const int CMR_SEYMOUR_NODE_TYPE_GRAPH
    const int CMR_SEYMOUR_NODE_TYPE_COGRAPH
    const int CMR_SEYMOUR_NODE_TYPE_PLANAR
    const int CMR_SEYMOUR_NODE_TYPE_R10
    const int CMR_SEYMOUR_NODE_TYPE_ONESUM
    const int CMR_SEYMOUR_NODE_TYPE_TWOSUM
    const int CMR_SEYMOUR_NODE_TYPE_DELTASUM
    const int CMR_SEYMOUR_NODE_TYPE_THREESUM
    const int CMR_SEYMOUR_NODE_TYPE_YSUM

    bool CMRseymourIsTernary(CMR_SEYMOUR_NODE* node)
    bool CMRseymourHasTranspose(CMR_SEYMOUR_NODE* node)
    CMR_CHRMAT* CMRseymourGetMatrix(CMR_SEYMOUR_NODE* node)
    CMR_CHRMAT* CMRseymourGetTranspose(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourNumChildren(CMR_SEYMOUR_NODE* node)
    CMR_SEYMOUR_NODE* CMRseymourChild(CMR_SEYMOUR_NODE* node, size_t childIndex)
    CMR_SEYMOUR_NODE_TYPE CMRseymourType(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourNumMinors(CMR_SEYMOUR_NODE* node)
    CMR_MINOR* CMRseymourMinor(CMR_SEYMOUR_NODE* node, size_t minorIndex)
    int8_t CMRseymourGraphicness(CMR_SEYMOUR_NODE* node)
    int8_t CMRseymourCographicness(CMR_SEYMOUR_NODE* node)
    int8_t CMRseymourRegularity(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourNumRows(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourNumColumns(CMR_SEYMOUR_NODE* node)
    CMR_ELEMENT* CMRseymourChildRowsToParent(CMR_SEYMOUR_NODE* node, size_t childIndex)
    CMR_ELEMENT* CMRseymourChildColumnsToParent(CMR_SEYMOUR_NODE* node, size_t childIndex)
    size_t* CMRseymourChildSpecialRows(CMR_SEYMOUR_NODE* node, size_t childIndex)
    size_t* CMRseymourChildSpecialColumns(CMR_SEYMOUR_NODE* node, size_t childIndex)
    CMR_GRAPH* CMRseymourGraph(CMR_SEYMOUR_NODE* node)
    CMR_GRAPH_EDGE* CMRseymourGraphForest(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourGraphSizeForest(CMR_SEYMOUR_NODE* node)
    CMR_GRAPH_EDGE* CMRseymourGraphCoforest(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourGraphSizeCoforest(CMR_SEYMOUR_NODE* node)
    bool* CMRseymourGraphArcsReversed(CMR_SEYMOUR_NODE* node)
    CMR_GRAPH* CMRseymourCograph(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourCographSizeForest(CMR_SEYMOUR_NODE* node)
    CMR_GRAPH_EDGE* CMRseymourCographForest(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourCographSizeCoforest(CMR_SEYMOUR_NODE* node)
    CMR_GRAPH_EDGE* CMRseymourCographCoforest(CMR_SEYMOUR_NODE* node)
    bool* CMRseymourCographArcsReversed(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourNumPivots(CMR_SEYMOUR_NODE* node)
    size_t* CMRseymourPivotRows(CMR_SEYMOUR_NODE* node)
    size_t* CMRseymourPivotColumns(CMR_SEYMOUR_NODE* node)
    size_t CMRseymourGetUsed(CMR_SEYMOUR_NODE* node)
    # CMR_ERROR CMRseymourPrint(CMR* cmr, CMR_SEYMOUR_NODE* node, FILE* stream, bool printChildren, bool printParentElements, bool printMatrices, bool printGraphs, bool printReductions, bool printPivots)
    CMR_ERROR CMRseymourCapture(CMR* cmr, CMR_SEYMOUR_NODE* node)
    CMR_ERROR CMRseymourRelease(CMR* cmr, CMR_SEYMOUR_NODE** pnode)
    CMR_ERROR CMRseymourCreate(CMR* cmr, CMR_SEYMOUR_NODE** pnode, bool isTernary, CMR_CHRMAT* matrix, bool copyMatrix)
    CMR_ERROR CMRseymourCloneUnknown(CMR* cmr, CMR_SEYMOUR_NODE* node, CMR_SEYMOUR_NODE** pclone)
    CMR_ERROR CMRseymourCloneSubtrees(CMR* cmr, size_t numSubtrees, CMR_SEYMOUR_NODE** subtreeRoots,CMR_SEYMOUR_NODE** clonedSubtrees)


cdef extern from "cmr/regular.h":

    ctypedef struct CMR_REGULAR_PARAMS:
        CMR_SEYMOUR_PARAMS seymour

    CMR_ERROR CMRregularParamsInit(CMR_REGULAR_PARAMS* params)

    ctypedef struct CMR_REGULAR_STATS:
        CMR_SEYMOUR_STATS seymour

    CMR_ERROR CMRregularStatsInit(CMR_REGULAR_STATS* stats)
    # CMR_ERROR CMRstatsRegularPrint(FILE* stream, CMR_REGULAR_STATS* stats, const char* prefix)
    CMR_ERROR CMRregularTest(CMR* cmr, CMR_CHRMAT* matrix, bool* pisRegular, CMR_SEYMOUR_NODE** pnode, CMR_MINOR** pminor, CMR_REGULAR_PARAMS* params, CMR_REGULAR_STATS* stats, double timeLimit)
    CMR_ERROR CMRregularCompleteDecomposition(CMR* cmr, CMR_SEYMOUR_NODE* node, CMR_REGULAR_PARAMS* params, CMR_REGULAR_STATS* stats, double timeLimit)
    CMR_ERROR CMRregularRefineDecomposition(CMR* cmr, size_t numNodes, CMR_SEYMOUR_NODE** nodes, CMR_REGULAR_PARAMS* params, CMR_REGULAR_STATS* stats, double timeLimit)


cdef extern from "cmr/tu.h":

    const int CMR_TU_ALGORITHM_DECOMPOSITION
    const int CMR_TU_ALGORITHM_EULERIAN
    const int CMR_TU_ALGORITHM_PARTITION

    ctypedef int CMR_TU_ALGORITHM

    ctypedef struct CMR_TU_PARAMS:
        CMR_TU_ALGORITHM algorithm
        CMR_SEYMOUR_PARAMS seymour
        bool ternary
        bool camionFirst
        bool naiveSubmatrix

    CMR_ERROR CMRtuParamsInit(CMR_TU_PARAMS* params)

    ctypedef struct CMR_TU_STATS:
        CMR_SEYMOUR_STATS seymour
        CMR_CAMION_STATISTICS camion

        uint32_t enumerationRowSubsets
        uint32_t enumerationColumnSubsets
        double enumerationTime

        uint32_t partitionRowSubsets
        uint32_t partitionColumnSubsets
        double partitionTime

    CMR_ERROR CMRtuStatsInit(CMR_TU_STATS* stats)
    # CMR_ERROR CMRtuStatsPrint(FILE* stream, CMR_TU_STATS* stats, const char* prefix)
    CMR_ERROR CMRtuTest(CMR* cmr, CMR_CHRMAT* matrix, bool* pisTotallyUnimodular, CMR_SEYMOUR_NODE** proot, CMR_SUBMAT** psubmatrix, CMR_TU_PARAMS* params, CMR_TU_STATS* stats, double timeLimit)
    CMR_ERROR CMRtuCompleteDecomposition(CMR* cmr, CMR_SEYMOUR_NODE* node, CMR_TU_PARAMS* params, CMR_TU_STATS* stats, double timeLimit)


cdef extern from "cmr/equimodular.h":

    ctypedef struct CMR_EQUIMODULAR_PARAMS:
        CMR_TU_PARAMS tu

    CMR_ERROR CMRequimodularParamsInit(CMR_EQUIMODULAR_PARAMS* params)

    ctypedef struct CMR_EQUIMODULAR_STATS:
        uint32_t totalCount
        double totalTime
        double linalgTime
        CMR_TU_STATS tu

    CMR_ERROR CMRequimodularStatsInit(CMR_EQUIMODULAR_STATS* stats)

    CMR_ERROR CMRequimodularTest(CMR* cmr, CMR_INTMAT* matrix,
                                    bool* pisEquimodular, int64_t *pgcdDet,
                                    CMR_EQUIMODULAR_PARAMS* params, CMR_EQUIMODULAR_STATS* stats,
                                    double timeLimit)
    CMR_ERROR CMRequimodularTestStrong(CMR* cmr, CMR_INTMAT* matrix,
                                          bool* pisStronglyEquimodular, int64_t *pgcdDet,
                                          CMR_EQUIMODULAR_PARAMS* params, CMR_EQUIMODULAR_STATS* stats,
                                          double timeLimit)
    CMR_ERROR CMRunimodularTest(CMR* cmr, CMR_INTMAT* matrix,
                                   bool* pisUnimodular,
                                   CMR_EQUIMODULAR_PARAMS* params, CMR_EQUIMODULAR_STATS* stats,
                                   double timeLimit)
    CMR_ERROR CMRunimodularTestStrong(CMR* cmr, CMR_INTMAT* matrix,
                                         bool* pisStronglyUnimodular,
                                         CMR_EQUIMODULAR_PARAMS* params, CMR_EQUIMODULAR_STATS* stats,
                                         double timeLimit)


cdef extern from "cmr/ctu.h":

    ctypedef struct CMR_CTU_PARAMS:
        CMR_TU_PARAMS tu

    CMR_ERROR CMRctuParamsInit(CMR_CTU_PARAMS* params)

    ctypedef struct CMR_CTU_STATS:
        uint32_t totalCount
        double totalTime
        CMR_TU_STATS tu

    CMR_ERROR CMRstatsComplementTotalUnimodularityInit(CMR_CTU_STATS* stats)
    # CMR_ERROR CMRstatsComplementTotalUnimodularityPrint(FILE* stream, CMR_CTU_STATS* stats, const char* prefix)
    CMR_ERROR CMRctuComplementRowColumn(CMR* cmr, CMR_CHRMAT* matrix, size_t complementRow, size_t complementColumn, CMR_CHRMAT** presult)
    CMR_ERROR CMRctuTest(CMR* cmr, CMR_CHRMAT* matrix, bool* pisComplementTotallyUnimodular, size_t* pcomplementRow, size_t* pcomplementColumn, CMR_CTU_PARAMS* params, CMR_CTU_STATS* stats, double timeLimit)


cdef extern from "cmr/balanced.h":
    ctypedef int CMR_BALANCED_ALGORITHM

    const int CMR_BALANCED_ALGORITHM_AUTO
    const int CMR_BALANCED_ALGORITHM_SUBMATRIX
    const int CMR_BALANCED_ALGORITHM_GRAPH

    ctypedef struct CMR_BALANCED_PARAMS:
        CMR_BALANCED_ALGORITHM algorithm
        bool seriesParallel

    ctypedef struct CMR_BALANCED_STATS:
        uint32_t totalCount
        double totalTime
        CMR_SP_STATISTICS seriesParallel
        size_t enumeratedRowSubsets
        size_t enumeratedColumnSubsets

    CMR_ERROR CMRbalancedParamsInit(CMR_BALANCED_PARAMS* params)

    CMR_ERROR CMRbalancedStatsInit(CMR_BALANCED_STATS* stats)

    # CMR_ERROR CMRbalancedStatsPrint(FILE* stream, CMR_BALANCED_STATS* stats, const char* prefix)

    CMR_ERROR CMRbalancedTest(CMR* cmr, CMR_CHRMAT* matrix, bool* pisBalanced, CMR_SUBMAT** psubmatrix, CMR_BALANCED_PARAMS* params, CMR_BALANCED_STATS* stats, double timeLimit)


# cdef extern from "cmr/block_decomposition.h":

#     ctypedef struct CMR_MATRIX

#     ctypedef struct CMR_BLOCK:
#         CMR_MATRIX* matrix
#         CMR_MATRIX* transpose
#         size_t* rowsToOriginal
#         size_t* columnsToOriginal

#     CMR_ERROR CMRdecomposeBlocks(
#         CMR* cmr,
#         CMR_MATRIX* matrix,
#         size_t matrixType,
#         size_t targetType,
#         size_t* pnumBlocks,
#         CMR_BLOCK** pblocks,
#         size_t* rowsToBlock,
#         size_t* columnsToBlock,
#         size_t* rowsToBlockRows,
#         size_t* columnsToBlockColumns
#     )


# Our global CMR environment
cdef CMR *cmr

cdef CMR_CALL(CMR_ERROR _cmr_error)
