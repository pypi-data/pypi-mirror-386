
# Class: BiologicalProcessTermObject

A term object that represents a biological process term from GO

URI: [gocam:BiologicalProcessTermObject](https://w3id.org/gocam/BiologicalProcessTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[BiologicalProcessAssociation]-%20term%200..1>[BiologicalProcessTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[BiologicalProcessTermObject],[BiologicalProcessAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[BiologicalProcessAssociation]-%20term%200..1>[BiologicalProcessTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[BiologicalProcessTermObject],[BiologicalProcessAssociation])

## Identifier prefixes

 * GO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[BiologicalProcessAssociation](BiologicalProcessAssociation.md)** *[BiologicalProcessAssociation➞term](BiologicalProcessAssociation_term.md)*  <sub>0..1</sub>  **[BiologicalProcessTermObject](BiologicalProcessTermObject.md)**

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
