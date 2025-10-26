# County Data API (HW4 Part 2)

## Endpoints

- **POST** `/api/county_data` (mirror: `/county_data`)
  - Body (JSON): `{ "zip": "02138", "measure_name": "Adult obesity" }`
  - Special: `coffee=teapot` in body or as query returns **418**
  - Errors: GET → **400**; missing fields → **400**; no results/unknown measure → **404**

- **GET/POST** `/api/obesity`, `/api/poverty`, `/api/fpm` (aliases without `/api`) and the paths `/@../obesity.json`, `/@../poverty.json`, `/@../fpm.json`
  - Always return a **JSON array**. Not found → **404**.

## Notes
- Uses parameterized SQL.
- Ensure `data.db`, `obesity.json`, `poverty.json`, `fpm.json` are in repo root.
- `link.txt` must contain exactly your county_data URL with no trailing newline/space.
