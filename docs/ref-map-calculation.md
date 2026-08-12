# Reference Map Coordinate Calculation

Reference objects use normalized coordinates so resizing the displayed image
does not change the stored location.

`map_x = (click_x - displayed_image_left) / displayed_image_width`

`map_y = (click_y - displayed_image_top) / displayed_image_height`

Both values are restricted to 0.0 through 1.0.

For a source image width W and height H:

`source_pixel_x = map_x * W`

`source_pixel_y = map_y * H`

The database can store NPCs, bosses, monsters/enemies, items, keys, drops,
vendors, doors, bonfires, routes, entrances, exits, and other encountered
objects. A record can explicitly say that an exact map location is not yet
known.

Only coordinate/object metadata is published. Third-party map image bytes stay
local and outside the character Git repository.

The public `ref-map-ai-exchange.json` file is an AI interchange surface.
External tooling can propose upsert/delete mutations. The simulator validates
the schedule, type, normalized coordinates, and rolling 10-per-hour mutation
limit before applying them to the local database.
