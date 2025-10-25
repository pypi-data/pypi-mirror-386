
# Class: MoleculeTermObject

A term object that represents a molecule term from CHEBI or UniProtKB

URI: [gocam:MoleculeTermObject](https://w3id.org/gocam/MoleculeTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[MoleculeAssociation]-%20term%200..1>[MoleculeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[MoleculeTermObject],[MoleculeAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[MoleculeAssociation]-%20term%200..1>[MoleculeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[MoleculeTermObject],[MoleculeAssociation])

## Identifier prefixes

 * CHEBI
 * UniProtKB

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[MoleculeAssociation](MoleculeAssociation.md)** *[MoleculeAssociation➞term](MoleculeAssociation_term.md)*  <sub>0..1</sub>  **[MoleculeTermObject](MoleculeTermObject.md)**

## Attributes


### Inherited from TermObject:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
