### Return values (updated May 2025)

Services **must** return:
* `<Model>Read` SQLModel DTOs for data
* Primitive IDs when only an identifier is required

They **must not** return:
* Session-bound SQLModel table instances
* Raw `dict` payloads
