INSERT INTO route (from_point_id, to_point_id, days) VALUES
(2, 13, 1),
(13, 14, 2),
(14, 11, 3),
(2, 15, 4),
(2, 16, 4),
(15, 14, 5),
(7, 17, 7),
(17, 14, 8),
(14, 8, 9),
(14, 9, 10),
(10, 18, 11),
(18, 14, 13),
(14,12,15)
ON CONFLICT DO NOTHING;