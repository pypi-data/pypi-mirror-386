
# Slot: term

A "term" that is an entity database object representing an individual gene product.

URI: [gocam:EnabledByGeneProductAssociation_term](https://w3id.org/gocam/EnabledByGeneProductAssociation_term)


## Domain and Range

[EnabledByGeneProductAssociation](EnabledByGeneProductAssociation.md) &#8594;  <sub>0..1</sub> [GeneProductTermObject](GeneProductTermObject.md)

## Parents

 *  is_a: [➞term](enabledByAssociation__term.md)

## Children


## Used by

 * [EnabledByGeneProductAssociation](EnabledByGeneProductAssociation.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | gocam:term |
| **Comments:** | | In the context of the GO workflow, the allowed values for this field come from the GPI file from an authoritative source. For example, the authoritative source for human is the EBI GOA group, and the GPI for this group consists of UniProtKB IDs (for proteins) and RNA Central IDs (for RNA gene products) |
|  | | A gene identifier may be provided as a value here (if the authoritative GPI allows it). Note that the *interpretation* of the gene ID in the context of a GO-CAM model is the (spliceform and proteoform agnostic) *product* of that gene. |
| **Examples:** | | Example({
  'value': 'UniProtKB:Q96Q11',
  'description': 'The protein product of the Homo sapiens TRNT1 gene'
}) |
|  | | Example({
  'value': 'RNAcentral:URS00026A1FBE_9606',
  'description': 'An RNA product of this RNA central gene'
}) |
