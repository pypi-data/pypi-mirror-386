
# Class: CellTypeTermObject

A term object that represents a cell type term from CL

URI: [gocam:CellTypeTermObject](https://w3id.org/gocam/CellTypeTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CellTypeAssociation]-%20term%200..1>[CellTypeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[CellTypeTermObject],[CellTypeAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CellTypeAssociation]-%20term%200..1>[CellTypeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[CellTypeTermObject],[CellTypeAssociation])

## Identifier prefixes

 * CL
 * PO
 * FAO
 * DDANAT

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[CellTypeAssociation](CellTypeAssociation.md)** *[CellTypeAssociation➞term](CellTypeAssociation_term.md)*  <sub>0..1</sub>  **[CellTypeTermObject](CellTypeTermObject.md)**

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
