
# Class: EvidenceTermObject

A term object that represents an evidence term from ECO. Only ECO terms that map up to a GO GAF evidence code should be used.

URI: [gocam:EvidenceTermObject](https://w3id.org/gocam/EvidenceTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[EvidenceItem]-%20term%200..1>[EvidenceTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[EvidenceTermObject],[EvidenceItem])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[EvidenceItem]-%20term%200..1>[EvidenceTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[EvidenceTermObject],[EvidenceItem])

## Identifier prefixes

 * ECO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **None** *[➞term](evidenceItem__term.md)*  <sub>0..1</sub>  **[EvidenceTermObject](EvidenceTermObject.md)**

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
