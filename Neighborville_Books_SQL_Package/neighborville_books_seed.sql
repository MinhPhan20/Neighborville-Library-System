-- Neighborville Public Library
-- Books catalog seed script generated from the spreadsheet provided by Mohammed Tanvvir
-- This script is intentionally kept portable for MySQL / PostgreSQL / SQLite style workflows.
-- It creates the book-related tables only: PUBLISHER, AUTHOR, BOOK_TITLE, TITLE_AUTHOR, plus a frontend-friendly view.

DROP VIEW IF EXISTS BOOK_CATALOG_VIEW;
DROP TABLE IF EXISTS TITLE_AUTHOR;
DROP TABLE IF EXISTS BOOK_TITLE;
DROP TABLE IF EXISTS AUTHOR;
DROP TABLE IF EXISTS PUBLISHER;

CREATE TABLE PUBLISHER (
    PUBLISHER_ID INTEGER PRIMARY KEY,
    PUBLISHER_NAME VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE AUTHOR (
    AUTHOR_ID INTEGER PRIMARY KEY,
    AUTHOR_NAME VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE BOOK_TITLE (
    TITLE_ID INTEGER PRIMARY KEY,
    BOOK_CODE VARCHAR(20) NOT NULL UNIQUE,
    TITLE_NAME VARCHAR(255) NOT NULL,
    GENRE VARCHAR(100),
    PUBLICATION_YEAR INTEGER,
    ISBN13 VARCHAR(20) NOT NULL UNIQUE,
    PUBLISHER_ID INTEGER NOT NULL,
    SHELF_LOCATION VARCHAR(50),
    STATUS VARCHAR(50),
    DESCRIPTION TEXT,
    SOURCE_URL TEXT,
    COVER_IMAGE_FILENAME VARCHAR(255),
    FOREIGN KEY (PUBLISHER_ID) REFERENCES PUBLISHER(PUBLISHER_ID)
);

CREATE TABLE TITLE_AUTHOR (
    TITLE_ID INTEGER NOT NULL,
    AUTHOR_ID INTEGER NOT NULL,
    TITLE_AUTHOR_ROLE VARCHAR(50) DEFAULT 'Author',
    PRIMARY KEY (TITLE_ID, AUTHOR_ID),
    FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID),
    FOREIGN KEY (AUTHOR_ID) REFERENCES AUTHOR(AUTHOR_ID)
);

-- Helpful indexes for search and website queries
CREATE INDEX IDX_BOOK_TITLE_NAME ON BOOK_TITLE (TITLE_NAME);
CREATE INDEX IDX_BOOK_GENRE ON BOOK_TITLE (GENRE);
CREATE INDEX IDX_BOOK_STATUS ON BOOK_TITLE (STATUS);
CREATE INDEX IDX_BOOK_SHELF_LOCATION ON BOOK_TITLE (SHELF_LOCATION);

-- Publishers
INSERT INTO PUBLISHER (PUBLISHER_ID, PUBLISHER_NAME) VALUES
    (1, 'Harper Perennial Modern Classics'),
    (2, 'Signet'),
    (3, 'Penguin Classics'),
    (4, 'Scribner'),
    (5, 'Little, Brown and Company'),
    (6, 'HarperCollins'),
    (7, 'Simon & Schuster'),
    (8, 'Mariner Books'),
    (9, 'Harper Perennial'),
    (10, 'Riverhead Books'),
    (11, 'Knopf Books for Young Readers'),
    (12, 'Clarion Books'),
    (13, 'Ace'),
    (14, 'Scholastic Press'),
    (15, 'Penguin Books'),
    (16, 'Puffin Books'),
    (17, 'Ecco'),
    (18, 'Square Fish'),
    (19, 'Scholastic'),
    (20, 'Scholastic Paperbacks'),
    (21, 'Disney Hyperion'),
    (22, 'Delacorte Press'),
    (23, 'Viking Books for Young Readers'),
    (24, 'Ballantine Books'),
    (25, 'Anchor Books'),
    (26, 'Vintage Crime/Black Lizard');

-- Authors
INSERT INTO AUTHOR (AUTHOR_ID, AUTHOR_NAME) VALUES
    (1, 'Harper Lee'),
    (2, 'George Orwell'),
    (3, 'Jane Austen'),
    (4, 'F. Scott Fitzgerald'),
    (5, 'Herman Melville'),
    (6, 'Charlotte Brontë'),
    (7, 'J.D. Salinger'),
    (8, 'J.R.R. Tolkien'),
    (9, 'Ray Bradbury'),
    (10, 'Aldous Huxley'),
    (11, 'C.S. Lewis'),
    (12, 'Paulo Coelho'),
    (13, 'Khaled Hosseini'),
    (14, 'Markus Zusak'),
    (15, 'Lois Lowry'),
    (16, 'Frank Herbert'),
    (17, 'Suzanne Collins'),
    (18, 'John Green'),
    (19, 'Louisa May Alcott'),
    (20, 'Emily Brontë'),
    (21, 'Mary Shelley'),
    (22, 'Bram Stoker'),
    (23, 'Oscar Wilde'),
    (24, 'Homer'),
    (25, 'Alexandre Dumas'),
    (26, 'Victor Hugo'),
    (27, 'Miguel de Cervantes'),
    (28, 'Charles Dickens'),
    (29, 'Mark Twain'),
    (30, 'John Steinbeck'),
    (31, 'Ernest Hemingway'),
    (32, 'Madeleine L''Engle'),
    (33, 'E.B. White'),
    (34, 'Frances Hodgson Burnett'),
    (35, 'J.K. Rowling'),
    (36, 'Rick Riordan'),
    (37, 'James Dashner'),
    (38, 'S.E. Hinton'),
    (39, 'Yann Martel'),
    (40, 'Andy Weir'),
    (41, 'Dan Brown'),
    (42, 'Stieg Larsson');

-- Books / titles
INSERT INTO BOOK_TITLE (TITLE_ID, BOOK_CODE, TITLE_NAME, GENRE, PUBLICATION_YEAR, ISBN13, PUBLISHER_ID, SHELF_LOCATION, STATUS, DESCRIPTION, SOURCE_URL, COVER_IMAGE_FILENAME) VALUES
    (1, 'BK-0001', 'To Kill a Mockingbird', 'Fiction', 1960, '9780141036144', 1, 'J FIC LEE', 'Available', 'Scout Finch grows up in a small Alabama town where her father, Atticus, defends a Black man falsely accused of a terrible crime. The novel blends childhood wonder with a sharp look at prejudice, justice, and moral courage.', 'https://www.harpercollins.com/products/to-kill-a-mockingbird-harper-lee', 'BK-0001.jpg'),
    (2, 'BK-0002', '1984', 'Dystopian', 1949, '9780451524935', 2, 'J FIC ORW', 'Available', 'Winston Smith lives under a regime that rewrites truth, watches everyone, and crushes independent thought. Orwell turns political fear into a gripping story about freedom, language, and control.', 'https://www.penguinrandomhouse.com/books/326569/1984-by-george-orwell/', 'BK-0002.jpg'),
    (3, 'BK-0003', 'Pride and Prejudice', 'Romance', 1813, '9780141439518', 3, 'J FIC AUS', 'Checked Out', 'Elizabeth Bennet and Mr. Darcy clash, misjudge one another, and slowly change through a series of social encounters and family pressures. It is both a love story and a witty critique of class, pride, and first impressions.', 'https://www.penguin.co.uk/books/55905/pride-and-prejudice-by-austen-jane/9780141439518', 'BK-0003.jpg'),
    (4, 'BK-0004', 'The Great Gatsby', 'Classic', 1925, '9780743273565', 4, 'J FIC FIT', 'Available', 'Nick Carraway is drawn into the glittering world of Jay Gatsby, a mysterious millionaire chasing an impossible dream. The story exposes the beauty and emptiness of wealth, obsession, and the American Dream.', 'https://www.amazon.com/Great-Gatsby-F-Scott-Fitzgerald/dp/0743273567', 'BK-0004.jpg'),
    (5, 'BK-0005', 'Moby-Dick', 'Adventure', 1851, '9780142437247', 3, 'J FIC MEL', 'Available', 'Captain Ahab leads the Pequod on a relentless hunt for the white whale that took his leg. Melville mixes adventure, philosophy, and obsession into a sweeping tale of man versus nature.', 'https://www.penguinrandomhousehighereducation.com/book/?isbn=9780142437247', 'BK-0005.jpg'),
    (6, 'BK-0006', 'Jane Eyre', 'Classic', 1847, '9780141441146', 3, 'J FIC BRO', 'On Hold', 'Orphaned Jane Eyre searches for dignity, independence, and love in a world that constantly tries to limit her. Her bond with Mr. Rochester gives the novel both emotional intensity and Gothic tension.', 'https://www.penguin.co.uk/books/60371/jane-eyre-by-charlotte-bronte-ed-dr-stevie-davies/9780141441146', 'BK-0006.jpg'),
    (7, 'BK-0007', 'The Catcher in the Rye', 'Coming-of-Age', 1951, '9780316769488', 5, 'J FIC SAL', 'Available', 'Holden Caulfield wanders New York after leaving school, mocking the phoniness he sees around him while struggling with grief and alienation. The novel captures teenage confusion with a voice that still feels immediate.', 'https://www.littlebrown.com/titles/j-d-salinger/the-catcher-in-the-rye/9780316769488/', 'BK-0007.jpg'),
    (8, 'BK-0008', 'The Hobbit', 'Fantasy', 1937, '9780547928227', 6, 'J FIC TOL', 'Checked Out', 'Bilbo Baggins is pulled out of his quiet life and sent on a dangerous journey involving dwarves, trolls, elves, and a dragon. It is a classic adventure about courage, luck, and discovering strength you did not know you had.', 'https://www.harpercollins.com/products/the-hobbit-jrr-tolkien', 'BK-0008.jpg'),
    (9, 'BK-0009', 'Fahrenheit 451', 'Science Fiction', 1953, '9781451673319', 7, 'J FIC BRA', 'Available', 'In a future where books are outlawed and burned, fireman Guy Montag begins to question the society he serves. The story warns about censorship, passive entertainment, and the loss of thought.', 'https://www.barnesandnoble.com/w/fahrenheit-451-ray-bradbury/1100383286', 'BK-0009.jpg'),
    (10, 'BK-0010', 'The Lord of the Rings', 'Fantasy', 1954, '9780618640157', 8, 'J FIC TOL', 'Available', 'Frodo Baggins carries the One Ring across Middle-earth while war spreads and temptation grows stronger. This epic fantasy combines friendship, sacrifice, myth, and a vast sense of history.', 'https://www.amazon.com/Lord-Rings-50th-Anniversary-Vol/dp/0618640150', 'BK-0010.jpg'),
    (11, 'BK-0011', 'Animal Farm', 'Satire', 1945, '9780451526342', 2, 'J FIC ORW', 'Available', 'Farm animals overthrow their human owner hoping to build a fairer society, only to watch a new tyranny rise from within. Orwell uses a simple fable to reveal how revolutions can be corrupted by power.', 'https://www.penguinrandomhousesecondaryeducation.com/book/?isbn=9780451526342', 'BK-0011.jpg'),
    (12, 'BK-0012', 'Brave New World', 'Dystopian', 1932, '9780060850524', 9, 'J FIC HUX', 'Available', 'Huxley imagines a future built on pleasure, conditioning, and artificial stability instead of freedom or depth. The novel is chilling because its world feels seductive as well as disturbing.', 'https://www.harpercollins.com/products/brave-new-world-aldous-huxley', 'BK-0012.jpg'),
    (13, 'BK-0013', 'The Chronicles of Narnia', 'Fantasy', 1956, '9780066238500', 6, 'J FIC LEW', 'Available', 'This collected volume brings together all seven Narnia stories, from first discoveries to final battles. It offers mythic fantasy, moral struggle, and a world where wonder and danger always travel together.', 'https://www.harpercollins.com/products/the-chronicles-of-narnia-c-s-lewis', 'BK-0013.jpg'),
    (14, 'BK-0014', 'The Alchemist', 'Adventure', 1988, '9780061122415', 6, 'J FIC COE', 'Checked Out', 'A young shepherd named Santiago follows recurring dreams in search of treasure and personal destiny. The book reads like a fable about faith, risk, and listening to the deeper call in your life.', 'https://www.abebooks.com/9780061122415/Alchemist-Paulo-Coelho-0061122416/plp', 'BK-0014.jpg'),
    (15, 'BK-0015', 'The Kite Runner', 'Drama', 2003, '9781594631931', 10, 'J FIC HOS', 'Available', 'Amir looks back on his childhood in Afghanistan and the betrayal that shaped the rest of his life. It is a deeply emotional novel about guilt, class, friendship, and the possibility of redemption.', 'https://www.penguinrandomhouse.com/books/83013/the-kite-runner-by-khaled-hosseini/', 'BK-0015.jpg'),
    (16, 'BK-0016', 'The Book Thief', 'Historical Fiction', 2005, '9780375842207', 11, 'J FIC ZUS', 'Available', 'Narrated by Death, the novel follows Liesel as she steals books and learns the power of words in Nazi Germany. It is heartbreaking, humane, and deeply interested in how stories help people endure.', 'https://www.amazon.com/Book-Thief-Markus-Zusak/dp/0375842209', 'BK-0016.jpg'),
    (17, 'BK-0017', 'The Giver', 'Young Adult', 1993, '9780544336261', 12, 'J FIC LOW', 'Available', 'Jonas lives in a carefully controlled community that seems peaceful until he begins receiving memories of the real world. The novel asks what is lost when comfort replaces freedom, feeling, and choice.', 'https://www.harpercollins.com/products/the-giver-lois-lowry', 'BK-0017.jpg'),
    (18, 'BK-0018', 'Dune', 'Science Fiction', 1965, '9780441172719', 13, 'J FIC HER', 'On Hold', 'Paul Atreides is swept into a brutal struggle over Arrakis, the desert world that controls the universe’s most valuable resource. Dune blends politics, religion, ecology, and destiny on an epic scale.', 'https://www.amazon.com/Dune-Frank-Herbert/dp/0441172717', 'BK-0018.jpg'),
    (19, 'BK-0019', 'The Hunger Games', 'Young Adult', 2008, '9780439023481', 14, 'J FIC COL', 'Checked Out', 'Katniss Everdeen volunteers to enter a televised fight to the death designed to keep the districts under control. The book is fast, tense, and sharply critical of spectacle, inequality, and power.', 'https://www.amazon.com/Hunger-Games-Book/dp/0439023483', 'BK-0019.jpg'),
    (20, 'BK-0020', 'The Fault in Our Stars', 'Young Adult', 2012, '9780142424179', 15, 'J FIC GRE', 'Available', 'Hazel and Augustus fall in love while living under the shadow of serious illness. John Green balances humor, romance, and grief without pretending that life becomes simple because people care for each other.', 'https://www.penguinrandomhouse.com/books/299004/the-fault-in-our-stars-by-john-green/', 'BK-0020.jpg'),
    (21, 'BK-0021', 'Little Women', 'Classic', 1868, '9780147514011', 16, 'J FIC ALC', 'Available', 'The four March sisters grow up during the Civil War era, each with different dreams and flaws. The novel turns ordinary family life into something warm, memorable, and emotionally rich.', 'https://www.penguinrandomhouse.com/books/316851/little-women-by-louisa-may-alcott-illustrated-by-anna-bond/', 'BK-0021.jpg'),
    (22, 'BK-0022', 'Wuthering Heights', 'Classic', 1847, '9780141439556', 3, 'J FIC BRO', 'Available', 'On the Yorkshire moors, the bond between Catherine and Heathcliff becomes fierce, destructive, and unforgettable. The novel is dark, stormy, and obsessed with love that refuses to stay within social boundaries.', 'https://penguinrandomhousehighereducation.com/book/?isbn=9780141439556', 'BK-0022.jpg'),
    (23, 'BK-0023', 'Frankenstein', 'Gothic', 1818, '9780141439471', 3, 'J FIC SHE', 'Checked Out', 'Victor Frankenstein creates life and then recoils from what he has made, setting off tragedy for everyone around him. Shelley combines Gothic suspense with questions about ambition, responsibility, and isolation.', 'https://www.penguin.co.uk/books/55587/frankenstein-by-mary-shelley-ed-maurice-hindle/9780141439471', 'BK-0023.jpg'),
    (24, 'BK-0024', 'Dracula', 'Horror', 1897, '9780141439846', 3, 'J FIC STO', 'Available', 'Jonathan Harker’s trip to Transylvania opens the door to one of literature’s most famous monsters. Dracula mixes dread, pursuit, and folklore into a foundational Gothic horror novel.', 'https://citylights.com/featured-titles/dracula-5/', 'BK-0024.jpg'),
    (25, 'BK-0025', 'The Picture of Dorian Gray', 'Classic', 1890, '9780141439570', 3, 'J FIC WIL', 'Available', 'Dorian Gray remains young and beautiful while a portrait records the corruption of his soul. Wilde turns vanity and pleasure into a stylish, unsettling meditation on art, morality, and self-destruction.', 'https://penguinrandomhouselibrary.com/book/?isbn=9780141439570', 'BK-0025.jpg'),
    (26, 'BK-0026', 'The Odyssey', 'Epic', -700, '9780140268867', 3, 'J FIC HOM', 'Available', 'Odysseus struggles to return home after the Trojan War, facing monsters, temptations, and the wrath of the gods. The poem is both a thrilling journey and a meditation on identity, loyalty, and endurance.', 'https://www.penguinrandomhouseretail.com/book/?isbn=9780140268867', 'BK-0026.jpg'),
    (27, 'BK-0027', 'The Iliad', 'Epic', -750, '9780140275360', 3, 'J FIC HOM', 'Available', 'The Iliad focuses on a brief but explosive stretch of the Trojan War, especially the rage of Achilles. It turns battlefield conflict into a profound study of honor, mortality, pride, and grief.', 'https://www.penguinrandomhouse.com/books/322812/the-iliad-by-homer-translated-by-robert-fagles-introduction-and-notes-by-bernard-knox/', 'BK-0027.jpg'),
    (28, 'BK-0028', 'The Count of Monte Cristo', 'Adventure', 1844, '9780140449266', 3, 'J FIC DUM', 'Checked Out', 'Edmond Dantes is betrayed, imprisoned, and reborn with a new identity and a plan for revenge. The novel is huge, dramatic, and immensely satisfying, with both adventure and emotional payoff.', 'https://www.penguinrandomhousehighereducation.com/book/?isbn=9780140449266', 'BK-0028.jpg'),
    (29, 'BK-0029', 'Les Misérables', 'Historical Fiction', 1862, '9780451419439', 2, 'J FIC HUG', 'Available', 'Jean Valjean tries to build an honorable life while the law, poverty, and history keep dragging him backward. Hugo mixes intimate human suffering with revolution, justice, mercy, and hope.', 'https://www.penguinrandomhouse.com/books/313987/les-miserables-by-victor-hugo/', 'BK-0029.jpg'),
    (30, 'BK-0030', 'Don Quixote', 'Classic', 1605, '9780060934347', 17, 'J FIC CER', 'Available', 'An aging nobleman becomes obsessed with knightly adventure and rides out to remake the world according to old ideals. The book is funny, sad, and strangely modern in the way it blurs illusion and reality.', 'https://www.harpercollins.com/products/don-quixote-miguel-de-cervantesedith-grossman', 'BK-0030.jpg'),
    (31, 'BK-0031', 'A Tale of Two Cities', 'Historical Fiction', 1859, '9780141439600', 3, 'J FIC DIC', 'Available', 'Set in London and Paris during the French Revolution, the novel ties personal sacrifice to violent historical upheaval. Dickens gives it urgency, atmosphere, and one of literature’s most famous endings.', 'https://penguinrandomhousehighereducation.com/book/?isbn=9780141439600', 'BK-0031.jpg'),
    (32, 'BK-0032', 'Great Expectations', 'Classic', 1861, '9780141439563', 3, 'J FIC DIC', 'On Hold', 'Pip rises from humble beginnings into the world of wealth and gentility, only to learn how costly his illusions have been. It is a coming-of-age story about ambition, shame, love, and self-knowledge.', 'https://www.penguin.co.uk/books/60338/great-expectations-by-charles-dickens-ed-charlotte-mitchell-intro-david-trotter/9780141439563', 'BK-0032.jpg'),
    (33, 'BK-0033', 'The Adventures of Huckleberry Finn', 'Adventure', 1884, '9780142437179', 3, 'J FIC TWA', 'Available', 'Huck Finn escapes down the Mississippi River with Jim, an enslaved man seeking freedom. Their journey becomes both a great adventure and a biting critique of hypocrisy, racism, and so-called civilization.', 'https://www.amazon.com/Adventures-Huckleberry-Finn-Penguin-Classics/dp/0142437174', 'BK-0033.jpg'),
    (34, 'BK-0034', 'The Adventures of Tom Sawyer', 'Adventure', 1876, '9780143039563', 3, 'J FIC TWA', 'Available', 'Tom Sawyer turns childhood mischief into something vivid, funny, and surprisingly mythic. The novel captures freedom, imagination, and the irresistible energy of boyhood adventure.', 'https://www.amazon.com/Adventures-Tom-Sawyer-Penguin-Classics/dp/0143039563', 'BK-0034.jpg'),
    (35, 'BK-0035', 'Of Mice and Men', 'Classic', 1937, '9780140177398', 15, 'J FIC STE', 'Checked Out', 'George and Lennie travel together looking for work and holding onto a dream of owning land. Steinbeck makes their friendship tender and tragic, while showing how fragile hope can be in hard times.', 'https://penguinrandomhousehighereducation.com/book/?isbn=9780140177398', 'BK-0035.jpg'),
    (36, 'BK-0036', 'The Grapes of Wrath', 'Classic', 1939, '9780143039433', 3, 'J FIC STE', 'Available', 'The Joad family heads west during the Great Depression, chasing survival and dignity after losing their farm. Steinbeck turns economic hardship into an epic of endurance, anger, and shared humanity.', 'https://www.amazon.com/Grapes-Wrath-John-Steinbeck/dp/0143039431', 'BK-0036.jpg'),
    (37, 'BK-0037', 'The Old Man and the Sea', 'Classic', 1952, '9780684801223', 4, 'J FIC HEM', 'Available', 'An aging Cuban fisherman battles a giant marlin far out at sea, refusing to surrender even when nature and luck turn against him. Hemingway writes it with great simplicity and emotional force.', 'https://www.simonandschuster.com/books/Old-Man-and-the-Sea/Ernest-Hemingway/9780684801223', 'BK-0037.jpg'),
    (38, 'BK-0038', 'A Wrinkle in Time', 'Fantasy', 1962, '9780312367541', 18, 'J FIC LEN', 'Available', 'Meg Murry joins a strange cosmic journey to rescue her father from a dark force threatening entire worlds. The novel blends science fantasy, family feeling, and a belief that love can resist darkness.', 'https://us.macmillan.com/books/9780312367541/awrinkleintime/', 'BK-0038.jpg'),
    (39, 'BK-0039', 'Charlotte''s Web', 'Children', 1952, '9780064400558', 6, 'J FIC WHI', 'Available', 'A pig named Wilbur is saved from slaughter by the friendship and cleverness of a spider named Charlotte. It is gentle and funny, but also honest about love, loss, and the passing of time.', 'https://www.harpercollins.com/products/charlottes-web-e-b-whitekate-dicamillo', 'BK-0039.jpg'),
    (40, 'BK-0040', 'The Secret Garden', 'Children', 1911, '9780064401883', 6, 'J FIC BUR', 'Available', 'Mary Lennox discovers a locked garden and, with it, a path toward healing for herself and others. The book turns nature, friendship, and care into a quiet kind of magic.', 'https://www.harpercollins.com/products/the-secret-garden-frances-hodgson-burnettfrances-hodgson-burnett', 'BK-0040.jpg'),
    (41, 'BK-0041', 'The Lion, the Witch and the Wardrobe', 'Fantasy', 1950, '9780064471046', 6, 'J FIC LEW', 'Checked Out', 'Four siblings step through a wardrobe into Narnia, where winter never ends and a deeper conflict is unfolding. It is an iconic portal fantasy filled with danger, sacrifice, and wonder.', 'https://www.harpercollins.com/products/the-lion-the-witch-and-the-wardrobe-c-s-lewis', 'BK-0041.jpg'),
    (42, 'BK-0042', 'Harry Potter and the Sorcerer''s Stone', 'Fantasy', 1997, '9780590353427', 19, 'J FIC ROW', 'Checked Out', 'Harry Potter learns he is a wizard and begins life at Hogwarts, where friendship and mystery quickly replace ordinary childhood. The book mixes wonder, humor, school adventure, and real emotional stakes.', 'https://www.amazon.com/Harry-Potter-Sorcerers-Stone-Rowling/dp/059035342X', 'BK-0042.jpg'),
    (43, 'BK-0043', 'Harry Potter and the Chamber of Secrets', 'Fantasy', 1998, '9780439064873', 20, 'J FIC ROW', 'Available', 'Harry returns to Hogwarts only to find the school shadowed by attacks, rumors, and a secret chamber tied to its past. The sequel expands the world while deepening the mystery and danger.', 'https://www.amazon.com/Harry-Potter-Chamber-Secrets-Rowling/dp/0439064872', 'BK-0043.jpg'),
    (44, 'BK-0044', 'Percy Jackson & the Olympians: The Lightning Thief', 'Fantasy', 2005, '9780786838653', 21, 'J FIC RIO', 'Available', 'Percy Jackson discovers that Greek mythology is real and that he is tangled in a divine conflict far bigger than himself. It is fast, funny, and built around a strong sense of quest and identity.', 'https://www.penguinrandomhouse.com/books/727674/percy-jackson-and-the-olympians-book-one-the-lightning-thief-by-rick-riordan/', 'BK-0044.jpg'),
    (45, 'BK-0045', 'The Maze Runner', 'Science Fiction', 2009, '9780385737951', 22, 'J FIC DAS', 'Available', 'Thomas wakes up in a giant maze with no memory of his past and only fragments of how this world works. The novel moves quickly, building suspense through survival, secrecy, and constant uncertainty.', 'https://www.amazon.com/Maze-Runner-Book-1/dp/0385737955', 'BK-0045.jpg'),
    (46, 'BK-0046', 'The Outsiders', 'Young Adult', 1967, '9780142407332', 23, 'J FIC HIN', 'Available', 'Ponyboy Curtis tries to survive the tension between rival social groups while protecting the people he loves. The novel is direct, emotional, and still effective as a story about class and belonging.', 'https://www.amazon.com/Outsiders-S-Hinton/dp/014240733X', 'BK-0046.jpg'),
    (47, 'BK-0047', 'Life of Pi', 'Adventure', 2001, '9780156027328', 8, 'J FIC MAR', 'Available', 'After a shipwreck, Pi Patel finds himself stranded in a lifeboat with a Bengal tiger and must improvise to survive. The novel is both a survival story and a reflection on faith, storytelling, and truth.', 'https://www.amazon.com/Life-Pi-Yann-Martel/dp/0156027321', 'BK-0047.jpg'),
    (48, 'BK-0048', 'The Martian', 'Science Fiction', 2011, '9780553418026', 24, 'J FIC WEI', 'On Hold', 'Astronaut Mark Watney is left behind on Mars and must use science, humor, and stubbornness to stay alive. The story is tense and smart, but its real charm comes from Watney’s voice and ingenuity.', 'https://www.penguinrandomhouse.com/books/234102/the-martian-by-andy-weir/', 'BK-0048.jpg'),
    (49, 'BK-0049', 'The Da Vinci Code', 'Thriller', 2003, '9780307474278', 25, 'J FIC BRO', 'Available', 'Robert Langdon is drawn into a global puzzle involving secret societies, art history, and a murder investigation. The novel is built for momentum, moving from clue to clue with constant twists.', 'https://www.amazon.com/Vinci-Code-Robert-Langdon/dp/0307474275', 'BK-0049.jpg'),
    (50, 'BK-0050', 'The Girl with the Dragon Tattoo', 'Mystery', 2005, '9780307454546', 26, 'J FIC LAR', 'Available', 'Journalist Mikael Blomkvist and hacker Lisbeth Salander investigate a decades-old disappearance linked to a powerful family. It is a dark, propulsive thriller with memorable characters and layered secrets.', 'https://www.penguinrandomhouse.com/books/98144/the-girl-with-the-dragon-tattoo-by-stieg-larsson/', 'BK-0050.jpg');

-- Book to author bridge
INSERT INTO TITLE_AUTHOR (TITLE_ID, AUTHOR_ID, TITLE_AUTHOR_ROLE) VALUES
    (1, 1, 'Author'),
    (2, 2, 'Author'),
    (3, 3, 'Author'),
    (4, 4, 'Author'),
    (5, 5, 'Author'),
    (6, 6, 'Author'),
    (7, 7, 'Author'),
    (8, 8, 'Author'),
    (9, 9, 'Author'),
    (10, 8, 'Author'),
    (11, 2, 'Author'),
    (12, 10, 'Author'),
    (13, 11, 'Author'),
    (14, 12, 'Author'),
    (15, 13, 'Author'),
    (16, 14, 'Author'),
    (17, 15, 'Author'),
    (18, 16, 'Author'),
    (19, 17, 'Author'),
    (20, 18, 'Author'),
    (21, 19, 'Author'),
    (22, 20, 'Author'),
    (23, 21, 'Author'),
    (24, 22, 'Author'),
    (25, 23, 'Author'),
    (26, 24, 'Author'),
    (27, 24, 'Author'),
    (28, 25, 'Author'),
    (29, 26, 'Author'),
    (30, 27, 'Author'),
    (31, 28, 'Author'),
    (32, 28, 'Author'),
    (33, 29, 'Author'),
    (34, 29, 'Author'),
    (35, 30, 'Author'),
    (36, 30, 'Author'),
    (37, 31, 'Author'),
    (38, 32, 'Author'),
    (39, 33, 'Author'),
    (40, 34, 'Author'),
    (41, 11, 'Author'),
    (42, 35, 'Author'),
    (43, 35, 'Author'),
    (44, 36, 'Author'),
    (45, 37, 'Author'),
    (46, 38, 'Author'),
    (47, 39, 'Author'),
    (48, 40, 'Author'),
    (49, 41, 'Author'),
    (50, 42, 'Author');

-- Frontend-friendly flattened view
CREATE VIEW BOOK_CATALOG_VIEW AS
SELECT
    bt.TITLE_ID,
    bt.BOOK_CODE,
    bt.TITLE_NAME,
    a.AUTHOR_NAME,
    p.PUBLISHER_NAME,
    bt.GENRE,
    bt.PUBLICATION_YEAR,
    bt.ISBN13,
    bt.SHELF_LOCATION,
    bt.STATUS,
    bt.DESCRIPTION,
    bt.SOURCE_URL,
    bt.COVER_IMAGE_FILENAME
FROM BOOK_TITLE bt
JOIN TITLE_AUTHOR ta ON bt.TITLE_ID = ta.TITLE_ID
JOIN AUTHOR a ON ta.AUTHOR_ID = a.AUTHOR_ID
JOIN PUBLISHER p ON bt.PUBLISHER_ID = p.PUBLISHER_ID;

-- Example queries
-- SELECT * FROM BOOK_CATALOG_VIEW ORDER BY TITLE_NAME;
-- SELECT * FROM BOOK_CATALOG_VIEW WHERE STATUS = 'Available' ORDER BY TITLE_NAME;
-- SELECT * FROM BOOK_CATALOG_VIEW WHERE TITLE_NAME LIKE '%Harry Potter%';
-- SELECT * FROM BOOK_CATALOG_VIEW WHERE AUTHOR_NAME = 'George Orwell';