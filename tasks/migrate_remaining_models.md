# Migrate remaining models to Read DTO pattern

- [ ] Run `scripts/split_models.py` to generate Base/Read classes for all table models.
- [ ] Move field definitions from table classes into their corresponding `*Base` classes.
- [ ] Add `FromModel` mixin to each `<Model>Read` class.
- [ ] Update services to return `<Model>Read` DTOs instead of raw dicts.
- [ ] Adjust tests to consume DTOs via attribute access.
