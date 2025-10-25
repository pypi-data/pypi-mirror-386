
# Class: CellTypeAssociation

An association between an activity and a cell type term

URI: [gocam:CellTypeAssociation](https://w3id.org/gocam/CellTypeAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[GrossAnatomyAssociation],[EvidenceItem],[CellTypeTermObject],[CellTypeTermObject]<term%200..1-%20[CellTypeAssociation&#124;type(i):string%20%3F],[GrossAnatomyAssociation]<part_of%200..1-++[CellTypeAssociation],[CellularAnatomicalEntityAssociation]++-%20part_of%200..1>[CellTypeAssociation],[TermAssociation]^-[CellTypeAssociation],[CellularAnatomicalEntityAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[GrossAnatomyAssociation],[EvidenceItem],[CellTypeTermObject],[CellTypeTermObject]<term%200..1-%20[CellTypeAssociation&#124;type(i):string%20%3F],[GrossAnatomyAssociation]<part_of%200..1-++[CellTypeAssociation],[CellularAnatomicalEntityAssociation]++-%20part_of%200..1>[CellTypeAssociation],[TermAssociation]^-[CellTypeAssociation],[CellularAnatomicalEntityAssociation])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞part_of](cellularAnatomicalEntityAssociation__part_of.md)*  <sub>0..1</sub>  **[CellTypeAssociation](CellTypeAssociation.md)**

## Attributes


### Own

 * [➞part_of](cellTypeAssociation__part_of.md)  <sub>0..1</sub>
     * Range: [GrossAnatomyAssociation](GrossAnatomyAssociation.md)
 * [CellTypeAssociation➞term](CellTypeAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [CellTypeTermObject](CellTypeTermObject.md)

### Inherited from TermAssociation:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
