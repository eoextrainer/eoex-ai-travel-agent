# Project Architecture

## C4 Model (Text Summary)
- Context: EOEX AI Travel Agent interacts with Amadeus API, MySQL DB, and end users via web UI.
- Containers: FastAPI backend, static frontend, MySQL database.
- Components: User service, Journey service, Amadeus client, Admin service.

## UML Data Model (Summary)
- `users(id, first_name, surname, dob, location, budget, preferences, companions, special_needs, username, role)`
- `journeys(id, user_id, destination_country, destination_city, budget, created_at)`
- `flights/accommodations/transportation/food_choices/shopping_choices/places_to_visit` linked to `journeys`.

## Sequence Diagram (Narrative)
1. User submits search form.
2. Backend validates criteria and calls Amadeus flight offers.
3. Results returned and displayed; DB can be seeded for caching.
4. Admin can query journeys with filters.

## State Diagram (Narrative)
- States: Idle -> Searching -> Results -> Selected -> Booked (future).

## Design Patterns
- Python: Repository/service layers, env-config, logging.
- JavaScript: Fetch API, simple state management via DOM updates.
