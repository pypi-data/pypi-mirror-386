
# Class: CellularAnatomicalEntityTermObject

A term object that represents a cellular anatomical entity term from GO

URI: [gocam:CellularAnatomicalEntityTermObject](https://w3id.org/gocam/CellularAnatomicalEntityTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CellularAnatomicalEntityAssociation]-%20term%200..1>[CellularAnatomicalEntityTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[CellularAnatomicalEntityTermObject],[CellularAnatomicalEntityAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CellularAnatomicalEntityAssociation]-%20term%200..1>[CellularAnatomicalEntityTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[CellularAnatomicalEntityTermObject],[CellularAnatomicalEntityAssociation])

## Identifier prefixes

 * GO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[CellularAnatomicalEntityAssociation](CellularAnatomicalEntityAssociation.md)** *[CellularAnatomicalEntityAssociation➞term](CellularAnatomicalEntityAssociation_term.md)*  <sub>0..1</sub>  **[CellularAnatomicalEntityTermObject](CellularAnatomicalEntityTermObject.md)**

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
