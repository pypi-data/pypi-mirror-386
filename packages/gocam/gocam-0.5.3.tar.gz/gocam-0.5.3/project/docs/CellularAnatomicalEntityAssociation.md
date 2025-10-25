
# Class: CellularAnatomicalEntityAssociation

An association between an activity and a cellular anatomical entity term

URI: [gocam:CellularAnatomicalEntityAssociation](https://w3id.org/gocam/CellularAnatomicalEntityAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[EvidenceItem],[CellularAnatomicalEntityTermObject],[CellularAnatomicalEntityTermObject]<term%200..1-%20[CellularAnatomicalEntityAssociation&#124;type(i):string%20%3F],[CellTypeAssociation]<part_of%200..1-++[CellularAnatomicalEntityAssociation],[Activity]++-%20occurs_in%200..1>[CellularAnatomicalEntityAssociation],[TermAssociation]^-[CellularAnatomicalEntityAssociation],[CellTypeAssociation],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[EvidenceItem],[CellularAnatomicalEntityTermObject],[CellularAnatomicalEntityTermObject]<term%200..1-%20[CellularAnatomicalEntityAssociation&#124;type(i):string%20%3F],[CellTypeAssociation]<part_of%200..1-++[CellularAnatomicalEntityAssociation],[Activity]++-%20occurs_in%200..1>[CellularAnatomicalEntityAssociation],[TermAssociation]^-[CellularAnatomicalEntityAssociation],[CellTypeAssociation],[Activity])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞occurs_in](activity__occurs_in.md)*  <sub>0..1</sub>  **[CellularAnatomicalEntityAssociation](CellularAnatomicalEntityAssociation.md)**

## Attributes


### Own

 * [➞part_of](cellularAnatomicalEntityAssociation__part_of.md)  <sub>0..1</sub>
     * Description: Optional extension allowing hierarchical nesting of CCs
     * Range: [CellTypeAssociation](CellTypeAssociation.md)
 * [CellularAnatomicalEntityAssociation➞term](CellularAnatomicalEntityAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [CellularAnatomicalEntityTermObject](CellularAnatomicalEntityTermObject.md)

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
