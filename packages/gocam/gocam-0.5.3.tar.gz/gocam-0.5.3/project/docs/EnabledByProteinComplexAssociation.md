
# Class: EnabledByProteinComplexAssociation

An association between an activity and a protein complex, where the complex carries out the activity. This should only be used when the activity cannot be attributed to an individual member of the complex, but instead the function is an emergent property of the complex.

URI: [gocam:EnabledByProteinComplexAssociation](https://w3id.org/gocam/EnabledByProteinComplexAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[ProteinComplexTermObject],[GeneProductTermObject],[EvidenceItem],[ProteinComplexTermObject]<term%200..1-%20[EnabledByProteinComplexAssociation&#124;type(i):string%20%3F],[GeneProductTermObject]<members%200..*-%20[EnabledByProteinComplexAssociation],[EnabledByAssociation]^-[EnabledByProteinComplexAssociation],[EnabledByAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[ProteinComplexTermObject],[GeneProductTermObject],[EvidenceItem],[ProteinComplexTermObject]<term%200..1-%20[EnabledByProteinComplexAssociation&#124;type(i):string%20%3F],[GeneProductTermObject]<members%200..*-%20[EnabledByProteinComplexAssociation],[EnabledByAssociation]^-[EnabledByProteinComplexAssociation],[EnabledByAssociation])

## Parents

 *  is_a: [EnabledByAssociation](EnabledByAssociation.md) - An association between an activity and the gene product or complex or set of potential gene products

## Referenced by Class


## Attributes


### Own

 * [➞members](enabledByProteinComplexAssociation__members.md)  <sub>0..\*</sub>
     * Description: The gene products that are part of the complex
     * Range: [GeneProductTermObject](GeneProductTermObject.md)
 * [EnabledByProteinComplexAssociation➞term](EnabledByProteinComplexAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [ProteinComplexTermObject](ProteinComplexTermObject.md)
     * Example: GO:0032991 The generic GO entry for a protein complex. If this is the value of `term`, then members *must* be specified.
     * Example: ComplexPortal:CPX-969 The human Caspase-2 complex

### Inherited from EnabledByAssociation:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | Protein complexes can be specified either by *pre-composition* or *post-composition*. For pre-composition, a species-specific named protein complex (such as an entry in ComplexPortal) can be specified, in which case the value of `members` is *implicit*. For post-composition, the placeholder term "GO:0032991" can be used, in which case `members` must be *explicitly* specified. An intermediate case is when a named class in GO that is a subclass of "GO:0032991" is used. In this case, `members` should still be specified, as this may only be partially specified by the GO class. |
