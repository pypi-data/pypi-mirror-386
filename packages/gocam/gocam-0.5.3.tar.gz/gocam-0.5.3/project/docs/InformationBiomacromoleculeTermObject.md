
# Class: InformationBiomacromoleculeTermObject

An abstract class for all information biomacromolecule term objects

URI: [gocam:InformationBiomacromoleculeTermObject](https://w3id.org/gocam/InformationBiomacromoleculeTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[ProteinComplexTermObject],[EnabledByAssociation]-%20term%200..1>[InformationBiomacromoleculeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[InformationBiomacromoleculeTermObject]^-[ProteinComplexTermObject],[InformationBiomacromoleculeTermObject]^-[GeneProductTermObject],[TermObject]^-[InformationBiomacromoleculeTermObject],[GeneProductTermObject],[EnabledByAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[ProteinComplexTermObject],[EnabledByAssociation]-%20term%200..1>[InformationBiomacromoleculeTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[InformationBiomacromoleculeTermObject]^-[ProteinComplexTermObject],[InformationBiomacromoleculeTermObject]^-[GeneProductTermObject],[TermObject]^-[InformationBiomacromoleculeTermObject],[GeneProductTermObject],[EnabledByAssociation])

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Children

 * [GeneProductTermObject](GeneProductTermObject.md) - A term object that represents a gene product term from GO or UniProtKB
 * [ProteinComplexTermObject](ProteinComplexTermObject.md) - A term object that represents a protein complex term from GO

## Referenced by Class

 *  **None** *[➞term](enabledByAssociation__term.md)*  <sub>0..1</sub>  **[InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md)**

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
