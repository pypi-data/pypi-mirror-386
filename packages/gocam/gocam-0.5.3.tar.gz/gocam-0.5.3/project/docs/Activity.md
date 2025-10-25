
# Class: Activity

An individual activity in a causal model, representing the individual molecular activity of a single gene product or complex in the context of a particular model

URI: [gocam:Activity](https://w3id.org/gocam/Activity)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[MoleculeAssociation],[MolecularFunctionAssociation],[EnabledByAssociation],[CellularAnatomicalEntityAssociation],[CausalAssociation],[BiologicalProcessAssociation],[ProvenanceInfo]<provenances%200..*-++[Activity&#124;id:uriorcurie],[CausalAssociation]<causal_associations%200..*-++[Activity],[MoleculeAssociation]<has_primary_output%200..1-++[Activity],[MoleculeAssociation]<has_output%200..*-++[Activity],[MoleculeAssociation]<has_primary_input%200..1-++[Activity],[MoleculeAssociation]<has_input%200..*-++[Activity],[BiologicalProcessAssociation]<part_of%200..1-++[Activity],[CellularAnatomicalEntityAssociation]<occurs_in%200..1-++[Activity],[MolecularFunctionAssociation]<molecular_function%200..1-++[Activity],[EnabledByAssociation]<enabled_by%200..1-++[Activity],[CausalAssociation]-%20downstream_activity%200..1>[Activity],[Model]++-%20activities%200..*>[Activity],[QueryIndex]-%20end_activities%200..*>[Activity],[QueryIndex]-%20intermediate_activities%200..*>[Activity],[QueryIndex]-%20singleton_activities%200..*>[Activity],[QueryIndex]-%20start_activities%200..*>[Activity],[QueryIndex],[Model])](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[MoleculeAssociation],[MolecularFunctionAssociation],[EnabledByAssociation],[CellularAnatomicalEntityAssociation],[CausalAssociation],[BiologicalProcessAssociation],[ProvenanceInfo]<provenances%200..*-++[Activity&#124;id:uriorcurie],[CausalAssociation]<causal_associations%200..*-++[Activity],[MoleculeAssociation]<has_primary_output%200..1-++[Activity],[MoleculeAssociation]<has_output%200..*-++[Activity],[MoleculeAssociation]<has_primary_input%200..1-++[Activity],[MoleculeAssociation]<has_input%200..*-++[Activity],[BiologicalProcessAssociation]<part_of%200..1-++[Activity],[CellularAnatomicalEntityAssociation]<occurs_in%200..1-++[Activity],[MolecularFunctionAssociation]<molecular_function%200..1-++[Activity],[EnabledByAssociation]<enabled_by%200..1-++[Activity],[CausalAssociation]-%20downstream_activity%200..1>[Activity],[Model]++-%20activities%200..*>[Activity],[QueryIndex]-%20end_activities%200..*>[Activity],[QueryIndex]-%20intermediate_activities%200..*>[Activity],[QueryIndex]-%20singleton_activities%200..*>[Activity],[QueryIndex]-%20start_activities%200..*>[Activity],[QueryIndex],[Model])

## Referenced by Class

 *  **None** *[➞downstream_activity](causalAssociation__downstream_activity.md)*  <sub>0..1</sub>  **[Activity](Activity.md)**
 *  **None** *[➞activities](model__activities.md)*  <sub>0..\*</sub>  **[Activity](Activity.md)**
 *  **None** *[➞end_activities](queryIndex__end_activities.md)*  <sub>0..\*</sub>  **[Activity](Activity.md)**
 *  **None** *[➞intermediate_activities](queryIndex__intermediate_activities.md)*  <sub>0..\*</sub>  **[Activity](Activity.md)**
 *  **None** *[➞singleton_activities](queryIndex__singleton_activities.md)*  <sub>0..\*</sub>  **[Activity](Activity.md)**
 *  **None** *[➞start_activities](queryIndex__start_activities.md)*  <sub>0..\*</sub>  **[Activity](Activity.md)**

## Attributes


### Own

 * [➞id](activity__id.md)  <sub>1..1</sub>
     * Description: Identifier of the activity unit. Should be in gocam namespace.
     * Range: [Uriorcurie](types/Uriorcurie.md)
     * Example: gomodel:63f809ec00000701 A model representing tRNA repair and recycling
 * [➞enabled_by](activity__enabled_by.md)  <sub>0..1</sub>
     * Description: The gene product or complex that carries out the activity
     * Range: [EnabledByAssociation](EnabledByAssociation.md)
 * [➞molecular_function](activity__molecular_function.md)  <sub>0..1</sub>
     * Description: The molecular function that is carried out by the gene product or complex
     * Range: [MolecularFunctionAssociation](MolecularFunctionAssociation.md)
 * [➞occurs_in](activity__occurs_in.md)  <sub>0..1</sub>
     * Description: The cellular location in which the activity occurs
     * Range: [CellularAnatomicalEntityAssociation](CellularAnatomicalEntityAssociation.md)
 * [➞part_of](activity__part_of.md)  <sub>0..1</sub>
     * Description: The larger biological process in which the activity is a part
     * Range: [BiologicalProcessAssociation](BiologicalProcessAssociation.md)
 * [➞has_input](activity__has_input.md)  <sub>0..\*</sub>
     * Description: The input molecules that are directly consumed by the activity
     * Range: [MoleculeAssociation](MoleculeAssociation.md)
 * [➞has_primary_input](activity__has_primary_input.md)  <sub>0..1</sub>
     * Description: The primary input molecule that is directly consumed by the activity
     * Range: [MoleculeAssociation](MoleculeAssociation.md)
 * [➞has_output](activity__has_output.md)  <sub>0..\*</sub>
     * Description: The output molecules that are directly produced by the activity
     * Range: [MoleculeAssociation](MoleculeAssociation.md)
 * [➞has_primary_output](activity__has_primary_output.md)  <sub>0..1</sub>
     * Description: The primary output molecule that is directly produced by the activity
     * Range: [MoleculeAssociation](MoleculeAssociation.md)
 * [➞causal_associations](activity__causal_associations.md)  <sub>0..\*</sub>
     * Description: The causal associations that flow out of this activity
     * Range: [CausalAssociation](CausalAssociation.md)
 * [➞provenances](activity__provenances.md)  <sub>0..\*</sub>
     * Description: Provenance information for the activity
     * Range: [ProvenanceInfo](ProvenanceInfo.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Aliases:** | | annoton |
