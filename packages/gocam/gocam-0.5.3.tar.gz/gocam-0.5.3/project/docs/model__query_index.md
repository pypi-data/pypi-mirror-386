
# Slot: query_index

An optional object that contains the results of indexing a model with various summary statistics and retrieval indices.

URI: [gocam:model__query_index](https://w3id.org/gocam/model__query_index)


## Domain and Range

None &#8594;  <sub>0..1</sub> [QueryIndex](QueryIndex.md)

## Parents


## Children


## Used by

 * [Model](Model.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | This is typically not populated in the primary transactional store (OLTP processing), because the values will be redundant with the primary edited components of the model. It is intended to be populated in batch *after* editing, and then used for generating reports, or for indexing in web applications. |
