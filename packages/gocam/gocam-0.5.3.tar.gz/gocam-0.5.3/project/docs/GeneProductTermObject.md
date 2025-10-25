
# Class: GeneProductTermObject

A term object that represents a gene product term from GO or UniProtKB

URI: [gocam:GeneProductTermObject](https://w3id.org/gocam/GeneProductTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[InformationBiomacromoleculeTermObject],[EnabledByGeneProductAssociation]-%20term%200..1>[GeneProductTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[EnabledByProteinComplexAssociation]-%20members%200..*>[GeneProductTermObject],[InformationBiomacromoleculeTermObject]^-[GeneProductTermObject],[EnabledByProteinComplexAssociation],[EnabledByGeneProductAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[InformationBiomacromoleculeTermObject],[EnabledByGeneProductAssociation]-%20term%200..1>[GeneProductTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[EnabledByProteinComplexAssociation]-%20members%200..*>[GeneProductTermObject],[InformationBiomacromoleculeTermObject]^-[GeneProductTermObject],[EnabledByProteinComplexAssociation],[EnabledByGeneProductAssociation])

## Parents

 *  is_a: [InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md) - An abstract class for all information biomacromolecule term objects

## Referenced by Class

 *  **[EnabledByGeneProductAssociation](EnabledByGeneProductAssociation.md)** *[EnabledByGeneProductAssociation➞term](EnabledByGeneProductAssociation_term.md)*  <sub>0..1</sub>  **[GeneProductTermObject](GeneProductTermObject.md)**
 *  **None** *[➞members](enabledByProteinComplexAssociation__members.md)*  <sub>0..\*</sub>  **[GeneProductTermObject](GeneProductTermObject.md)**

## Attributes


### Inherited from InformationBiomacromoleculeTermObject:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
