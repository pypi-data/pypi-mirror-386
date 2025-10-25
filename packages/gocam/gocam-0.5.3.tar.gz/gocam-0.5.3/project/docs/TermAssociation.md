
# Class: TermAssociation

An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

URI: [gocam:TermAssociation](https://w3id.org/gocam/TermAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[TermObject]<term%200..1-%20[TermAssociation&#124;type(i):string%20%3F],[TermAssociation]^-[MoleculeAssociation],[TermAssociation]^-[MolecularFunctionAssociation],[TermAssociation]^-[GrossAnatomyAssociation],[TermAssociation]^-[CellularAnatomicalEntityAssociation],[TermAssociation]^-[CellTypeAssociation],[TermAssociation]^-[BiologicalProcessAssociation],[Association]^-[TermAssociation],[ProvenanceInfo],[MoleculeAssociation],[MolecularFunctionAssociation],[GrossAnatomyAssociation],[EvidenceItem],[CellularAnatomicalEntityAssociation],[CellTypeAssociation],[BiologicalProcessAssociation],[Association])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[TermObject]<term%200..1-%20[TermAssociation&#124;type(i):string%20%3F],[TermAssociation]^-[MoleculeAssociation],[TermAssociation]^-[MolecularFunctionAssociation],[TermAssociation]^-[GrossAnatomyAssociation],[TermAssociation]^-[CellularAnatomicalEntityAssociation],[TermAssociation]^-[CellTypeAssociation],[TermAssociation]^-[BiologicalProcessAssociation],[Association]^-[TermAssociation],[ProvenanceInfo],[MoleculeAssociation],[MolecularFunctionAssociation],[GrossAnatomyAssociation],[EvidenceItem],[CellularAnatomicalEntityAssociation],[CellTypeAssociation],[BiologicalProcessAssociation],[Association])

## Parents

 *  is_a: [Association](Association.md) - An abstract grouping for different kinds of evidence-associated provenance

## Children

 * [BiologicalProcessAssociation](BiologicalProcessAssociation.md) - An association between an activity and a biological process term
 * [CellTypeAssociation](CellTypeAssociation.md) - An association between an activity and a cell type term
 * [CellularAnatomicalEntityAssociation](CellularAnatomicalEntityAssociation.md) - An association between an activity and a cellular anatomical entity term
 * [GrossAnatomyAssociation](GrossAnatomyAssociation.md) - An association between an activity and a gross anatomical structure term
 * [MolecularFunctionAssociation](MolecularFunctionAssociation.md) - An association between an activity and a molecular function term
 * [MoleculeAssociation](MoleculeAssociation.md) - An association between an activity and a molecule term

## Referenced by Class


## Attributes


### Own

 * [➞term](termAssociation__term.md)  <sub>0..1</sub>
     * Description: The ontology term that describes the nature of the association
     * Range: [TermObject](TermObject.md)

### Inherited from Association:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
