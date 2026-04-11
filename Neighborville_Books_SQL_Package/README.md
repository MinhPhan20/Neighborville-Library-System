# Neighborville Books SQL Package

This package translates the uploaded **books spreadsheet** into SQL that your teammates can plug into the database and website layer quickly.

## What is included
- `neighborville_books_seed.sql`  
  Creates and seeds the book-related tables:
  - `PUBLISHER`
  - `AUTHOR`
  - `BOOK_TITLE`
  - `TITLE_AUTHOR`
  - `BOOK_CATALOG_VIEW` (flattened view for easy website queries)

- `covers/`  
  50 extracted cover image files from the spreadsheet.  
  Each image filename matches the `COVER_IMAGE_FILENAME` value in `BOOK_TITLE`.

## Why this structure
Your spreadsheet is **one row per book title**, so this SQL package seeds the title-side of the database, not circulation tables like `CHECKOUT`, `HOLD`, `FEE`, or physical-copy tables like `BOOK_COPY`.

That makes it a clean handoff for teammates:
- database teammate can connect this to the rest of the schema
- website teammate can query `BOOK_CATALOG_VIEW` immediately

## Table design summary

### PUBLISHER
Stores one row per publisher.

### AUTHOR
Stores one row per author.

### BOOK_TITLE
Stores the main book data from the spreadsheet:
- title
- genre
- publication year
- ISBN-13
- publisher
- shelf location
- status
- description
- source URL
- cover image filename

### TITLE_AUTHOR
Bridge table between titles and authors.

### BOOK_CATALOG_VIEW
Flattened join that is easiest for frontend usage.

## Fastest way for your teammates to use this

1. Run `neighborville_books_seed.sql`
2. Put the `covers/` folder into the website's static assets folder
3. Query:
   ```sql
   SELECT * FROM BOOK_CATALOG_VIEW ORDER BY TITLE_NAME;
   ```
4. Build image URLs in the frontend using `COVER_IMAGE_FILENAME`

Example:
- stored filename: `BK-0001.jpg`
- frontend path: `/covers/BK-0001.jpg`

## Suggested next step for the database teammate
If your team wants multiple physical copies of the same title later, connect this package to a `BOOK_COPY` table such as:

```sql
CREATE TABLE BOOK_COPY (
    COPY_ID INTEGER PRIMARY KEY,
    TITLE_ID INTEGER NOT NULL,
    BARCODE VARCHAR(50) NOT NULL UNIQUE,
    COPY_STATUS VARCHAR(50) NOT NULL,
    FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID)
);
```

## Suggested next step for the website teammate
Use `BOOK_CATALOG_VIEW` for:
- home catalog page
- search results
- book detail page
- filters by status / genre / author

## Counts in this package
- Books: 50
- Authors: 42
- Publishers: 26
- Cover images extracted: 50
