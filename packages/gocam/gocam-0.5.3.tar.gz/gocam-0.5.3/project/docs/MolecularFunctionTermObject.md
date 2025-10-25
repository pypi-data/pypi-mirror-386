
# Class: MolecularFunctionTermObject

A term object that represents a molecular function term from GO

URI: [gocam:MolecularFunctionTermObject](https://w3id.org/gocam/MolecularFunctionTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[MolecularFunctionAssociation]-%20term%200..1>[MolecularFunctionTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[MolecularFunctionTermObject],[MolecularFunctionAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[MolecularFunctionAssociation]-%20term%200..1>[MolecularFunctionTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[MolecularFunctionTermObject],[MolecularFunctionAssociation])

## Identifier prefixes

 * GO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[MolecularFunctionAssociation](MolecularFunctionAssociation.md)** *[MolecularFunctionAssociation➞term](MolecularFunctionAssociation_term.md)*  <sub>0..1</sub>  **[MolecularFunctionTermObject](MolecularFunctionTermObject.md)**

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
