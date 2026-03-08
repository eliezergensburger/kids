-- INSERTS INTO TEACHER
INSERT INTO TEACHER (first_name, last_name, email) VALUES
('Sarah', 'Levi', 'sarah.levi@example.com'),
('David', 'Cohen', 'david.cohen@example.com'),
('Maya', 'Rosen', 'maya.rosen@example.com'),
('Daniel', 'Katz', 'daniel.katz@example.com'),
('Noa', 'Shapiro', 'noa.shapiro@example.com'),
('Ariel', 'Baron', 'ariel.baron@example.com'),
('Tamar', 'Golan', 'tamar.golan@example.com'),
('Yossi', 'Mizrahi', 'yossi.mizrahi@example.com'),
('Lior', 'Ben-Ami', 'lior.benami@example.com'),
('Rina', 'Aviv', 'rina.aviv@example.com');

-- INSERTS INTO GROUP
INSERT INTO PLAYGROUP (groupName, teacherId) VALUES
('Lions', 1),
('Tigers', 2),
('Bears', 3),
('Eagles', 4),
('Dolphins', 5),
('Owls', 6),
('Foxes', 7),
('Wolves', 8);

-- INSERTS INTO CHILD
INSERT INTO CHILD (first_name, last_name, age, email, groupId) VALUES
('Adam', 'Levi', 6, 'adam.levi@example.com', 1),
('Ella', 'Cohen', 5, 'ella.cohen@example.com', 1),
('Ben', 'Rosen', 7, 'ben.rosen@example.com', 2),
('Sofia', 'Katz', 6, 'sofia.katz@example.com', 2),
('Amit', 'Shapiro', 5, 'amit.shapiro@example.com', 3),
('Nina', 'Baron', 6, 'nina.baron@example.com', 3),
('Omer', 'Golan', 7, 'omer.golan@example.com', 4),
('Lia', 'Mizrahi', 5, 'lia.mizrahi@example.com', 4),
('Eitan', 'Ben-Ami', 6, 'eitan.benami@example.com', 5),
('Romi', 'Aviv', 7, 'romi.aviv@example.com', 5),
('Yarden', 'Levi', 5, 'yarden.levi@example.com', 6),
('Shira', 'Cohen', 6, 'shira.cohen@example.com', 6),
('Itai', 'Rosen', 7, 'itai.rosen@example.com', 7),
('Mila', 'Katz', 5, 'mila.katz@example.com', 7),
('Yonatan', 'Shapiro', 6, 'yonatan.shapiro@example.com', 8),
('Gal', 'Baron', 7, 'gal.baron@example.com', 8),
('Noam', 'Golan', 5, 'noam.golan@example.com', 1),
('Talia', 'Mizrahi', 6, 'talia.mizrahi@example.com', 2),
('Harel', 'Ben-Ami', 7, 'harel.benami@example.com', 3),
('Yael', 'Aviv', 5, 'yael.aviv@example.com', 4);

commit;