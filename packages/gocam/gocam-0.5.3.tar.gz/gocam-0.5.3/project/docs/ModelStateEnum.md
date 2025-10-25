
# Enum: ModelStateEnum

A term describing where the model is in the development life cycle.

URI: [gocam:ModelStateEnum](https://w3id.org/gocam/ModelStateEnum)


## Permissible Values

| Text | Description | Meaning | Other Information |
| :--- | :---: | :---: | ---: |
| development | Used when the curator is still working on the model. Edits are still being made, and the information in the model is not yet guaranteed to be accurate or complete. The model should not be displayed in end-user facing websites, unless it is made clear that the model is a work in progress. |  | {'aliases': ['work in progress']} |
| production | Used when the curator has declared the model is ready for public consumption. Edits might still be performed on the model in future, but the information in the model is believed to be both accurate and reasonably complete. The model may be displayed in public websites. |  |  |
| delete | When the curator has marked for future deletion. |  |  |
| review | The model has been marked for curator review. |  |  |
| internal_test | The model is not intended for use public use; it is likely to be used for internal testing. |  |  |
| closed | TBD |  |  |
