
# Class: PhaseTermObject

A term object that represents a phase term from GO or UBERON

URI: [gocam:PhaseTermObject](https://w3id.org/gocam/PhaseTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[BiologicalProcessAssociation]-%20happens_during%200..1>[PhaseTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[PhaseTermObject],[BiologicalProcessAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[BiologicalProcessAssociation]-%20happens_during%200..1>[PhaseTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[PhaseTermObject],[BiologicalProcessAssociation])

## Identifier prefixes

 * GO
 * UBERON
 * PO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **None** *[➞happens_during](biologicalProcessAssociation__happens_during.md)*  <sub>0..1</sub>  **[PhaseTermObject](PhaseTermObject.md)**

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
