
# Class: QueryIndex

An index that is optionally placed on a model in order to support common query or index operations. Note that this index is not typically populated in the working transactional store for a model, it is derived via computation from core primary model information.

URI: [gocam:QueryIndex](https://w3id.org/gocam/QueryIndex)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[Activity]<singleton_activities%200..*-%20[QueryIndex&#124;taxon_label:string%20%3F;number_of_activities:integer%20%3F;number_of_enabled_by_terms:integer%20%3F;number_of_causal_associations:integer%20%3F;length_of_longest_causal_association_path:integer%20%3F;number_of_strongly_connected_components:integer%20%3F;number_of_start_activities:integer%20%3F;number_of_end_activities:integer%20%3F;number_of_intermediate_activities:integer%20%3F;number_of_singleton_activities:integer%20%3F],[Activity]<intermediate_activities%200..*-%20[QueryIndex],[Activity]<end_activities%200..*-%20[QueryIndex],[Activity]<start_activities%200..*-%20[QueryIndex],[TermObject]<annoton_terms%200..*-++[QueryIndex],[TermObject]<model_taxon_rollup%200..*-++[QueryIndex],[TermObject]<model_taxon_closure%200..*-++[QueryIndex],[TermObject]<model_taxon%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_closure%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_terms%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_closure%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_terms%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_closure%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_terms%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_closure%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_terms%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_closure%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_terms%200..*-++[QueryIndex],[PublicationObject]<flattened_references%200..*-++[QueryIndex],[Model]++-%20query_index%200..1>[QueryIndex],[PublicationObject],[Model],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[Activity]<singleton_activities%200..*-%20[QueryIndex&#124;taxon_label:string%20%3F;number_of_activities:integer%20%3F;number_of_enabled_by_terms:integer%20%3F;number_of_causal_associations:integer%20%3F;length_of_longest_causal_association_path:integer%20%3F;number_of_strongly_connected_components:integer%20%3F;number_of_start_activities:integer%20%3F;number_of_end_activities:integer%20%3F;number_of_intermediate_activities:integer%20%3F;number_of_singleton_activities:integer%20%3F],[Activity]<intermediate_activities%200..*-%20[QueryIndex],[Activity]<end_activities%200..*-%20[QueryIndex],[Activity]<start_activities%200..*-%20[QueryIndex],[TermObject]<annoton_terms%200..*-++[QueryIndex],[TermObject]<model_taxon_rollup%200..*-++[QueryIndex],[TermObject]<model_taxon_closure%200..*-++[QueryIndex],[TermObject]<model_taxon%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_closure%200..*-++[QueryIndex],[TermObject]<model_activity_has_input_terms%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_closure%200..*-++[QueryIndex],[TermObject]<model_activity_part_of_terms%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_closure%200..*-++[QueryIndex],[TermObject]<model_activity_enabled_by_terms%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_closure%200..*-++[QueryIndex],[TermObject]<model_activity_occurs_in_terms%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_rollup%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_closure%200..*-++[QueryIndex],[TermObject]<model_activity_molecular_function_terms%200..*-++[QueryIndex],[PublicationObject]<flattened_references%200..*-++[QueryIndex],[Model]++-%20query_index%200..1>[QueryIndex],[PublicationObject],[Model],[Activity])

## Referenced by Class

 *  **None** *[➞query_index](model__query_index.md)*  <sub>0..1</sub>  **[QueryIndex](QueryIndex.md)**

## Attributes


### Own

 * [➞taxon_label](queryIndex__taxon_label.md)  <sub>0..1</sub>
     * Description: The label of the primary taxon for the model
     * Range: [String](types/String.md)
 * [➞number_of_activities](queryIndex__number_of_activities.md)  <sub>0..1</sub>
     * Description: The number of activities in a model.
     * Range: [Integer](types/Integer.md)
 * [➞number_of_enabled_by_terms](queryIndex__number_of_enabled_by_terms.md)  <sub>0..1</sub>
     * Description: The number of molecular entities or sets of entities in a model.
     * Range: [Integer](types/Integer.md)
 * [➞number_of_causal_associations](queryIndex__number_of_causal_associations.md)  <sub>0..1</sub>
     * Description: Total number of causal association edges connecting activities in a model.
     * Range: [Integer](types/Integer.md)
 * [➞length_of_longest_causal_association_path](queryIndex__length_of_longest_causal_association_path.md)  <sub>0..1</sub>
     * Description: The maximum number of hops along activities along the direction of causal flow in a model.
     * Range: [Integer](types/Integer.md)
 * [➞number_of_strongly_connected_components](queryIndex__number_of_strongly_connected_components.md)  <sub>0..1</sub>
     * Description: The number of distinct components that consist of activities that are connected (directly or indirectly) via causal connections. Most models will consist of a single SCC. Some models may consist of two or more "islands" where there is no connection from one island to another.
     * Range: [Integer](types/Integer.md)
 * [➞flattened_references](queryIndex__flattened_references.md)  <sub>0..\*</sub>
     * Description: All publication objects from the model across different levels combined in one place
     * Range: [PublicationObject](PublicationObject.md)
 * [➞model_activity_molecular_function_terms](queryIndex__model_activity_molecular_function_terms.md)  <sub>0..\*</sub>
     * Description: All MF terms for all activities
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_molecular_function_closure](queryIndex__model_activity_molecular_function_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of `model_activity_molecular_function_terms`, over the is_a relationship
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_molecular_function_rollup](queryIndex__model_activity_molecular_function_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of `model_activity_molecular_function_closure` to a GO subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_occurs_in_terms](queryIndex__model_activity_occurs_in_terms.md)  <sub>0..\*</sub>
     * Description: All direct cellular component localization terms for all activities
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_occurs_in_closure](queryIndex__model_activity_occurs_in_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of `model_activity_occurs_in_terms`, over the is_a and part_of relationship type
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_occurs_in_rollup](queryIndex__model_activity_occurs_in_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of `model_activity_occurs_in_closure` to a GO subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_enabled_by_terms](queryIndex__model_activity_enabled_by_terms.md)  <sub>0..\*</sub>
     * Description: All direct enabler terms for all activities
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_enabled_by_closure](queryIndex__model_activity_enabled_by_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of `model_activity_enabled_by_terms`, over the is_a and has_part relationship type (e.g. complex to parts)
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_enabled_by_rollup](queryIndex__model_activity_enabled_by_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of `model_activity_enabled_by_closure` to a GO subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_part_of_terms](queryIndex__model_activity_part_of_terms.md)  <sub>0..\*</sub>
     * Description: All direct biological process terms for all activities
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_part_of_closure](queryIndex__model_activity_part_of_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of `model_activity_part_of_terms`, over the is_a and part_of relationship type
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_part_of_rollup](queryIndex__model_activity_part_of_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of `model_activity_part_of_closure` to a GO subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_has_input_terms](queryIndex__model_activity_has_input_terms.md)  <sub>0..\*</sub>
     * Description: All direct input terms for all activities
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_has_input_closure](queryIndex__model_activity_has_input_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of `model_activity_has_input_terms`, over the is_a relationship type
     * Range: [TermObject](TermObject.md)
 * [➞model_activity_has_input_rollup](queryIndex__model_activity_has_input_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of `model_activity_has_input_closure` to a GO subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞model_taxon](queryIndex__model_taxon.md)  <sub>0..\*</sub>
     * Description: The primary taxon term for the model, over the NCBITaxon:subClassOf relationship type. This is used to determine the primary taxon that the model is relevant to.
     * Range: [TermObject](TermObject.md)
 * [➞model_taxon_closure](queryIndex__model_taxon_closure.md)  <sub>0..\*</sub>
     * Description: The reflexive transitive closure of the taxon term for the model, over the NCBITaxon:subClassOf relationship type. This is used to determine the set of taxa that are relevant to the model.
     * Range: [TermObject](TermObject.md)
 * [➞model_taxon_rollup](queryIndex__model_taxon_rollup.md)  <sub>0..\*</sub>
     * Description: The rollup of the taxon closure to a NCBITaxon subset or slim.
     * Range: [TermObject](TermObject.md)
 * [➞annoton_terms](queryIndex__annoton_terms.md)  <sub>0..\*</sub>
     * Range: [TermObject](TermObject.md)
 * [➞start_activities](queryIndex__start_activities.md)  <sub>0..\*</sub>
     * Description: The set of activities that are the starting points of the model, i.e. those that have no incoming causal associations.
     * Range: [Activity](Activity.md)
 * [➞end_activities](queryIndex__end_activities.md)  <sub>0..\*</sub>
     * Description: The set of activities that are the end points of the model, i.e. those that have no outgoing causal associations.
     * Range: [Activity](Activity.md)
 * [➞intermediate_activities](queryIndex__intermediate_activities.md)  <sub>0..\*</sub>
     * Description: The set of activities that are neither start nor end activities, i.e. those that have both incoming and outgoing causal associations.
     * Range: [Activity](Activity.md)
 * [➞singleton_activities](queryIndex__singleton_activities.md)  <sub>0..\*</sub>
     * Description: The set of activities that have no causal associations, i.e. those that are not connected to any other activity in the model.
     * Range: [Activity](Activity.md)
 * [➞number_of_start_activities](queryIndex__number_of_start_activities.md)  <sub>0..1</sub>
     * Description: The number of start activities in a model
     * Range: [Integer](types/Integer.md)
 * [➞number_of_end_activities](queryIndex__number_of_end_activities.md)  <sub>0..1</sub>
     * Description: The number of end activities in a model
     * Range: [Integer](types/Integer.md)
 * [➞number_of_intermediate_activities](queryIndex__number_of_intermediate_activities.md)  <sub>0..1</sub>
     * Description: The number of intermediate activities in a model
     * Range: [Integer](types/Integer.md)
 * [➞number_of_singleton_activities](queryIndex__number_of_singleton_activities.md)  <sub>0..1</sub>
     * Description: The number of singleton activities in a model
     * Range: [Integer](types/Integer.md)
