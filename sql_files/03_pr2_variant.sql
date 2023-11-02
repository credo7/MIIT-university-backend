INSERT INTO practice_two_variant (id, legend, package_width, package_length, package_height, package_tons)
VALUES (1, 'Компания имеет производственные мощности в Китае, отправляя свою продукцию в Европу через порты Германии преимущественно морским путём в 20-футовых контейнерах с продолжительностью от 40 суток.\nС учётом значительной продолжительности доставки продукции и случившегося кризиса у поставщика транспортных услуг, от существующей схемы Компания планирует отказаться.\nКроме того, в условиях увеличения спроса на производимую продукцию Компания расширила географию присутствия, разместив дополнительные производственные мощности в Японии и Корее и рассматривает новые цепи поставок.\nВ связи с повышением привлекательности ускоренных контейнерных сервисов через Казахстан, Монголию и Россию, Компания планирует использовать новые маршруты и технологии доставки продукции.\nПеред Логистическим департаментом поставлена задача поиска оптимальных маршрутов цепей поставок продукции в страны Европы. Проект поручен группе инициативных логистов.\nНа основании изучения рынка и заключённых договоров на поставку продукции сформированы 5 новых цепей поставок продукции ежемесячно при разных условиях Инкотермс:\n1. Китай - Польша 800 т/месяц\n2. Япония - Германия 600 т/месяц\n3. Япония - Нидерланды 400 т/месяц\n4. Корея - Польша 500 т/месяц\n5. Корея - Чехия 300 т/месяц\nПродукция предоставляется к перевозке в сформированных на поддонах транспортных пакетах размером 1,1м*1,1мм*1м (Д*Ш*В) весом 0,5 т.\nИзучив рынок ускоренных железнодорожных и интермодальных контейнерных сервисов «Door to Door», логисты выбрали варианты маршрутов доставки с фиксированными ставками от логистических провайдеров 3PL (таблица 1). Срок доставки по любому из маршрутов не превышает 22 суток, что полностью устраивает Компанию. Цепи поставок из Китая в Польшу предлагается реализовать тремя различными маршрутами, что увеличивает количество рассматриваемых вариантов.', 1.1, 1.1, 1.1, 0.5);
-- TERMINAL | PORT | COUNTRY
INSERT INTO point (id, name, type, country) VALUES ('RUSSIA_TERMINAL_1', 'Россия терминал 1', 'TERMINAL', 'Россия'),
('CHINA_TERMINAL_1', 'Чунцин (Китай) терминал 1', 'TERMINAL', 'Китай'),
('RUSSIA_TERMINAL_2', 'Россия терминал 2', 'TERMINAL', 'Россия'),
('MONGLIA_TERMINAL_1', 'Монголия терминал 1', 'TERMINAL', 'Монголия'),
('KAZAKHSTAN_TERMINAL_1', 'Казахстан терминал 1', 'TERMINAL', 'Казахстан'),
('RUSSIA_PORT_1', 'Морской торговый порт России', 'PORT', 'Россия'),
('JAPAN_TERMINAL_1', 'Йокогама (Япония)', 'TERMINAL', 'Япония'),
('GERMANY_TERMINAL_1', 'Гамбург (Германия)', 'TERMINAL', 'Германия'),
('NETHERLANDS_TERMINAL_1', 'Роттердам (Нидерланды)', 'TERMINAL', 'Нидерланды'),
('KOREA_TERMINAL_1', 'Пусан (Корея)', 'TERMINAL', 'Корея'),
('POLAND_TERMINAL_1', 'Варшава (Польша) терминал 1', 'TERMINAL', 'Польша'),
('CHZECH_TERMINAL_1', 'Острава (Чехия)', 'TERMINAL', 'Чехия'),
('RUSSIA_TERMINAL_3', 'Забайкальск (Россия)', 'TERMINAL', 'Россия'),
('BELORUS_TERMINAL_1', 'Брест (Белоруссия)', 'TERMINAL', 'Белоруссия'),
('MONGLIA_TERMINAL_2', 'Наушки (Монголия)', 'TERMINAL', 'Монголия'),
('KAZAKHSTAN_TERMINAL_2', 'Достык (Казахстан)', 'TERMINAL', 'Казахстан'),
('RUSSIA_PORT_2', 'Восточный (Россия)', 'PORT', 'Россия'),
('RUSSIA_PORT_3', 'Владивосток (Россия)', 'PORT', 'Россия');

INSERT INTO route (from_point_id, to_point_id, days) VALUES
('CHINA_TERMINAL_1', 'RUSSIA_TERMINAL_3', 1),
('RUSSIA_TERMINAL_3', 'BELORUS_TERMINAL_1', 2),
('BELORUS_TERMINAL_1', 'POLAND_TERMINAL_1', 3),
('CHINA_TERMINAL_1', 'MONGLIA_TERMINAL_2', 4),
('CHINA_TERMINAL_1', 'KAZAKHSTAN_TERMINAL_2', 5)
('MONGLIA_TERMINAL_2', 'BELORUS_TERMINAL_1', 6),
('JAPAN_TERMINAL_1', 'RUSSIA_PORT_2', 7),
('RUSSIA_PORT_2', 'BELORUS_TERMINAL_1', 8),
('GERMANY_TERMINAL_1', 'BELORUS_TERMINAL_1', 9)
('BELORUS_TERMINAL_1', 'NETHERLANDS_TERMINAL_1', 10),
('KOREA_TERMINAL_1', 'RUSSIA_PORT_3', 11),
('RUSSIA_PORT_3', 'BELORUS_TERMINAL_1', 12),
('KAZAKHSTAN_TERMINAL_2', 'BELORUS_TERMINAL_1', 13)
('BELORUS_TERMINAL_1', 'CHZECH_TERMINAL_1', 14);

INSERT INTO practice_two_variant_bet (variant_id, from_point_id, transit_point_id, to_point_id, tons, third_party_logistics_1, third_party_logistics_2, third_party_logistics_3, answer) VALUES
(1, 'CHINA_TERMINAL_1', 'RUSSIA_TERMINAL_3', 'POLAND_TERMINAL_1', 2, 11, 800, 4500, 4800, NULL, '["CHINA_TERMINAL_1", "RUSSIA_TERMINAL_3", "BELORUS_TERMINAL_1", "POLAND_TERMINAL_1"]'),
(1, 'CHINA_TERMINAL_1', 'MONGLIA_TERMINAL_2', 'POLAND_TERMINAL_1', 2, 11, 800, NULL, 4600, 4800, '["CHINA_TERMINAL_1", "MONGLIA_TERMINAL_2", "BELORUS_TERMINAL_1", "POLAND_TERMINAL_1"]'),
(1, 'CHINA_TERMINAL_1', 'KAZAKHSTAN_TERMINAL_2', 'POLAND_TERMINAL_1', 2, 11, 800, 4500, NULL, 4600, '["CHINA_TERMINAL_1", "KAZAKHSTAN_TERMINAL_2", "BELORUS_TERMINAL_1", "POLAND_TERMINAL_1"]'),
(1, 'JAPAN_TERMINAL_1', 'RUSSIA_PORT_2', 'GERMANY_TERMINAL_1', 7, 8, 400, 5000, 4800, 4900, '["JAPAN_TERMINAL_1", "RUSSIA_PORT_2", "BELORUS_TERMINAL_1", "GERMANY_TERMINAL_1"]'),
(1, 'JAPAN_TERMINAL_1', 'RUSSIA_PORT_2', 'NETHERLANDS_TERMINAL_1', 7, 9, 500, 5000, 4900, 5000, '["JAPAN_TERMINAL_1", "RUSSIA_PORT_2", "BELORUS_TERMINAL_1", "NETHERLANDS_TERMINAL_1"]'),
(1, 'KOREA_TERMINAL_1', 'RUSSIA_PORT_3', 'POLAND_TERMINAL_1', 10,11,500, 4800, 4700, 4800, '["KOREA_TERMINAL_1", "RUSSIA_PORT_3", "BELORUS_TERMINAL_1", "POLAND_TERMINAL_1"]'),
(1, 'KOREA_TERMINAL_1', 'RUSSIA_PORT_3', 'CHZECH_TERMINAL_1', 10,12,300, 4900, 4800, 4900, '["KOREA_TERMINAL_1", "RUSSIA_PORT_3", "BELORUS_TERMINAL_1", "CHZECH_TERMINAL_1"]');
